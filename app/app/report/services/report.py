from sqlalchemy.ext.asyncio import AsyncSession
from app.bill.repo import bill_repo
from app import crud
from app.parking.repo import zone_repo
from datetime import datetime, timedelta, UTC
from dateutil.relativedelta import relativedelta
from app.report import schemas as report_schemas
from app.parking.repo import zone_repo
from app.parking.services import zone as zone_services
from typing import Any


# calculate  first date month
def get_month_dates(reference_date, months_ago):
    month_dates = []

    for i in range(0, months_ago):
        # Calculate the start date of the month `i` months ago
        start_date = (reference_date - relativedelta(months=i)).replace(day=1)

        # Calculate the end date of that month
        end_date = (start_date + relativedelta(months=1)).replace(
            day=1
        ) - timedelta(days=1)

        month_dates.append((start_date, end_date))

    return month_dates


# convert day, hour, seconed to minute
def convert_time_to_minutes(start_time, end_time):
    if start_time > end_time:
        return 0
    day = 0
    time_diffrence = end_time - start_time

    # seprating day from time
    if time_diffrence.days:
        day = time_diffrence.days * 24 * 60
        time_diffrence = str(time_diffrence).split(", ")[
            1
        ]  # example 1 day, 00:00:00 -> 00:00:00
    # Calculation hours, conversion minutes and seconds to hours
    hours, minutes, seconds = map(float, str(time_diffrence).split(":"))
    hours = hours * 60 if hours > 0 else 0
    minutes = minutes if minutes > 0 else 0
    seconds = seconds / 60 if seconds > 0 else 0
    time_diffrence = hours + minutes + seconds + day
    return time_diffrence


def convert_time_to_minute(time: datetime):
    minute = 0
    # seprating day from time
    if time.days:
        minute = time.days * 24 * 60
        time = str(time).split(", ")[1]  # example 1 day, 00:00:00 -> 00:00:00
    # Calculation hours, conversion minutes and seconds to hours
    hours, minutes, seconds = map(float, str(time).split(":"))
    total_minute = (hours * 60) + (minutes + minute) + (seconds / 60)
    return round(total_minute)


def calculate_percentage(start_time, end_time):
    """Calculate the normalized percentage difference between start_time and end_time."""
    percentage_difference = 0
    # handel devision zero
    if end_time == 0:
        if start_time == 0:
            return percentage_difference
        return -100
    # Calculate the absolute difference in seconds
    difference = start_time - end_time
    if difference == 0:
        return percentage_difference

    # Calculate the percentage difference, capped at 100%
    percentage_difference = (difference / end_time) * 100

    return round(percentage_difference)


async def capacity(db: AsyncSession):
    start_today = datetime.now(UTC).replace(
        tzinfo=None, hour=0, minute=0, second=0, microsecond=0
    )
    end_today = datetime.now(UTC).replace(
        tzinfo=None, hour=23, minute=59, second=59, microsecond=9999
    )
    count_referred = await crud.record.get_count_referred(
        db,
        input_start_create_time=start_today,
        input_end_create_time=end_today,
    )

    total_amount_bill = await bill_repo.get_total_amount_bill(db)
    if total_amount_bill is None:
        total_amount_bill = 0

    avg_time_park = await crud.record.get_avg_time_park(
        db,
        start_time_in=start_today,
        end_time_in=end_today,
    )
    if avg_time_park:
        avg_time_park = avg_time_park.total_seconds() / 60
    else:
        avg_time_park = 0

    capacity_zones, count_zone = await zone_repo.get_capacity_count_zone(db)

    unknown_referred = await crud.record.get_count_unknown_referred(db)
    if unknown_referred is None:
        unknown_referred = 0

    total_count_in_parking = await crud.record.get_total_in_parking(db)

    if not total_count_in_parking:
        total_count_in_parking = 0

    empty = capacity_zones - (total_count_in_parking + unknown_referred)
    if empty < 0:
        empty = 0

    effective_utilization_rate = round(
        (((avg_time_park / 60) / (capacity_zones * 24)) * 100), 2
    )

    return report_schemas.Capacity(
        total=capacity_zones,
        empty=empty,
        full=total_count_in_parking + unknown_referred,
        unknown=unknown_referred,
        count_referred=count_referred,
        total_amount_bill=total_amount_bill,
        avg_minute_park=avg_time_park,
        len_zone=count_zone,
        effective_utilization_rate=effective_utilization_rate,
    )


async def report_zone(db: AsyncSession):
    start_today = datetime.now(UTC).replace(
        tzinfo=None, hour=0, minute=0, second=0, microsecond=0
    )
    end_today = datetime.now(UTC).replace(
        tzinfo=None, hour=23, minute=59, second=59, microsecond=9999
    )
    zones = await zone_repo.get_multi(db, limit=None)
    for zone in zones:
        zone_id = {zone.id}
        zone = await zone_services.set_children_ancestors_capacity(db, zone)
        zone.total_referred = (
            await crud.record.get_today_count_referred_by_zone(
                db,
                zone_id=zone.id,
                start_time_in=start_today,
                end_time_in=end_today,
            )
        )
        avg_time = await crud.record.get_avg_time_park(
            db,
            zone_id_in=zone.id,
            start_time_in=start_today,
            end_time_in=end_today,
        )

        convert_avg_time = 0
        if avg_time:
            convert_avg_time = avg_time.total_seconds() / 60

            zone.effective_utilization_rate = round(
                ((((convert_avg_time / 60) / (zone.capacity * 24)) * 100)), 2
            )

        zone.avrage_stop_minute_today = round(convert_avg_time)

        total_price, total_income = await bill_repo.get_price_income(
            db,
            zone_id=zone_id,
            start_time_in=start_today,
            end_time_in=end_today,
        )

        zone.avrage_amount_bill_today = round(total_price)
        zone.income_today_parking = round(total_income)
        zone.pricings = []
        zone.ancestors = []
        zone.children = []
        zone.rules = []

    return zones


async def park_time(
    db: AsyncSession,
    *,
    start_time_in: datetime,
    end_time_in: datetime,
    jalali_date: report_schemas.JalaliDate,
):
    list_avg_zone_time_park = []
    convert_to_minute_time_park = 0

    total_avrage_park_time = await crud.record.get_avg_time_park(
        db,
        start_time_in=start_time_in,
        end_time_in=end_time_in,
        jalali_date=jalali_date,
    )
    if total_avrage_park_time is not None:
        total_avrage_park_time = round(
            total_avrage_park_time.total_seconds() / 60
        )
    else:
        total_avrage_park_time = 0
    zones = await zone_repo.get_multi(db, limit=None)
    for zone in zones:
        avrage_park_time = await crud.record.get_avg_time_park(
            db,
            zone_id_in=zone.id,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
            jalali_date=jalali_date,
        )
        if avrage_park_time:
            convert_to_minute_time_park = round(
                avrage_park_time.total_seconds() / 60
            )
        list_avg_zone_time_park.append(
            {
                "zone_name": zone.name,
                "avg_time_park": convert_to_minute_time_park,
            }
        )
    list_avg_zone_time_park.append(
        {"avg_total_time_park": total_avrage_park_time}
    )

    return list_avg_zone_time_park


async def effective_utilization_rate(
    db: AsyncSession,
    *,
    start_time_in: datetime,
    end_time_in: datetime,
    jalali_date: report_schemas.JalaliDate,
):
    list_effective_utilization_rate = []
    convert_to_minute_time_park = 0
    total_capacity = 0

    zones = await zone_repo.get_multi(db, limit=None)
    for zone in zones:
        avrage_park_time = await crud.record.get_avg_time_park(
            db,
            zone_id_in=zone.id,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
            jalali_date=jalali_date,
        )
        if avrage_park_time:
            convert_to_minute_time_park = round(
                (
                    (avrage_park_time.total_seconds() / 3600)
                    / (zone.capacity * 24)
                )
                * 100
            )
        list_effective_utilization_rate.append(
            {
                zone.name: convert_to_minute_time_park,
            }
        )
        total_capacity += zone.capacity

    total_avrage_park_time = await crud.record.get_avg_time_park(
        db,
        start_time_in=start_time_in,
        end_time_in=end_time_in,
        jalali_date=jalali_date,
    )
    if total_avrage_park_time is not None and total_capacity != 0:
        total_effective_utilization_rate = round(
            (
                (
                    (total_avrage_park_time.total_seconds() / 3600)
                    / (total_capacity * 24)
                )
                * 100
            ),
            2,
        )
    else:
        total_effective_utilization_rate = 0
    list_effective_utilization_rate.append(
        {"total_effective_utilization_rate": total_effective_utilization_rate}
    )

    return list_effective_utilization_rate


# Helper function to get the last day of a given month
def last_day_of_month(date: datetime):
    next_month = date.replace(day=28) + timedelta(
        days=4
    )  # this will be in the next month
    return next_month - timedelta(days=next_month.day)


def get_month_range(start_date: datetime, end_date: datetime):

    # List to store the month ranges
    month_ranges = []

    # Start iterating from the first month
    current_start = start_date.replace(day=1)

    # Loop through each month until the end_date
    while current_start <= end_date:
        current_end = last_day_of_month(current_start)
        if current_end > end_date:
            current_end = end_date

        month_ranges.append((current_start, current_end))

        # Move to the next month
        next_month = current_start + timedelta(days=31)
        current_start = next_month.replace(day=1)

    return month_ranges


def get_year_range(start_date: datetime, end_date: datetime):

    start_year = start_date.year
    end_year = end_date.year

    return [
        datetime(year, 1, 1).date() for year in range(start_year, end_year + 1)
    ]


def create_ranges_date(
    end_date: datetime, start_date: datetime, timing: report_schemas.Timing
):

    start_date = start_date.date()
    end_date = end_date.date()

    ranges = []
    current_date = start_date
    while current_date <= end_date:
        # Create a range
        start_time = current_date
        if timing == report_schemas.Timing.day:
            current_date += timedelta(days=1)
            ranges.append({"time": start_time, "count": 0})

        if timing == report_schemas.Timing.week:
            ranges.append({"time": start_time, "count": 0})
            start_time = current_date + timedelta(days=7)
            current_date += timedelta(days=7)

        if timing == report_schemas.Timing.month:
            range_month = get_month_range(start_date, end_date)
            for start, end in range_month:
                ranges.append({"time": start, "count": 0})
            return ranges

        if timing == report_schemas.Timing.year:
            years = get_year_range(start_date, end_date)
            for year in years:
                ranges.append({"time": year, "count": 0})
            return ranges

    return ranges


async def get_count_referred(
    db: AsyncSession,
    start_time_in: datetime,
    end_time_in: datetime,
    timing: report_schemas.Timing,
    jalali_date: report_schemas.JalaliDate,
    zone_id: int | None = None,
) -> list:

    range_date = create_ranges_date(
        start_date=start_time_in, end_date=end_time_in, timing=timing
    )

    capacity_zone = await crud.zone_repo.get_capacity(db, zone_id=zone_id)
    count_record = await crud.record.get_count_referred_by_timing_status(
        db,
        input_start_create_time=start_time_in,
        input_end_create_time=end_time_in,
        timing=(
            timing
            if timing != report_schemas.Timing.week
            else report_schemas.Timing.day
        ),
        zone_id=zone_id,
    )
    convert_to_dict_record = {}
    total_count_record = 0
    for time, count, avg_time_park in count_record:
        total_count_record += count
        record_date = time.date()
        if record_date not in convert_to_dict_record:
            convert_to_dict_record[record_date] = {}
        convert_to_dict_record[record_date]["count"] = count
        convert_to_dict_record[record_date]["effective_utilization_rate"] = (
            round(
                (
                    (
                        (avg_time_park.total_seconds() / 3600)
                        / (capacity_zone * 24)
                    )
                    * 100
                ),
                2,
            )
        )

    for item in range_date:
        if timing == report_schemas.Timing.day:
            if item["time"] in convert_to_dict_record:
                # print(convert_to_dict_record[item["time"]])
                item["count"] = convert_to_dict_record[item["time"]]

            else:
                item["count"] = {"count": 0, "effective_utilization_rate": 0}
        if timing == report_schemas.Timing.week:
            start_date = item["time"]
            end_date = start_date + timedelta(days=7)
            weekly_data = {"unfinished": 0, "finished": 0, "unknown": 0}

            # Iterate through each day in the 7-day period and sum up the count
            current_date = start_date
            while current_date < end_date:
                if current_date in convert_to_dict_record:
                    for status, count in convert_to_dict_record[
                        current_date
                    ].items():
                        if status in weekly_data:
                            weekly_data[status] += count
                        else:
                            weekly_data[status] = count
                current_date += timedelta(days=1)
            item.update({"end_date": end_date})
            item["count"] = weekly_data
        if timing == report_schemas.Timing.month:
            if item["time"] in convert_to_dict_record:

                item["count"] = convert_to_dict_record[item["time"]]
            else:
                item["count"] = {"count": 0, "effective_utilization_rate": 0}
            item.update({"end_time": last_day_of_month(item["time"])})
        if timing == report_schemas.Timing.year:
            if item["time"] in convert_to_dict_record:
                item["count"] = convert_to_dict_record[item["time"]]
            else:
                item["count"] = {"count": 0, "effective_utilization_rate": 0}
        item["start_time"] = item.pop("time")
        item["data"] = item.pop("count")
    range_date.append({"total_refferd": total_count_record})

    return range_date


async def cal_count_with_out_status(
    data: Any, start_time_in, end_time_in, timing
):
    range_date = create_ranges_date(
        start_date=start_time_in, end_date=end_time_in, timing=timing
    )
    convert_to_dict_record = {time.date(): count for time, count in data}

    for item in range_date:
        if timing == report_schemas.Timing.day:
            if item["time"] in convert_to_dict_record:
                item["count"] = convert_to_dict_record[item["time"]]
        if timing == report_schemas.Timing.week:
            # For weekly grouping, sum over a 7-day period
            start_date = item[
                "time"
            ]  # Assuming `item["time"]` is the start of the week
            end_date = start_date + timedelta(days=7)
            week_count = 0

            # Iterate through each day in the 7-day period and sum up the count
            current_date = start_date
            while current_date < end_date:
                if current_date in convert_to_dict_record:
                    week_count += convert_to_dict_record[current_date]
                current_date += timedelta(days=1)
            item.update({"end_date": end_date})
            item["count"] = week_count
        if timing == report_schemas.Timing.month:
            if item["time"] in convert_to_dict_record:
                item["count"] = convert_to_dict_record[item["time"]]
                item.update({"end_time": last_day_of_month(item["time"])})
        if timing == report_schemas.Timing.year:
            if item["time"] in convert_to_dict_record:
                item["count"] = convert_to_dict_record[item["time"]]
        item["start_time"] = item.pop("time")

    return range_date


async def get_count_referred_by_zone(
    db: AsyncSession,
    start_time_in: datetime,
    end_time_in: datetime,
    timing: report_schemas.Timing,
    zone_id: int | None = None,
) -> list:

    all_count_referred = 0
    result = {}
    zones_ids = await zone_repo.get_multi(db, limit=None)
    if zone_id:
        zone = await zone_repo.get(db, id=zone_id)
        zones_ids = [zone]
    for zone in zones_ids:
        total_count_referred = 0
        zone_data = await crud.record.get_count_referred_with_out_status(
            db,
            input_start_create_time=start_time_in,
            input_end_create_time=end_time_in,
            timing=timing,
            zone_id=zone.id,
        )
        record_detail = await cal_count_with_out_status(
            data=zone_data,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
            timing=timing,
        )
        for record in record_detail:
            start_time = record["start_time"]
            count = record["count"]

            if start_time not in result:
                result[start_time] = {"total": 0}

            result[start_time][zone.name] = count
            result[start_time]["total"] += count

            total_count_referred += count
        all_count_referred += total_count_referred
    result["all_count_referred"] = all_count_referred
    return result


async def count_entrance_exit_zone(
    db: AsyncSession,
    zone_id_in: int | None = None,
    start_time_in: datetime | None = None,
    end_time_in: datetime | None = None,
):

    camera_entrance, camera_exit = (
        await crud.equipment_repo.get_entrance_exit_camera(
            db, zone_id=zone_id_in
        )
    )

    def _initialize_cameras(cameras):
        camera_dict = {}
        for name_camera, zone_name in cameras:
            if zone_name not in camera_dict:
                camera_dict[zone_name] = {}
            camera_dict[zone_name][name_camera] = 0
        return camera_dict

    obj_camera_entrance = _initialize_cameras(camera_entrance)
    obj_camera_exit = _initialize_cameras(camera_exit)

    count_entrance, count_exit = await crud.record.count_entrance_exit_door(
        db,
        zone_id_in=zone_id_in,
        start_time_in=start_time_in,
        end_time_in=end_time_in,
    )
    for zone_name, cameras in obj_camera_entrance.items():
        for camera_name in cameras:
            obj_camera_entrance[zone_name][camera_name] = count_entrance.get(
                camera_name, 0
            )
    for zone_name, cameras in obj_camera_exit.items():
        for camera_name in cameras:
            obj_camera_exit[zone_name][camera_name] = count_exit.get(
                camera_name, 0
            )

    return report_schemas.CountEntranceExitDoor(
        count_entrance=obj_camera_entrance, count_exit=obj_camera_exit
    )


async def report_bill(
    db: AsyncSession,
    *,
    zone_id: int,
    start_time_in: datetime,
    end_time_in: datetime,
):

    total_bills, bills_paid, bills_unpaid = (
        await bill_repo.get_total_price_count(
            db,
            zone_id=zone_id,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
        )
    )
    total_amount = 0
    if total_bills[0] is not None:
        total_amount = round(total_bills[0])
    total_amount_paid = 0
    if bills_paid[0] is not None:
        total_amount_paid = round(bills_paid[0])
    total_amount_unpaid = 0
    if bills_unpaid[0] is not None:
        total_amount_unpaid = round(bills_unpaid[0])

    return {
        "total_bills": {
            "price": total_amount,
            "count": total_bills[1],
        },
        "bills_paid": {
            "price": total_amount_paid,
            "count": bills_paid[1],
        },
        "bills_unpaid": {
            "price": total_amount_unpaid,
            "count": bills_unpaid[1],
        },
    }


async def report_bill_by_timing(
    db: AsyncSession,
    *,
    timing: report_schemas.Timing = report_schemas.Timing.day,
    zone_id: int | None = None,
    start_time_in: datetime,
    end_time_in: datetime,
):
    range_dates = create_ranges_date(
        start_date=start_time_in, end_date=end_time_in, timing=timing
    )

    total_bills = await bill_repo.get_total_price_by_timing(
        db,
        timing=(
            timing
            if timing != report_schemas.Timing.week
            else report_schemas.Timing.day
        ),
        zone_id=zone_id,
        start_time_in=start_time_in,
        end_time_in=end_time_in,
    )

    convert_total_bills = {date.date(): price for date, price in total_bills}

    for range_date in range_dates:
        if timing == report_schemas.Timing.day:
            if range_date["time"] in convert_total_bills:
                range_date["count"] = convert_total_bills[range_date["time"]]
        if timing == report_schemas.Timing.week:
            # For weekly grouping, sum over a 7-day period
            start_date = range_date[
                "time"
            ]  # Assuming `item["time"]` is the start of the week
            end_date = start_date + timedelta(days=7)
            week_price = 0

            # Iterate through each day in the 7-day period and sum up the count
            current_date = start_date
            while current_date < end_date:
                if current_date in convert_total_bills:
                    week_price += convert_total_bills[current_date]
                current_date += timedelta(days=1)
            range_date.update({"end_date": end_date})
            range_date["count"] = week_price
        if timing == report_schemas.Timing.month:
            if range_date["time"] in convert_total_bills:
                range_date["count"] = convert_total_bills[range_date["time"]]
                range_date.update(
                    {"end_time": last_day_of_month(range_date["time"])}
                )

        if timing == report_schemas.Timing.year:
            if range_date["time"] in convert_total_bills:
                range_date["count"] = convert_total_bills[range_date["time"]]

        range_date["start_time"] = range_date.pop("time")
        range_date["price"] = range_date.pop("count")

    return range_dates

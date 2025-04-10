from .models import Bill
from app import models
from app.crud.base import CRUDBase
from .schemas.bill import (
    BillCreate,
    BillUpdate,
    ParamsBill,
    Bill as billschemas,
    StatusBill,
    JalaliDate,
    OrderByBill,
)
from app.parking.models import Zone
from app.report.schemas import Timing
from sqlalchemy import false
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import datetime, UTC
from typing import Awaitable
from app.models import Record, Image
from app.parking.models import Equipment
import re


class BillRepository(CRUDBase[Bill, BillCreate, BillUpdate]):

    async def get_bill_by_plate(
        self, db: AsyncSession, plate_in: str = None
    ) -> Bill:

        query = select(Bill)

        filters = [Bill.is_deleted == false()]

        if plate_in is not None:
            filters.append(Bill.plate == plate_in)

        return await self._first(
            db.scalars(query.order_by(Bill.created.desc()).filter(*filters))
        )

    async def get_bills_by_plate(
        self,
        db: AsyncSession,
        *,
        plate: str = None,
        bill_status: StatusBill,
    ) -> Bill:

        query = select(Bill)

        filters = [Bill.is_deleted == false()]

        if plate is not None:
            filters.append(Bill.plate == plate)

        if bill_status is not None:
            filters.append(Bill.status == bill_status)

        return await self._all(db.scalars(query.filter(*filters)))

    # async def get_bills(
    #     self,
    #     db: AsyncSession,
    #     *,
    #     plate: str = None,
    #     bill_status: StatusBill,
    # ) -> Bill:

    #     equipment_entance = aliased(Equipment)
    #     equipment_exit = aliased(Equipment)

    #     query = (
    #         select(
    #             Bill,
    #             (Bill.end_time - Bill.start_time).label("time_park"),
    #             Zone.name,
    #             equipment_entance.tag.label("camera_entrance"),
    #             equipment_exit.tag.label("camera_exit"),
    #         )
    #         .outerjoin(Record, Bill.record_id == Record.id)
    #         .outerjoin(Zone, Bill.zone_id == Zone.id)
    #         .outerjoin(
    #             equipment_entance,
    #             Bill.camera_entrance_id == equipment_entance.id,
    #         )
    #         .outerjoin(
    #             equipment_exit, Bill.camera_exit_id == equipment_exit.id
    #         )
    #     )

    #     filters = [Bill.is_deleted == false()]

    #     if plate is not None:
    #         filters.append(Bill.plate == plate)

    #     if bill_status is not None:
    #         filters.append(Bill.status == bill_status)

    #     return (await db.execute(query.filter(*filters))).fetchall()

    async def get_multi_by_filters(
        self,
        db: AsyncSession,
        *,
        params: ParamsBill,
        jalali_date: JalaliDate | None = None,
    ) -> list[billschemas]:
        equipment_entance = aliased(Equipment)
        equipment_exit = aliased(Equipment)

        query = (
            select(
                Bill,
                (Bill.end_time - Bill.start_time).label("time_park"),
                Zone.name,
                equipment_entance.tag.label("camera_entrance"),
                equipment_exit.tag.label("camera_exit"),
                models.User.full_name,
                Record,
            )
            .outerjoin(Zone, Bill.zone_id == Zone.id)
            .outerjoin(
                equipment_entance,
                Bill.camera_entrance_id == equipment_entance.id,
            )
            .outerjoin(
                equipment_exit, Bill.camera_exit_id == equipment_exit.id
            )
            .outerjoin(models.User, Bill.user_paid_id == models.User.id)
            .outerjoin(models.Record, Bill.record_id == models.Record.id)
        )

        filters = [Bill.is_deleted == false()]

        # if jalali_date is not None:
        #     column_date_jalali = select(
        #         Bill.id,
        #         func.format_jalali(Bill.created, False).label("date_jalali"),
        #     ).subquery()
        #     dj = aliased(column_date_jalali)
        #     if jalali_date.start_jalali_date is not None:
        #         query = query.join(dj, Bill.id == dj.c.id).filter(
        #             *[
        #                 dj.c.date_jalali.between(
        #                     jalali_date.start_jalali_date,
        #                     jalali_date.end_jalali_date,
        #                 )
        #             ]
        #         )
        if params.input_camera_entrance is not None:
            filters.append(
                Bill.camera_entrance_id == params.input_camera_entrance
            )

        if params.input_id is not None:
            filters.append(Bill.id == params.input_id)

        if params.input_notice_sent_by is not None:
            filters.append(Bill.notice_sent_by == params.input_notice_sent_by)

        if params.input_user_paid_id is not None:
            filters.append(Bill.user_paid_id == params.input_user_paid_id)

        if params.input_notice_sent_by_bool:
            filters.append(Bill.notice_sent_by.is_(None))

        if params.input_notice_sent_by_bool == False:
            filters.append(Bill.notice_sent_by.is_not(None))

        if params.input_bill_type is not None:
            filters.append(Bill.bill_type == params.input_bill_type)

        if params.input_camera_exit is not None:
            filters.append(Bill.camera_exit_id == params.input_camera_exit)

        if params.input_plate is not None and bool(
            re.fullmatch(r"[0-9?]{9}", params.input_plate)
        ):
            value_plate = params.input_plate.replace("?", "_")
            filters.append(Bill.plate.like(value_plate))

        if params.input_zone_id is not None:
            filters.append(Bill.zone_id == params.input_zone_id)

        if params.input_start_time is not None:
            filters.append(Bill.created >= params.input_start_time)

        if params.input_end_time is not None:
            filters.append(Bill.created <= params.input_end_time)

        if params.input_issued_by is not None:
            filters.append(Bill.issued_by == params.input_issued_by)

        if params.input_status is not None:
            filters.append(Bill.status == params.input_status)

        count = await db.scalar(
            query.filter(*filters).with_only_columns(func.count())
        )
        if params.input_order_by == OrderByBill.id:
            order_by = Bill.id.asc() if params.asc else Bill.id.desc()

        if params.input_order_by == OrderByBill.entry_time:
            order_by = (
                Bill.start_time.asc() if params.asc else Bill.start_time.desc()
            )

        if params.input_order_by == OrderByBill.leave_time:
            order_by = (
                Bill.end_time.asc() if params.asc else Bill.end_time.desc()
            )

        if params.input_order_by == OrderByBill.issue_bill:
            order_by = (
                Bill.created.asc() if params.asc else Bill.created.desc()
            )

        if params.size is None:
            items = (
                await db.execute(
                    query.filter(*filters)
                    .order_by(order_by)
                    .offset(params.skip)
                )
            ).fetchall()

            return [items, count]

        items = (
            await db.execute(
                query.filter(*filters)
                .order_by(order_by)
                .limit(params.size)
                .offset(params.skip)
            )
        ).fetchall()

        return [items, count]

    async def get_price_income(
        self,
        db: AsyncSession,
        *,
        start_time_in: datetime = None,
        end_time_in: datetime = None,
        zone_id: int = None,
    ):
        filters = [Bill.is_deleted == false()]

        if start_time_in is not None and end_time_in is not None:
            filters.append(Bill.created.between(start_time_in, end_time_in))

        if zone_id is not None:
            filters.append(Bill.zone_id.in_(zone_id))

        query_sum_price_bill = select(
            func.count(), func.sum(Bill.price)
        ).filter(*filters)

        filters_income = filters

        filters_income.append(Bill.status == StatusBill.paid)

        query_sum_income_bill = select(func.sum(Bill.price)).filter(
            *filters_income
        )

        total_income = await db.scalar(query_sum_income_bill)

        if total_income == None or total_income == 0:
            total_income = 0

        count, total_price = (
            await db.execute(query_sum_price_bill)
        ).fetchone()

        if total_price is None or total_price == 0:
            total_price = 0

        return total_price, total_income

    async def get_total_amount_bill(
        self, db: AsyncSession, start_time: datetime | None = None
    ):

        return await db.scalar(
            select(func.sum(Bill.price)).filter(
                Bill.is_deleted == False,
                Bill.created >= start_time,
            )
        )

    async def get_camera_by_image_id(self, db: AsyncSession, img_id: int):

        query = (
            select(Equipment.serial_number)
            .select_from(Bill)
            .join(Image, img_id == Image.id)
            .join(Equipment, Image.camera_id == Equipment.id)
        )

        return await db.scalar(query.filter(*[Bill.is_deleted == False]))

    async def get_total_price_count(
        self,
        db: AsyncSession,
        *,
        zone_id: int,
        start_time_in: datetime,
        end_time_in: datetime,
    ):

        filters = [Bill.is_deleted == False]

        if zone_id is not None:
            filters.append(Bill.zone_id == zone_id)
        if start_time_in is not None:
            filters.append(Bill.created >= start_time_in)
        if end_time_in is not None:
            filters.append(Bill.created <= end_time_in)

        query_total_count_price = select(
            func.sum(Bill.price),
            func.count(),
        ).filter(*filters)

        excute_query_total_count_price = await db.execute(
            query_total_count_price
        )
        fetch_query_total_count_price = (
            excute_query_total_count_price.fetchone()
        )

        query_get_paid_price_count = select(
            func.sum(Bill.price), func.count()
        ).filter(*filters, Bill.status == StatusBill.paid)

        excute_query_get_paid_price_count = await db.execute(
            query_get_paid_price_count
        )
        fetch_query_get_paid_price_count = (
            excute_query_get_paid_price_count.fetchone()
        )

        query_get_unpaid_price_count = select(
            func.sum(Bill.price), func.count()
        ).filter(*filters, Bill.status == StatusBill.unpaid)

        excute_query_get_unpaid_price_count = await db.execute(
            query_get_unpaid_price_count
        )
        fetch_query_get_unpaid_price_count = (
            excute_query_get_unpaid_price_count.fetchone()
        )

        return (
            fetch_query_total_count_price,
            fetch_query_get_paid_price_count,
            fetch_query_get_unpaid_price_count,
        )

    async def get_total_price_by_timing(
        self,
        db: AsyncSession,
        *,
        timing: Timing,
        zone_id: int,
        start_time_in: datetime,
        end_time_in: datetime,
    ):

        filters = [Bill.is_deleted == False]

        if zone_id is not None:
            filters.append(Bill.zone_id == zone_id)
        if start_time_in is not None:
            filters.append(Bill.created >= start_time_in)
        if end_time_in is not None:
            filters.append(Bill.created <= end_time_in)

        query = (
            select(
                func.date_trunc(timing, Bill.created).label(timing),
                func.sum(Bill.price),
            )
            .filter(*filters)
            .group_by(timing)
        )

        excute_query_total_count_price = await db.execute(query)
        fetch_query_total_price = excute_query_total_count_price.fetchall()

        return fetch_query_total_price

    async def get(
        self, db: AsyncSession, id: int, for_update: bool = False
    ) -> Bill | Awaitable[Bill]:

        query = select(self.model).filter(
            self.model.id == id, self.model.is_deleted == False
        )
        if for_update:
            return await self._first(db.scalars(query.with_for_update()))

        return await self._first(db.scalars(query))

    async def avg_price_per_referred(
        self,
        db: AsyncSession,
        start_time_in: datetime,
        end_time_in: datetime,
        zone_id: int,
    ):

        filters = [Bill.is_deleted == False]

        if start_time_in is not None and end_time_in is not None:
            filters.append(
                and_(
                    Bill.created.between(start_time_in, end_time_in),
                    Record.start_time.between(start_time_in, end_time_in),
                )
            )
        if zone_id is not None:
            filters.append(Bill.zone_id == zone_id)
            filters.append(Record.zone_id == zone_id)
        query = (
            select(
                func.count(Record.id).label("count"),
                func.sum(Bill.price).label("price"),
            )
            .where(and_(*filters))
            .join(Record)
        )

        execute = await db.execute(query)

        count, total_price = execute.fetchone()

        if count is None or count == 0:
            return 0

        return round(total_price / count)

    async def get_and_lock(
        self, db: AsyncSession, id: int, for_update: bool = False
    ) -> Bill | Awaitable[Bill]:

        query = select(self.model).filter(
            self.model.id == id, self.model.is_deleted == False
        )
        if for_update:
            return await self._first(db.scalars(query.with_for_update()))

        return await self._first(db.scalars(query))


bill_repo = BillRepository(Bill)

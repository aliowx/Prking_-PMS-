from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict


class Capacity(BaseModel):
    total: int | None = None
    empty: int | None = None
    full: int | None = None
    total_today_park: int | None = None


class AverageTimeDetail(BaseModel):
    time: int | None = None
    compare: int | None = None


class AverageTime(BaseModel):
    avrage_all_time: str | None = None
    avrage_one_day_ago: AverageTimeDetail | None = None
    avrage_one_week_ago: AverageTimeDetail | None = None
    avrage_one_month_ago: AverageTimeDetail | None = None
    avrage_six_month_ago: AverageTimeDetail | None = None
    avrage_one_year_ago: AverageTimeDetail | None = None


class referred_timing(BaseModel):
    week: list | None = []
    month: list | None = []
    six_month: list | None = []
    year: list | None = []


class Referred(BaseModel):
    list_referred: dict | None = None


class MaxTimePark(BaseModel):
    plate: str | None = None
    created: datetime | None = None
    time: str | None = None


class ListMaxTimePark(BaseModel):
    total_max_time_park: list[MaxTimePark] = [MaxTimePark]


class CountEntranceExitDoor(BaseModel):
    count_entrance_exit_door: list | None = []

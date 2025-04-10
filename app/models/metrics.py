import datetime

from pydantic import BaseModel


class TimeSeriesMetricData(BaseModel):
    metric: str
    scope: str
    point_list_interval: int
    point_list_length: int
    point_list: list[tuple[datetime.datetime, float]]
    point_list_start_datetime: datetime.datetime
    point_list_end_datetime: datetime.datetime
    display_name: str

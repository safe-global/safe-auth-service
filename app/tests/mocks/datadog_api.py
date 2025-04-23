from typing import Any

metrics_time_series: list[dict] = [
    {
        "unit": None,
        "query_index": 0,
        "aggr": None,
        "metric": "apisix.request.latency.median",
        "tag_set": [],
        "expression": "apisix.request.latency.median{*}",
        "scope": "*",
        "interval": 30,
        "length": 2,
        "start": 1744190130000,
        "end": 1744190189000,
        "pointlist": [
            [1744190130000.0, 3.000020980835],
            [1744190160000.0, 1.5000104904175],
        ],
        "display_name": "apisix.request.latency.median",
        "attributes": {},
    }
]

datadog_time_series_response: dict[str, Any] = {
    "status": "ok",
    "res_type": "time_series",
    "resp_version": 1,
    "query": "apisix.request.latency.median{*}",
    "from_date": 1744182650000,
    "to_date": 1744190450000,
    "series": metrics_time_series,
    "values": [],
    "times": [],
    "message": "",
    "group_by": [],
}

datadog_time_series_empty_response: dict[str, Any] = {
    "status": "ok",
    "res_type": "time_series",
    "resp_version": 1,
    "query": "apisix.request.latency.median{*}",
    "from_date": 1744182650000,
    "to_date": 1744190450000,
    "series": [],
    "values": [],
    "times": [],
    "message": "",
    "group_by": [],
}

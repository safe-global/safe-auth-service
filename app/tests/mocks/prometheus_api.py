import datetime
from typing import Any

prometheus_vector_response: dict[str, Any] = {
    "status": "success",
    "data": {
        "resultType": "vector",
        "result": [
            {
                "metric": {"request_uri": "/service/hello?app=1"},
                "value": [1745245204.461, "20"],
            },
            {
                "metric": {"request_uri": "/service/hello?app=2"},
                "value": [1745245204.461, "30"],
            },
            {
                "metric": {"request_uri": "/service/hello?app=3"},
                "value": [1745245204.461, "40"],
            },
        ],
    },
}

prometheus_vector_response_expected_vector_20: list[tuple[datetime.datetime, float]] = [
    (
        datetime.datetime.fromtimestamp(1745245204.461, tz=datetime.timezone.utc),
        20.0,
    ),
]

prometheus_vector_response_expected_vector_30: list[tuple[datetime.datetime, float]] = [
    (
        datetime.datetime.fromtimestamp(1745245204.461, tz=datetime.timezone.utc),
        30.0,
    ),
]

prometheus_vector_response_expected_vector_40: list[tuple[datetime.datetime, float]] = [
    (
        datetime.datetime.fromtimestamp(1745245204.461, tz=datetime.timezone.utc),
        40.0,
    ),
]

prometheus_matrix_response: dict[str, Any] = {
    "status": "success",
    "data": {
        "resultType": "matrix",
        "result": [
            {
                "metric": {"request_uri": "/service/hello?app=1"},
                "values": [
                    [1745243602.356, "1"],
                    [1745243659.356, "4"],
                    [1745243716.356, "8"],
                    [1745243773.356, "12"],
                    [1745243830.356, "16"],
                    [1745243887.356, "20"],
                    [1745243944.356, "20"],
                ],
            }
        ]
        * 3,
    },
}

prometheus_matrix_response_expected_point_list: list[
    tuple[datetime.datetime, float]
] = [
    (
        datetime.datetime.fromtimestamp(1745243602.356, tz=datetime.timezone.utc),
        1.0,
    ),
    (
        datetime.datetime.fromtimestamp(1745243659.356, tz=datetime.timezone.utc),
        4.0,
    ),
    (
        datetime.datetime.fromtimestamp(1745243716.356, tz=datetime.timezone.utc),
        8.0,
    ),
    (
        datetime.datetime.fromtimestamp(1745243773.356, tz=datetime.timezone.utc),
        12.0,
    ),
    (
        datetime.datetime.fromtimestamp(1745243830.356, tz=datetime.timezone.utc),
        16.0,
    ),
    (
        datetime.datetime.fromtimestamp(1745243887.356, tz=datetime.timezone.utc),
        20.0,
    ),
    (
        datetime.datetime.fromtimestamp(1745243944.356, tz=datetime.timezone.utc),
        20.0,
    ),
]

prometheus_empty_response: dict[str, Any] = {
    "status": "success",
    "data": {"resultType": "matrix", "result": []},
}

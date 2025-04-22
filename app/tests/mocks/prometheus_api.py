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

prometheus_empty_response: dict[str, Any] = {
    "status": "success",
    "data": {"resultType": "matrix", "result": []},
}

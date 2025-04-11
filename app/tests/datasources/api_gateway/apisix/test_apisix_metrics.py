import unittest

from app.datasources.api_gateway.apisix.apisix_metrics import (
    ApisixAggregatedBaseMetricEnum,
    ApisixAggregatedMetric,
    ApisixAggregationFunctionEnum,
    ApisixMetricTagFilterEnum,
    ApisixRequestsCounterMetric,
)


class TestApisixMetrics(unittest.TestCase):

    def test_apisix_metric_tag_filter_enum(self):
        self.assertEqual(ApisixMetricTagFilterEnum.ROUTE_NAME.value, "route_name")
        self.assertEqual(ApisixMetricTagFilterEnum.SERVICE_NAME.value, "service_name")
        self.assertEqual(ApisixMetricTagFilterEnum.CONSUMER.value, "consumer")
        self.assertEqual(
            ApisixMetricTagFilterEnum.RESPONSE_STATUS.value, "response_status"
        )

    def test_apisix_aggregation_function_enum(self):
        self.assertEqual(
            ApisixAggregationFunctionEnum.PERCENTILE_95.value, "95percentile"
        )
        self.assertEqual(ApisixAggregationFunctionEnum.AVG.value, "avg")
        self.assertEqual(ApisixAggregationFunctionEnum.COUNT.value, "count")
        self.assertEqual(ApisixAggregationFunctionEnum.MAX.value, "max")
        self.assertEqual(ApisixAggregationFunctionEnum.MEDIAN.value, "median")

    def test_apisix_aggregated_base_metric_enum(self):
        self.assertEqual(
            ApisixAggregatedBaseMetricEnum.APIGATEWAY_LATENCY.value,
            "apisix.apisix.latency",
        )
        self.assertEqual(
            ApisixAggregatedBaseMetricEnum.EGRESS_SIZE.value, "apisix.egress.size"
        )
        self.assertEqual(
            ApisixAggregatedBaseMetricEnum.INGRESS_SIZE.value, "apisix.ingress.size"
        )
        self.assertEqual(
            ApisixAggregatedBaseMetricEnum.REQUEST_LATENCY.value,
            "apisix.request.latency",
        )
        self.assertEqual(
            ApisixAggregatedBaseMetricEnum.UPSTREAM_LATENCY.value,
            "apisix.upstream.latency",
        )

    def test_apisix_aggregated_metric(self):
        metric_filters = {
            ApisixMetricTagFilterEnum.ROUTE_NAME: "route1",
            ApisixMetricTagFilterEnum.RESPONSE_STATUS: 200,
        }
        aggregated_metric = ApisixAggregatedMetric(
            ApisixAggregatedBaseMetricEnum.APIGATEWAY_LATENCY,
            ApisixAggregationFunctionEnum.PERCENTILE_95,
            metric_filters,
        )
        expected_query = (
            "apisix.apisix.latency.95percentile{route_name:route1,response_status:200}"
        )
        self.assertEqual(aggregated_metric.get_metric_query(), expected_query)

    def test_apisix_requests_counter_metric(self):
        metric_filters = {ApisixMetricTagFilterEnum.CONSUMER: "consumer1"}
        counter_metric = ApisixRequestsCounterMetric(metric_filters)
        expected_query = "apisix.request.counter{consumer:consumer1}"
        self.assertEqual(counter_metric.get_metric_query(), expected_query)

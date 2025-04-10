from unittest import IsolatedAsyncioTestCase, mock

from app.datasources.api_gateway.api_gateway_client import ApiGatewayClient
from app.datasources.api_gateway.apisix.apisix_client import get_apisix_client
from app.datasources.api_gateway.exceptions import ApiGatewayRequestError


class TestApisixClient(IsolatedAsyncioTestCase):

    apisix_client: ApiGatewayClient

    async def asyncSetUp(self):
        self.apisix_client = get_apisix_client()

    def setUp(self):
        get_apisix_client.cache_clear()

    def tearDown(self):
        get_apisix_client.cache_clear()

    async def asyncTearDown(self):
        consumers = await self.apisix_client.get_consumers()
        for consumer in consumers:
            await self.apisix_client.delete_consumer(consumer.name)

        consumer_groups = await self.apisix_client.get_consumer_groups()
        for consumer_group in consumer_groups:
            await self.apisix_client.delete_consumer_group(consumer_group.name)

    async def test_create_consumer_group(self):
        with self.assertRaises(ApiGatewayRequestError):
            await self.apisix_client.get_consumer_group("consumer_group_one")

        await self.apisix_client.add_consumer_group(
            "consumer_group_one",
            description="consumer_group_one description",
            labels={"env": "test"},
        )

        consumer_group = await self.apisix_client.get_consumer_group(
            "consumer_group_one"
        )
        self.assertEqual(consumer_group.name, "consumer_group_one")
        self.assertEqual(consumer_group.description, "consumer_group_one description")
        self.assertEqual(consumer_group.labels, {"env": "test"})
        self.assertEqual(consumer_group.plugins, {})

    async def test_update_consumer_group(self):
        with self.assertRaises(ApiGatewayRequestError):
            await self.apisix_client.update_consumer_group(
                "consumer_group_two",
                new_description="new description",
                new_labels={"env": "new"},
            )

        await self.apisix_client.add_consumer_group("consumer_group_two")

        consumer_group = await self.apisix_client.get_consumer_group(
            "consumer_group_two"
        )
        self.assertEqual(consumer_group.name, "consumer_group_two")
        self.assertEqual(consumer_group.description, None)
        self.assertEqual(consumer_group.labels, None)
        self.assertEqual(consumer_group.plugins, {})

        await self.apisix_client.update_consumer_group(
            "consumer_group_two",
            new_description="new description",
            new_labels={"env": "new"},
        )

        consumer_group = await self.apisix_client.get_consumer_group(
            "consumer_group_two"
        )
        self.assertEqual(consumer_group.name, "consumer_group_two")
        self.assertEqual(consumer_group.description, "new description")
        self.assertEqual(consumer_group.labels, {"env": "new"})
        self.assertEqual(consumer_group.plugins, {})

    async def test_set_rate_limit_consumer_group(self):
        with self.assertRaises(ApiGatewayRequestError):
            await self.apisix_client.set_rate_limit_to_consumer_group(
                "consumer_group_with_rate_limit", requests_number=5, time_window=1
            )

        await self.apisix_client.add_consumer_group("consumer_group_with_rate_limit")

        consumer_group = await self.apisix_client.get_consumer_group(
            "consumer_group_with_rate_limit"
        )
        self.assertEqual(consumer_group.plugins, {})

        await self.apisix_client.set_rate_limit_to_consumer_group(
            "consumer_group_with_rate_limit", requests_number=5, time_window=1
        )

        consumer_group = await self.apisix_client.get_consumer_group(
            "consumer_group_with_rate_limit"
        )
        self.assertEqual(
            consumer_group.plugins,
            {
                "limit-count": {
                    "show_limit_quota_header": True,
                    "count": 5,
                    "rejected_code": 429,
                    "rejected_msg": "Too many requests",
                    "policy": "local",
                    "time_window": 1,
                    "key_type": "var",
                    "key": "consumer_name",
                    "allow_degradation": False,
                }
            },
        )

    async def test_delete_consumer_group(self):
        await self.apisix_client.add_consumer_group("consumer_group_to_delete")

        consumer_group = await self.apisix_client.get_consumer_group(
            "consumer_group_to_delete"
        )
        self.assertIsNotNone(consumer_group)

        await self.apisix_client.delete_consumer_group("consumer_group_to_delete")

        with self.assertRaises(ApiGatewayRequestError):
            await self.apisix_client.get_consumer_group("consumer_group_to_delete")

    async def test_get_consumer_groups(self):
        await self.apisix_client.add_consumer_group("consumer_group_to_get")

        consumer_group = await self.apisix_client.get_consumer_group(
            "consumer_group_to_get"
        )
        self.assertIsNotNone(consumer_group)

        consumer_groups = await self.apisix_client.get_consumer_groups()
        self.assertListEqual(consumer_groups, [consumer_group])

    async def test_get_consumers(self):
        await self.apisix_client.upsert_consumer("consumer_to_get")

        consumer = await self.apisix_client.get_consumer("consumer_to_get")
        self.assertIsNotNone(consumer)

        consumers = await self.apisix_client.get_consumers()
        self.assertListEqual(consumers, [consumer])

    async def test_upsert_consumer(self):
        with self.assertRaises(ApiGatewayRequestError):
            await self.apisix_client.get_consumer("consumer_one")

        await self.apisix_client.upsert_consumer(
            "consumer_one",
            description="consumer_one description",
            labels={"env": "test"},
        )

        consumer = await self.apisix_client.get_consumer("consumer_one")
        self.assertEqual(consumer.name, "consumer_one")
        self.assertEqual(consumer.description, "consumer_one description")
        self.assertEqual(consumer.labels, {"env": "test"})
        self.assertIsNone(consumer.consumer_group_name)
        self.assertEqual(
            consumer.plugins,
            {
                "jwt-auth": {
                    "algorithm": "ES256",
                    "base64_secret": False,
                    "exp": 86400,
                    "key": "consumer_one",
                    "lifetime_grace_period": 0,
                    "public_key": "-----BEGIN PUBLIC KEY-----\n"
                    "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEXHVxB7s5SR7I9cWwry/JkECIReka\n"
                    "CwG3uOLCYbw5gVzn4dRmwMyYUJFcQWuFSfECRK+uQOOXD0YSEucBq0p5tA==\n"
                    "-----END PUBLIC KEY-----\n",
                }
            },
        )

        with self.assertRaises(ApiGatewayRequestError):
            await self.apisix_client.upsert_consumer(
                "consumer_one",
                description="consumer_one description",
                labels={"env": "test"},
                consumer_group_name="consumer_group_one",
            )

        await self.apisix_client.add_consumer_group("consumer_group_one")
        await self.apisix_client.upsert_consumer(
            "consumer_one",
            description="consumer_one description",
            labels={"env": "test"},
            consumer_group_name="consumer_group_one",
        )
        consumer = await self.apisix_client.get_consumer("consumer_one")
        self.assertEqual(consumer.consumer_group_name, "consumer_group_one")

    async def test_delete_consumer(self):
        await self.apisix_client.upsert_consumer("consumer_to_delete")

        consumer = await self.apisix_client.get_consumer("consumer_to_delete")
        self.assertIsNotNone(consumer)

        await self.apisix_client.delete_consumer("consumer_to_delete")

        with self.assertRaises(ApiGatewayRequestError):
            await self.apisix_client.get_consumer("consumer_to_delete")

    async def test_update_consumers_jwt_config(self):
        with mock.patch("app.config.settings.JWT_PUBLIC_KEY", "old key"):
            await self.apisix_client.upsert_consumer("consumer_one")
            await self.apisix_client.upsert_consumer("consumer_two")

        consumers = await self.apisix_client.get_consumers()
        for consumer in consumers:
            self.assertEqual(
                consumer.plugins,
                {
                    "jwt-auth": {
                        "public_key": "old key",
                        "algorithm": "ES256",
                        "base64_secret": False,
                        "exp": 86400,
                        "key": consumer.name,
                        "lifetime_grace_period": 0,
                    }
                },
            )

        with mock.patch("app.config.settings.JWT_PUBLIC_KEY", "new key"):
            await self.apisix_client.update_consumers_jwt_config()

        consumers = await self.apisix_client.get_consumers()
        for consumer in consumers:
            self.assertEqual(
                consumer.plugins,
                {
                    "jwt-auth": {
                        "public_key": "new key",
                        "algorithm": "ES256",
                        "base64_secret": False,
                        "exp": 86400,
                        "key": consumer.name,
                        "lifetime_grace_period": 0,
                    }
                },
            )

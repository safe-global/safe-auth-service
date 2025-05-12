import uuid

import faker

from app.datasources.db.connector import db_session_context
from app.datasources.db.models import ApiKey, User, Webhook

from .async_db_test_case import AsyncDbTestCase
from .factory import (
    generate_random_api_key,
    generate_random_user,
    generate_random_webhook,
)

fake = faker.Faker()


class TestModel(AsyncDbTestCase):
    @db_session_context
    async def test_user(self):
        user, _ = await generate_random_user()
        await user.create()
        result = await user.get_all()
        self.assertEqual(result[0], user)

    @db_session_context
    async def test_update_password(self):
        old_password = fake.password()
        user = await User(email=fake.email(), hashed_password=old_password).create()
        self.assertEqual(user.hashed_password, old_password)
        new_password = fake.password()

        updated = await User.update_password(uuid.uuid4(), new_password)
        self.assertFalse(updated)
        user = await User.get_by_user_id(user.id)
        self.assertEqual(user.hashed_password, old_password)

        updated = await User.update_password(user.id, new_password)
        self.assertTrue(updated)
        user = await User.get_by_user_id(user.id)
        self.assertEqual(user.hashed_password, new_password)

    @db_session_context
    async def test_api_key(self):
        user, _ = await generate_random_user()
        api_key = await generate_random_api_key(user.id)
        await api_key.create()
        result = await api_key.get_all()
        self.assertEqual(result[0], api_key)

    @db_session_context
    async def test_get_api_key_by_ids(self):
        user, _ = await generate_random_user()
        wrong_user, _ = await generate_random_user()
        api_key = await generate_random_api_key(user.id)
        api_key_other = await generate_random_api_key(user.id)

        result = await ApiKey.get_by_ids(api_key.id, wrong_user.id)
        self.assertIsNone(result)

        result = await ApiKey.get_by_ids(api_key.id, user.id)
        self.assertEqual(result, api_key)

        result = await ApiKey.get_by_ids(api_key_other.id, user.id)
        self.assertEqual(result, api_key_other)

    @db_session_context
    async def test_delete_api_key_by_ids(self):
        user, _ = await generate_random_user()
        api_key = await generate_random_api_key(user.id)
        api_key_other = await generate_random_api_key(user.id)

        result = await ApiKey.delete_by_ids(api_key.id, uuid.uuid4())
        self.assertFalse(result)

        result = await ApiKey.delete_by_ids(api_key.id, user.id)
        self.assertTrue(result)

        result = await ApiKey.get_by_ids(api_key.id, user.id)
        self.assertIsNone(result)

        result = await ApiKey.get_by_ids(api_key_other.id, user.id)
        self.assertEqual(result, api_key_other)

    @db_session_context
    async def test_get_api_keys_by_user(self):
        user, _ = await generate_random_user()

        result = await ApiKey.get_api_keys_by_user(user.id)
        self.assertEqual(result, [])

        api_keys = [await generate_random_api_key(user.id) for _ in range(5)]

        result = await ApiKey.get_api_keys_by_user(user.id)
        self.assertEqual(len(result), len(api_keys))
        self.assertEqual(result, api_keys)

    @db_session_context
    async def test_webhook(self):
        user, _ = await generate_random_user()
        webhook = await generate_random_webhook(user.id)
        await webhook.create()
        result = await webhook.get_all()
        self.assertEqual(result[0], webhook)

    @db_session_context
    async def test_get_webhook_by_ids(self):
        user, _ = await generate_random_user()
        wrong_user, _ = await generate_random_user()
        webhook = await generate_random_webhook(user.id)
        webhook_other = await generate_random_webhook(user.id)

        result = await Webhook.get_by_ids(webhook.id, wrong_user.id)
        self.assertIsNone(result)

        result = await Webhook.get_by_ids(webhook.id, user.id)
        self.assertEqual(result, webhook)

        result = await Webhook.get_by_ids(webhook_other.id, user.id)
        self.assertEqual(result, webhook_other)

    @db_session_context
    async def test_delete_webhook_by_ids(self):
        user, _ = await generate_random_user()
        webhook = await generate_random_webhook(user.id)
        webhook_other = await generate_random_webhook(user.id)

        result = await Webhook.delete_by_ids(webhook.id, uuid.uuid4())
        self.assertFalse(result)

        result = await Webhook.delete_by_ids(webhook.id, user.id)
        self.assertTrue(result)

        result = await Webhook.get_by_ids(webhook.id, user.id)
        self.assertIsNone(result)

        result = await Webhook.get_by_ids(webhook_other.id, user.id)
        self.assertEqual(result, webhook_other)

    @db_session_context
    async def test_get_webhooks_by_user(self):
        user, _ = await generate_random_user()

        result = await Webhook.get_webhooks_by_user(user.id)
        self.assertEqual(result, [])

        webhooks = [await generate_random_webhook(user.id) for _ in range(5)]

        result = await Webhook.get_webhooks_by_user(user.id)
        self.assertEqual(len(result), len(webhooks))
        self.assertEqual(result, webhooks)

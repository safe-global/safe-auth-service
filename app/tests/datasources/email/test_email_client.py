import uuid
from unittest import IsolatedAsyncioTestCase

import aiohttp

from app.config import settings
from app.datasources.email.email_client import send_email, send_register_temporary_token_email


class TestEmailClient(IsolatedAsyncioTestCase):
    """
    Email sending are tested using smtp4dev
    """

    async def asyncSetUp(self):
        deleted_messages = self._delete_messages()
        await deleted_messages

    async def _delete_messages(self) -> bool:
        """
        Delete all messages using smtp4dev API

        Returns:
            True if all messages were deleted, False otherwise
        """
        full_url = settings.SMTP_TEST_API_URL + "Messages/*?mailboxName=Default"
        async with aiohttp.ClientSession() as session:
            async with session.delete(full_url) as response:
                self.assertEqual(200, response.status)
        return True

    async def _get_number_messages(self) -> int:
        """
        Returns:
            Number of messages using smtp4dev API
        """
        full_url = settings.SMTP_TEST_API_URL + "Messages?mailboxName=Default"
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url) as response:
                self.assertEqual(200, response.status)
                result = await response.json()
                return result["rowCount"]

    async def test_send_email(self):
        self.assertEqual(await self._get_number_messages(), 0)
        sent_successfully = send_email(
            "random-address@safe.global", "<b>Hello!</b>", "Test subject"
        )
        self.assertTrue(sent_successfully)
        self.assertEqual(await self._get_number_messages(), 1)

    async def test_send_register_temporary_token_email(self):
        self.assertEqual(await self._get_number_messages(), 0)
        sent_successfully = send_register_temporary_token_email(
            "random-address@safe.global", uuid.uuid4().hex
        )
        self.assertTrue(sent_successfully)
        self.assertEqual(await self._get_number_messages(), 1)

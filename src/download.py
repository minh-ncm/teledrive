from telethon import TelegramClient
from settings import settings
from logger import get_logger
from client import DownloadClient
import telethon

telethon.errors.rpc_errors_re += (('FLOOD_PREMIUM_WAIT_(\\d+)', telethon.errors.FloodWaitError),)



logger = get_logger(__name__)
client = TelegramClient(
    "anon",
    api_id=settings.API_APP_ID,
    api_hash=settings.API_APP_HASH
)


async def main():
    await client.start()
    upload_client = DownloadClient(client)
    await upload_client.download()


if __name__ == '__main__':
    client.loop.run_until_complete(main())
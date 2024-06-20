from telethon import TelegramClient
from telethon.tl.types import PeerChat
from settings import settings
from logger import get_logger
from client import UploadClient


logger = get_logger(__name__)
client = TelegramClient(
    "anon",
    api_id=settings.API_APP_ID,
    api_hash=settings.API_APP_HASH
)


async def main():
    await client.start()
    # upload_client = UploadClient(client)
    # await upload_client.upload()

    entity = PeerChat(4245312988)
    message = await client.get_messages(entity, ids=7059)
    print(type(message))
    await client.download_media(message, file=message.file.name)



if __name__ == '__main__':
    client.loop.run_until_complete(main())
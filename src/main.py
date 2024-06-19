from telethon import TelegramClient
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
    upload_client = UploadClient(client)
    await upload_client.upload()

    # for task in tasks:
    #     message: Message = task.result()
    #     print(message)
    #     message = await client.get_messages(entity, ids=message.id)
    #     print(type(message))
    #     await client.download_media(message, file=message.file.name)



if __name__ == '__main__':
    client.loop.run_until_complete(main())
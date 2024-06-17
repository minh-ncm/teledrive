import asyncio
from telethon import TelegramClient
import os
from dotenv import load_dotenv
from telethon.tl.types import PeerChat

from settings import settings
from constants import FILE_MAX_SIZE
import glob
import math
from files import split_file_into_chunks, upload_file
from logger import get_logger
from rich.progress import Progress


logger = get_logger(__name__)
client = TelegramClient(
    "anon",
    api_id=settings.TELE_API_APP_ID,
    api_hash=settings.TELE_API_APP_HASH
)


async def main():
    await client.start()
    file_path = r"D:\New folder\c\MDCM-0011.mp4"
    file_chunks = split_file_into_chunks(file_path)
    entity = await client.get_entity(PeerChat(4245312988))

    with Progress() as progress:
        tasks = []
        async for file in file_chunks:
            # await upload_file(client, entity, file)
            tasks.append(asyncio.create_task(upload_file(client, entity, file, progress)))
        await asyncio.gather(*tasks)



if __name__ == '__main__':
    client.loop.run_until_complete(main())
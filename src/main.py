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
from asyncio import Task
from typing import List
from telethon.tl.patched import Message


logger = get_logger(__name__)
client = TelegramClient(
    "anon",
    api_id=settings.TELE_API_APP_ID,
    api_hash=settings.TELE_API_APP_HASH
)


async def main():
    await client.start()
    entity = await client.get_entity(PeerChat(4245312988))
    file_path = ".env"
    namespace = "/top/top2"
    file_chunks = split_file_into_chunks(file_path, namespace)
    with Progress() as progress:
        tasks: List[Task] = []
        async for file in file_chunks:
            tasks.append(asyncio.create_task(upload_file(client, entity, file, progress)))
        await asyncio.gather(*tasks)
    return
    for task in tasks:
        message: Message = task.result()
        print(message)
        message = await client.get_messages(entity, ids=message.id)
        print(type(message))
        await client.download_media(message, file=message.file.name)



if __name__ == '__main__':
    client.loop.run_until_complete(main())
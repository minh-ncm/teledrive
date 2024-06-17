import os
import math
import glob
from constants import FILE_MAX_SIZE
from typing import List, AsyncIterator
from telethon import TelegramClient
from telethon.tl.types import PeerChat
import asyncio
import random
from rich.progress import Progress

from logger import get_logger
from models import FileSchema, FileChunk
from constants import LOCAL_TEMP_DIR


logger = get_logger(__name__)


async def split_file_into_chunks(file_path: str) -> AsyncIterator[FileChunk]:
    f = open(file_path, 'rb')
    file_size = os.path.getsize(file_path)
    file_name, file_ext = os.path.splitext(os.path.split(file_path)[1])
    logger.info(f"Spliting {file_name}{file_ext} into chunks")

    total_chunks = math.ceil(file_size / FILE_MAX_SIZE)
    remain_size = file_size
    for chunk_index in range(total_chunks):
        chunk_cursor_index = chunk_index * FILE_MAX_SIZE
        f.seek(chunk_cursor_index)
        chunk_path = os.path.join(LOCAL_TEMP_DIR, f"{file_name}_{chunk_index:03d}{file_ext}")
        chunk_size = min(FILE_MAX_SIZE, remain_size)
        with open(chunk_path, 'wb') as part_file:
            chunk = f.read(chunk_size)
            part_file.write(chunk)
        remain_size = file_size - (chunk_index+1) * FILE_MAX_SIZE
        logger.info(f"Chunk {chunk_index} created for {file_name}{file_ext}")
        yield FileChunk(path=chunk_path, size=chunk_size)
    f.close()


def join_chunks_to_file(file_parts_path: List[str]):
    with open("joined.mp4", 'wb') as joined_file:
        for path in file_parts_path:
            with open(path, 'rb') as f:
                joined_file.write(f.read())


def get_progress_callback(progress: Progress, label: str, total: int):
    task = progress.add_task(label, total=total)

    def progress_callback(sent_bytes, total):
        progress.update(task, completed=sent_bytes)

    return progress_callback

async def upload_file(telegram_client: TelegramClient, entity: PeerChat, file: FileChunk, progress: Progress):
    progress_callback = get_progress_callback(progress, f"Uploading... {file.path}", file.size)
    await telegram_client.send_file(entity, open(file.path, "rb"), progress_callback=progress_callback, force_document=True)
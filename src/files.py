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
import os
from logger import get_logger
from models import FileChunk, FileModel
from constants import LOCAL_TEMP_DIR, CHUNK_PART_NAME_FORMAT
from telethon.tl.patched import Message
from pathlib import Path
from database import get_engine
from sqlalchemy.orm import Session


logger = get_logger(__name__)


def create_local_namespace(path):
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Create local namespace: {path}")


async def split_file_into_chunks(file_path: str, namespace: str) -> AsyncIterator[FileChunk]:
    namespace = os.path.normpath(namespace[1:] if namespace.startswith("/") else namespace)
    chunk_output_dir = os.path.join(LOCAL_TEMP_DIR, namespace)
    create_local_namespace(chunk_output_dir)

    f = open(file_path, 'rb')
    file_size = os.path.getsize(file_path)
    file_name, file_ext = os.path.splitext(os.path.split(file_path)[1])
    logger.info(f"Spliting {file_name}{file_ext} into chunks")

    total_chunks = math.ceil(file_size / FILE_MAX_SIZE)
    remain_size = file_size
    for chunk_index in range(total_chunks):
        chunk_cursor_index = chunk_index * FILE_MAX_SIZE
        f.seek(chunk_cursor_index)
        if total_chunks <= 1:
            chunk_name = f"{file_name}{file_ext}"
        else:
            chunk_name = f"{file_name}.{chunk_index}{file_ext}"
        chunk_path = os.path.join(chunk_output_dir, chunk_name)
        chunk_size = min(FILE_MAX_SIZE, remain_size)
        with open(chunk_path, 'wb') as part_file:
            chunk = f.read(chunk_size)
            part_file.write(chunk)
        remain_size = file_size - (chunk_index+1) * FILE_MAX_SIZE
        logger.info(f"Created file chunk: {chunk_name} in {chunk_path}")
        yield FileChunk(path=chunk_path, size=chunk_size, og_name=file_name)
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


def track_file_to_db(file: FileChunk):
    engine = get_engine()
    with Session(engine) as session:
        new_file = FileModel(og_name=file.og_name, path=file.path, tele_id=file.tele_id)
        session.add(new_file)
        session.commit()
        logger.info(f"Tracked: {new_file}")

async def upload_file(telegram_client: TelegramClient, entity: PeerChat, file: FileChunk, progress: Progress) -> Message:
    progress_callback = get_progress_callback(progress, f"Uploading... {file.path}", file.size)
    message = await telegram_client.send_file(entity, open(file.path, "rb"), progress_callback=progress_callback, force_document=True)
    file.tele_id = message.id
    track_file_to_db(file)
    return message
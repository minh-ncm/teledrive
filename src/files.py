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


def join_chunks_to_file(file_parts_path: List[str]):
    with open("joined.mp4", 'wb') as joined_file:
        for path in file_parts_path:
            with open(path, 'rb') as f:
                joined_file.write(f.read())


async def download_file(telegram_client: TelegramClient, entity: PeerChat, message_id: int, file: FileModel) -> Message:
    message: Message = await telegram_client.get_messages(entity=entity, ids=message_id)
    telegram_client.download_media(message, file=os.path.normpath(file.path))
    logger.info(f"Downloaded {file.path}")
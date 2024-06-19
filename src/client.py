import asyncio
import os
import math
from typing import List, AsyncIterator
from telethon import TelegramClient
from telethon.tl.types import PeerChat
from telethon.hints import EntityLike, MessageLike
from settings import settings, upload_list
from logger import get_logger
from models import FileChunk, FileModel
from rich.progress import Progress
import utils
import constants


logger = get_logger(__name__)


class UploadClient:
    def __init__(self, client: TelegramClient):
        self._client = client

    
    async def _split_file_into_chunks(file_path: str, namespace: str) -> AsyncIterator[FileChunk]:
        namespace = os.path.normpath(namespace[1:] if namespace.startswith("/") else namespace)
        chunk_output_dir = os.path.join(constants.LOCAL_TEMP_DIR, namespace)
        utils.create_local_path(chunk_output_dir)

        f = open(file_path, 'rb')
        file_size = os.path.getsize(file_path)
        file_name, file_ext = os.path.splitext(os.path.split(file_path)[1])
        logger.info(f"Spliting {file_name}{file_ext} into chunks")

        total_chunks = math.ceil(file_size / constants.FILE_MAX_SIZE)
        remain_size = file_size
        for chunk_index in range(total_chunks):
            chunk_cursor_index = chunk_index * constants.FILE_MAX_SIZE
            f.seek(chunk_cursor_index)
            if total_chunks <= 1:
                chunk_name = f"{file_name}{file_ext}"
            else:
                chunk_name = f"{file_name}.{chunk_index}{file_ext}"
            chunk_path = os.path.join(chunk_output_dir, chunk_name)
            chunk_size = min(constants.FILE_MAX_SIZE, remain_size)
            with open(chunk_path, 'wb') as part_file:
                chunk = f.read(chunk_size)
                part_file.write(chunk)
            remain_size = file_size - (chunk_index+1) * constants.FILE_MAX_SIZE
            logger.info(f"Created file chunk: {chunk_name} in {chunk_path}")
            yield FileChunk(path=chunk_path, size=chunk_size, og_name=file_name)
        f.close()

    async def _upload_file(self, entity: EntityLike, file: FileChunk, progress: Progress) -> MessageLike:
        progress_callback = utils.get_progress_callback(progress, f"Uploading... {file.path}", file.size)
        if utils.is_tracked_file_in_db(file):
            logger.warn(f"Already tracked: {file}. Skipping upload")
            return
        
        message = await self._client.send_file(entity, open(file.path, "rb"), progress_callback=progress_callback, force_document=True)
        file.tele_id = message.id
        utils.track_upload_file_to_db(file)
        logger.info(f"Uploaded: {file.path} chunk")
        os.remove(file.path)
        logger.info(f"Removed {file.path} chunk")
        return message

    async def upload(self):
        entity = await self._client.get_entity(PeerChat(settings.CHAT_ID))
        for info in upload_list:
            file_chunks = self._split_file_into_chunks(info.path, info.namespace)
            with Progress() as progress:
                tasks: List[asyncio.Task] = []
                async for file in file_chunks:
                    tasks.append(asyncio.create_task(self._upload_file(entity, file, progress)))
                await asyncio.gather(*tasks)
            logger.info(f"Complete upload all chunks of {info.path}")

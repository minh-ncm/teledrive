import asyncio
import os
import math
from typing import List, AsyncGenerator
from telethon import TelegramClient
from telethon.tl.types import PeerChat
from telethon.hints import EntityLike, MessageLike
from settings import settings, upload_list, download_list
from logger import get_logger
from models import FileChunk, FileModel
from rich.progress import Progress
import utils
import constants


logger = get_logger(__name__)


class UploadClient:
    def __init__(self, client: TelegramClient):
        self._client = client

    
    async def _split_file_into_chunks(self, file_path: str, namespace: str) -> AsyncGenerator[FileChunk, None]:
        """
        Split file into multiple chunks if larger than FILE_MAX_SIZE. Chunks will be saved in LOCAL_TEMP_DIR/namespace dir

        Args:
            file_path (str): path to the original file
            namespace (str): path from the root of LOCAL_TEMP_DIR to store the chunks

        Returns:
            AsyncIterator[FileChunk]: _description_

        Yields:
            Iterator[AsyncIterator[FileChunk]]: _description_
        """
        # Create namespace folder in local temp dir
        namespace = os.path.normpath(namespace[1:] if namespace.startswith("/") else namespace)
        chunk_output_dir = os.path.join(constants.LOCAL_TEMP_DIR, namespace)
        utils.create_local_path(chunk_output_dir)

        # Open file and calculate total number of chunks
        f = open(file_path, 'rb')
        file_size = os.path.getsize(file_path)
        file_name, file_ext = os.path.splitext(os.path.basename(file_path))
        total_chunks = math.ceil(file_size / constants.FILE_MAX_SIZE)
        remain_size = file_size
        logger.info(f"Spliting {file_name}{file_ext} into {total_chunks} chunks")

        for chunk_index in range(total_chunks):
            # Move cursor to the beginning of the next chunk
            chunk_cursor_index = chunk_index * constants.FILE_MAX_SIZE
            f.seek(chunk_cursor_index)

            # Add chunk index to file name if there is more than one chunk
            if total_chunks <= 1:
                chunk_name = f"{file_name}{file_ext}"
            else:
                chunk_name = f"{file_name}.{chunk_index}{file_ext}"
            
            # Write the chunk to disk
            chunk_path = os.path.join(chunk_output_dir, chunk_name)
            chunk_size = min(constants.FILE_MAX_SIZE, remain_size)
            with open(chunk_path, 'wb') as part_file:
                chunk = f.read(chunk_size)
                part_file.write(chunk)

            # Calculate remaining size for reading final chunk
            remain_size = file_size - (chunk_index+1) * constants.FILE_MAX_SIZE

            logger.info(f"Created file chunk: {chunk_name}")
            yield FileChunk(namespace=namespace, size=chunk_size, og_name=file_name+file_ext, chunk_name=chunk_name)
        f.close()

    async def _upload_file(self, entity: EntityLike, file: FileChunk, progress: Progress) -> MessageLike:
        progress_callback = utils.get_progress_callback(progress, f"Uploading {file.chunk_name}", file.size)
        if utils.is_tracked_file_in_db(file):
            logger.warn(f"Already tracked: {file}. Skipping upload")
            return
        
        chunk_path = os.path.join(constants.LOCAL_TEMP_DIR, file.namespace, file.chunk_name)
        message = await self._client.send_file(
            entity,
            open(chunk_path, "rb"), 
            progress_callback=progress_callback, 
            force_document=True
        )
        file.tele_id = message.id
        utils.track_upload_file_to_db(file)
        logger.info(f"Uploaded: {file.chunk_name} chunk")
        os.remove(chunk_path)
        logger.info(f"Removed {file.chunk_name} chunk")
        return message

    async def upload(self, asynchronous: bool = False):
        entity = await self._client.get_entity(PeerChat(settings.CHAT_ID))
        for info in upload_list:
            file_chunks = self._split_file_into_chunks(info.path, info.namespace)
            with Progress() as progress:
                tasks: List[asyncio.Task] = []
                async for file in file_chunks:
                    if asynchronous:
                        tasks.append(asyncio.create_task(self._upload_file(entity, file, progress)))
                    else:
                        await self._upload_file(entity, file, progress)
                await asyncio.gather(*tasks)
            logger.info(f"Complete upload all chunks of {info.path}")


class DownloadClient:
    def __init__(self, client: TelegramClient):
        self._client = client

    async def download(self, asynchronous: bool = False):
        entity = await self._client.get_entity(PeerChat(settings.CHAT_ID))
        for info in download_list:
            with Progress() as progress:
                tracked_chunks = utils.get_file_tracked_chunks(info.og_name, info.namespace)
                chunks = []
                async for chunk in tracked_chunks:
                    if asynchronous:
                        tasks.append(asyncio.create_task(self._download_file(entity, chunk, progress)))
                    else:
                        await self._download_file(entity, chunk, progress)
                    chunks.append(chunk)
                tasks: List[asyncio.Task] = []
                await asyncio.gather(*tasks)
            logger.info(f"Complete download all chunks of {info.og_name}")
            self._join_chunks_to_file(chunks)


    def _join_chunks_to_file(self, chunks: List[FileModel]):
        if len(chunks) <= 1:
            logger.warning(f"No need to join {len(chunks)} chunk")
        first_file = chunks[0]
        output_dir = os.path.join(constants.LOCAL_TEMP_DIR, first_file.namespace)
        with open(os.path.join(output_dir, first_file.og_name), 'wb') as joined_file:
            for path in chunks:
                logger.info(f"Joining {path.chunk_name}")
                with open(os.path.join(output_dir, path.chunk_name), 'rb') as f:
                    joined_file.write(f.read())
                os.remove(os.path.join(output_dir, path.chunk_name))
                logger.info(f"Removed {path.chunk_name}")
        logger.info(f"Joined all chunks for {first_file.og_name} in {output_dir}")


    async def _download_file(self, entity: PeerChat, file: FileModel, progress: Progress) -> MessageLike:
        message: MessageLike = await self._client.get_messages(entity, ids=file.tele_id)
        progress_callback = utils.get_progress_callback(progress, f"Downloading {file.chunk_name}", message.file.size)
        chunk_path = os.path.join(constants.LOCAL_TEMP_DIR, file.namespace, file.chunk_name)
        await self._client.download_media(message, file=chunk_path, progress_callback=progress_callback)
        logger.info(f"Downloaded to {chunk_path}")
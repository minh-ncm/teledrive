# -*- coding: utf-8 -*-
import os
from typing import Callable

from telethon.hints import EntityLike, MessageLike
from telethon.sync import TelegramClient
from telethon.tl.types import PeerChat

import constants
import utils
from abstract import Singleton
from logger import get_logger
from models import FileChunk, FileModel
from settings import settings
from utils.pyside import PySideProgressBarDialogCallback

logger = get_logger(__name__)


class ClientManager(metaclass=Singleton):
    def __init__(self) -> None:
        self.client = None

    def create_client(self, api_id: int | None, api_hash: str | None):
        if api_id is None:
            logger.error("API ID cannot be None")
        if api_hash is None:
            logger.error("API Hash cannot be None")

        if self.client is None:
            self.client = TelegramClient(constants.TELEGRAM_SESSION_NAME, api_id, api_hash)
            logger.info("Client created")
        else:
            logger.info("Client already created")

    def get_client(self):
        if self.client and not self.client.is_connected():
            logger.info("Connecting client")
            self.client.connect()
            logger.info("Client connected")
        if self.client is None:
            logger.warning("Getting empty client")
        return self.client

    def download_chunk(self, chunk: FileModel, delete_after: bool = False):
        download_client = DownloadClient(self.get_client())
        download_client.download(chunk, delete_after)

    def upload_chunk(self, namespace: str, file_chunk: FileChunk) -> bool:
        logger.info(f"Preparing to upload: {file_chunk.chunk_name} to {namespace}")
        upload_client = UploadClient(self.get_client())
        message = upload_client.upload(file_chunk)
        if message:
            return True
        else:
            return False

    def disconnect_client(self):
        if self.client and self.client.is_connected():
            self.client.disconnect()


class UploadClient:
    def __init__(self, client: TelegramClient):
        self._client = client

    def _upload_file(self, entity: EntityLike, file: FileChunk, progress_callback: Callable) -> MessageLike:
        chunk_path = os.path.join(constants.LOCAL_TEMP_DIR, file.namespace, file.chunk_name)
        message = self._client.send_file(
            entity, open(chunk_path, "rb"), progress_callback=progress_callback, force_document=True
        )
        file.tele_id = message.id
        file.size = message.document.size
        # Store uploaded file's info in db
        utils.track_upload_file_to_db(file)
        logger.info(f"Uploaded: {file.chunk_name} chunk")

        return message

    def upload(self, chunk: FileChunk) -> MessageLike:
        entity = self._client.get_entity(PeerChat(settings.CHAT_ID))
        callback_manager = PySideProgressBarDialogCallback()
        message = self._upload_file(entity, chunk, callback_manager.get_progess_dialog_callback(chunk.chunk_name))
        return message


class DownloadClient:
    def __init__(self, client: TelegramClient):
        self._client = client

    def download(self, file: FileModel, delete_after: bool = False):
        entity = self._client.get_entity(PeerChat(settings.CHAT_ID))
        callback_manager = PySideProgressBarDialogCallback()
        self._download_file(entity, file, callback_manager.get_progess_dialog_callback(file.chunk_name))
        logger.info(f"Complete download all chunks of {file.og_name}")

        # Delete telegram messages
        if delete_after:
            self._client.delete_messages(entity, message_ids=file.tele_id)
            logger.info(f"Deleted {file.chunk_name} from Telegram")

    def _download_file(self, entity: PeerChat, file: FileModel, progress_callback: Callable) -> MessageLike:
        message: MessageLike = self._client.get_messages(entity, ids=file.tele_id)
        # Create download directory if not existed
        download_dir = os.path.join(constants.LOCAL_TEMP_DIR, file.namespace)
        utils.create_local_path(download_dir)

        # Download chunks to LOCAL_TEMP_DIR
        chunk_path = os.path.join(download_dir, file.chunk_name)
        self._client.download_media(message, file=chunk_path, progress_callback=progress_callback)
        logger.info(f"Downloaded to {chunk_path}")

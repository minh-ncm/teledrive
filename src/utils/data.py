# -*- coding: utf-8 -*-
from sqlalchemy import select
from sqlalchemy.orm import Session
from telethon.sync import TelegramClient
from telethon.tl.types import PeerChat

from database import get_engine
from models import FileModel
from settings import settings


def update_chunk_size():
    client = TelegramClient("anon", api_id=settings.API_APP_ID, api_hash=settings.API_APP_HASH)
    client.start()
    entity = client.get_entity(PeerChat(settings.CHAT_ID))

    engine = get_engine()
    with Session(engine) as session:
        stmt = select(FileModel)
        result = session.execute(stmt)

        for chunk in result.scalars():
            message = client.get_messages(entity, ids=chunk.tele_id)
            chunk.size = message.document.size
        session.commit()

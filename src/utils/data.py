# -*- coding: utf-8 -*-
from sqlalchemy import select
from sqlalchemy.orm import Session
from telethon.tl.types import PeerChat

from client import ClientManager
from database import get_engine
from models import FileModel
from settings import settings


def update_chunk_size():
    manager = ClientManager()
    manager.create_client(settings.API_APP_ID, settings.API_APP_HASH)
    client = manager.get_client()
    entity = client.get_entity(PeerChat(settings.CHAT_ID))

    engine = get_engine()
    with Session(engine) as session:
        stmt = select(FileModel).where(FileModel.size == None)  # noqa
        result = session.execute(stmt)

        for chunk in result.scalars():
            message = client.get_messages(entity, ids=chunk.tele_id)
            chunk.size = message.document.size
        session.commit()

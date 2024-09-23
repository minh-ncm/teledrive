# -*- coding: utf-8 -*-
from telethon.tl.types import PeerChat

from client import ClientManager
from settings import settings

if __name__ == "__main__":
    manager = ClientManager()
    manager.create_client(settings.API_APP_ID, settings.API_APP_HASH)
    client = manager.get_client()

    entity = client.get_entity(PeerChat(settings.CHAT_ID))
    message = client.get_messages(entity, ids=7805)

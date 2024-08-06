# -*- coding: utf-8 -*-
from telethon.tl.custom.dialog import Dialog

from client import ClientManager
from settings import settings

if __name__ == "__main__":
    manager = ClientManager()
    manager.create_client(settings.API_APP_ID, settings.API_APP_HASH)
    client = manager.get_client()

    for dialog in client.iter_dialogs():
        dialog: Dialog
        if dialog.is_group:
            print(dialog.name)
            print(dialog.message.peer_id)

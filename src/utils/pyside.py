# -*- coding: utf-8 -*-
from typing import Dict

from PySide6.QtWidgets import QProgressDialog

from abstract import Singleton


class PySideProgressBarDialogCallback(metaclass=Singleton):
    def __init__(self) -> None:
        self.progress_dialogs: Dict[str, QProgressDialog] = {}

    def add_progress_dialog(self, progress_dialog: QProgressDialog, name: str):
        if name not in self.progress_dialogs:
            self.progress_dialogs[name] = progress_dialog

    def get_progess_dialog_callback(self, name: str):
        def progress_callback(sent_bytes, total):
            self.progress_dialogs[name].setValue(sent_bytes)

        if name not in self.progress_dialogs:
            return None
        return progress_callback

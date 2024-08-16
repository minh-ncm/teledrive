# -*- coding: utf-8 -*-
import json

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from constants import FILE_NAME_CONFIG
from logger import get_logger
from widgets.dialogs import SelectChatDialog, SetupAPIDialog, SignInDialog

logger = get_logger(__name__)


class FirstTimeView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        label = QLabel()
        label.setText(
            "Welcome to Teledrive. Please set up the following configs before using any features.\n \
            If you don't have API ID and hash. Please follow the instructions below at: \
            https://docs.telethon.dev/en/stable/basic/signing-in.html#signing-in"
        )

        self._layout = QVBoxLayout()
        self._layout.addWidget(label)

        setup_api_button = QPushButton("Setup API", self)
        self._layout.addWidget(setup_api_button)
        setup_api_button.clicked.connect(self._setup_api)

        self.setLayout(self._layout)

    def _setup_api(self):
        setup_api_dialog = SetupAPIDialog(self)
        setup_api_dialog_result = setup_api_dialog.exec()

        if setup_api_dialog_result == QDialog.DialogCode.Accepted:
            self._api_app_hash = setup_api_dialog.api_app_hash
            self._api_app_id = setup_api_dialog.api_app_id

            signin_dialog = SignInDialog(self, self._api_app_id, self._api_app_hash)
            signin_dialog_result = signin_dialog.exec()
            if signin_dialog_result == QDialog.DialogCode.Accepted:
                select_chat_dialog = SelectChatDialog(self, self._api_app_id, self._api_app_hash)
                select_chat_dialog_result = select_chat_dialog.exec()

                if select_chat_dialog_result == QDialog.DialogCode.Accepted:
                    logger.info(
                        f"Saving \
                        API app id: {self._api_app_id}\n \
                        API app hash: {self._api_app_hash}\n \
                        Phone number: {signin_dialog.phone_number}\n \
                        Chat ID: {select_chat_dialog.selected_chat_id}"
                    )
                    self._save_configs(
                        self._api_app_id,
                        self._api_app_hash,
                        signin_dialog.phone_number,
                        select_chat_dialog.selected_chat_id,
                    )
                    logger.info("Saved configs.")

    def _save_configs(self, api_app_id, api_app_hash, phone_number, chat_id):
        if isinstance(chat_id, int) and chat_id < 0:
            chat_id = abs(chat_id)
        json.dump(
            {
                "API_APP_ID": api_app_id,
                "API_APP_HASH": api_app_hash,
                "PHONE_NUMBER": phone_number,
                "CHAT_ID": chat_id,
            },
            open(FILE_NAME_CONFIG, "w+"),
        )
        self.parent().layout().setCurrentIndex(1)  # Change to main view

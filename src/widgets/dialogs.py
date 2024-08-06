# -*- coding: utf-8 -*-
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from telethon.tl.custom.dialog import Dialog

from client import ClientManager
from logger import get_logger

logger = get_logger(__name__)


class ConfirmDownloadDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Confirm Download")
        self.setModal(False)
        self.delete_after = False

        layout = QVBoxLayout()
        self.setLayout(layout)

        checkbox = QCheckBox("Delete after download")
        checkbox.checkStateChanged.connect(self._toggle_delete_after)
        layout.addWidget(checkbox)

        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

    def _toggle_delete_after(self, state):
        self.delete_after = state == Qt.CheckState.Checked


class SetupAPIDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Setup API")
        self.setModal(False)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # display textbox for api app id
        api_app_id_label = QLabel("API app ID:", self)
        layout.addWidget(api_app_id_label)
        api_app_id_edit = QLineEdit(self)
        layout.addWidget(api_app_id_edit)

        # display textbox for api app hash
        api_app_hash_label = QLabel("API App hash:", self)
        layout.addWidget(api_app_hash_label)
        api_app_hash_edit = QLineEdit(self)
        layout.addWidget(api_app_hash_edit)

        # display dialog actions
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(lambda: self._save_api_config(api_app_id_edit.text(), api_app_hash_edit.text()))
        buttonBox.rejected.connect(self.reject)

    def _save_api_config(self, api_app_id, api_app_hash):
        logger.info(f"User entered api app id: {api_app_id} and api app hash: {api_app_hash}")
        self.api_app_id = api_app_id
        self.api_app_hash = api_app_hash
        self.accept()


class SignInDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, api_app_id: str = "", api_app_hash: str = "") -> None:
        self._api_app_id = api_app_id
        self._api_app_hash = api_app_hash
        self.phone_number = None
        super().__init__(parent)

        self.setWindowTitle("Sign in")
        self.setModal(False)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # display textbox for enter phone number
        api_app_hash_label = QLabel("Phone number:", self)
        layout.addWidget(api_app_hash_label)
        self._phone_number_edit = QLineEdit(self)
        layout.addWidget(self._phone_number_edit)

        # display button for request signin code
        send_code_button = QPushButton("Send code", self)
        layout.addWidget(send_code_button)
        send_code_button.clicked.connect(self._send_code)

        # display textbox for enter signin code
        signin_code_label = QLabel("Sign in code:", self)
        layout.addWidget(signin_code_label)
        self._signin_code_edit = QLineEdit(self)
        layout.addWidget(self._signin_code_edit)

        # Sign in with signin code
        verify_code_button = QPushButton("Sign in", self)
        layout.addWidget(verify_code_button)
        verify_code_button.clicked.connect(self._verify_code)

    def _send_code(self):
        self.phone_number = self._phone_number_edit.text()
        manager = ClientManager()
        manager.create_client(self._api_app_id, self._api_app_hash)
        client = manager.get_client()
        logger.info(f"Request sending sign in code to {self.phone_number}")
        sent = client.send_code_request(self.phone_number)
        logger.info("Request sent")
        logger.debug(sent)

    def _verify_code(self):
        code = self._signin_code_edit.text()
        logger.debug(f"Sign in code: {code}")
        client = ClientManager().get_client()
        logger.info("Signing in")
        sent = client.sign_in(self.phone_number, code)
        logger.info("Sign in successfully")
        logger.debug(sent)
        self.accept()


class UploadNamespaceDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Upload Namespace")
        self.setModal(False)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # display textbox for enter namespace
        namespace_label = QLabel("Namespace:", self)
        layout.addWidget(namespace_label)
        namespace_edit = QLineEdit(self)
        layout.addWidget(namespace_edit)

        # display dialog actions
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(lambda: self._save_namespace(namespace_edit.text()))
        buttonBox.rejected.connect(self.reject)

    def _save_namespace(self, namespace: str):
        logger.info(f"Uploading with namespace: {namespace}")
        self.namespace = namespace
        self.accept()


class SelectChatDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, api_app_id: str = None, api_app_hash: str = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select group chat will be used for upload")
        self.setModal(False)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # display textbox for enter namespace
        self._group_chat_list_widget = QListWidget(self)
        self._group_chat_list_widget.setSelectionMode(self._group_chat_list_widget.SelectionMode.SingleSelection)
        layout.addWidget(self._group_chat_list_widget)
        self._group_chat_list_widget.itemClicked.connect(self.set_selected_id)

        manager = ClientManager()
        manager.create_client(api_app_id, api_app_hash)
        client = manager.get_client()

        self._group_chat_ids = []
        self.selected_chat_id = None
        for dialog in client.iter_dialogs():
            dialog: Dialog
            if dialog.is_group:
                self._group_chat_ids.append(dialog.id)
                group_chat_list_widget_item = QListWidgetItem(dialog.name)
                self._group_chat_list_widget.addItem(group_chat_list_widget_item)

        # display dialog actions
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(lambda: self.get_selected_group_chat_id())
        buttonBox.rejected.connect(self.reject)

    def set_selected_id(self, item: QListWidgetItem):
        self._selected_id = self._group_chat_list_widget.indexFromItem(item).row()

    def get_selected_group_chat_id(self) -> int:
        self.selected_chat_id = self._group_chat_ids[self._selected_id]
        self.accept()

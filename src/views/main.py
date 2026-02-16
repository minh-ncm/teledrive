# -*- coding: utf-8 -*-
import os
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFileSystemModel,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QProgressDialog,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from telethon.tl.types import PeerChat

import constants
import utils
from client import ClientManager
from logger import get_logger
from settings import ChunkInfo, settings
from utils.pyside import PySideProgressBarDialogCallback
from widgets.dialogs import ConfirmDownloadDialog, UploadNamespaceDialog

logger = get_logger(__name__)


def cancel_upload():
    client_manager = ClientManager()
    # client_manager.disconnect_client()


class MainView(QWidget):
    ITEMS_PER_PAGE = 50

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.current_page = 0
        self.search_query = ""
        self.total_items = 0

        layout = QVBoxLayout(self)

        # Search box section
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Search by filename or namespace...")
        self.search_box.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        # File list widget
        self.file_widgets = QListWidget(self)
        layout.addWidget(self.file_widgets)
        self.file_widgets.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.file_widgets.itemClicked.connect(self._select_checkbox)

        # Pagination controls section
        pagination_layout = QHBoxLayout()

        self.prev_button = QPushButton("← Previous")
        self.prev_button.clicked.connect(self._previous_page)
        pagination_layout.addWidget(self.prev_button)

        self.page_info_label = QLabel("Page 1 of 1")
        self.page_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pagination_layout.addWidget(self.page_info_label)

        self.next_button = QPushButton("Next →")
        self.next_button.clicked.connect(self._next_page)
        pagination_layout.addWidget(self.next_button)

        pagination_layout.addStretch()

        layout.addLayout(pagination_layout)
        self.setLayout(layout)

        # Load initial data
        self._load_page()

    def _select_files_to_upload(self):
        file_paths, extension_desc = QFileDialog.getOpenFileNames(self)
        # Exit if no file selected
        if not file_paths:
            return
        dialog = UploadNamespaceDialog(self)
        dialog_result = dialog.exec()
        if dialog_result == dialog.DialogCode.Accepted:
            manager = ClientManager()
            for path in file_paths:
                file_chunks = utils.split_file_into_chunks(path, dialog.namespace)
                for chunk in file_chunks:
                    if utils.is_tracked_file_in_db(chunk):
                        logger.warn(f"Already tracked: {chunk.chunk_name}.")
                    else:
                        # Create progress dialog
                        progress_dialog = QProgressDialog(
                            f"Uploading {chunk.chunk_name}", "Cancel", 0, chunk.size, self
                        )
                        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                        progress_dialog.canceled.connect(cancel_upload)

                        # Add progress dialog to manager
                        callback_manager = PySideProgressBarDialogCallback()
                        callback_manager.add_progress_dialog(progress_dialog, chunk.chunk_name)

                        # Upload chunk
                        manager.upload_chunk(dialog.namespace, chunk)

                    # Delete chunk file after upload
                    chunk_path = os.path.join(constants.LOCAL_TEMP_DIR, chunk.namespace, chunk.chunk_name)
                    os.remove(chunk_path)
                    logger.info(f"Removed {chunk.chunk_name} chunk")

                # Add uploaded file to UI list
                og_name = os.path.basename(path)
                logger.info(f"Completed upload {og_name}")
                # Reload the page to reflect the newly uploaded file
                self._load_page()

    def _select_folder_to_upload(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        for widget_type in (QListView, QTreeView):
            for view in file_dialog.findChildren(widget_type):
                if isinstance(view.model(), QFileSystemModel):
                    view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        file_dialog.exec()
        folder_paths = file_dialog.selectedFiles()

        # folder_path = QFileDialog.getExistingDirectory(self)
        # Exit if no folder selected
        if not folder_paths:
            return
        dialog = UploadNamespaceDialog(self)
        dialog_result = dialog.exec()
        if dialog_result == dialog.DialogCode.Accepted:
            manager = ClientManager()
            for folder_path in folder_paths:
                file_chunks = utils.split_file_into_chunks(folder_path, dialog.namespace)
                for chunk in file_chunks:
                    if utils.is_tracked_file_in_db(chunk):
                        logger.warn(f"Already tracked: {chunk.chunk_name}.")
                    else:
                        # Create progress dialog
                        progress_dialog = QProgressDialog(
                            f"Uploading {chunk.chunk_name}", "Cancel", 0, chunk.size, self
                        )
                        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                        progress_dialog.canceled.connect(cancel_upload)

                        # Add progress dialog to manager
                        callback_manager = PySideProgressBarDialogCallback()
                        callback_manager.add_progress_dialog(progress_dialog, chunk.chunk_name)

                        # Upload chunk
                        manager.upload_chunk(dialog.namespace, chunk)

                    # Delete chunk file after upload
                    chunk_path = os.path.join(constants.LOCAL_TEMP_DIR, chunk.namespace, chunk.chunk_name)
                    os.remove(chunk_path)
                    logger.info(f"Removed {chunk.chunk_name} chunk")

                os.remove(chunk.get_local_path())

                # Add uploaded folder zip to UI list - reload page to reflect the newly uploaded folder
                logger.info(f"Completed upload {os.path.basename(folder_path)}.zip")
                self._load_page()

    def _load_page(self):
        """Load files for the current page with the current search query."""
        offset = self.current_page * self.ITEMS_PER_PAGE
        tracked_files = utils.list_tracked_file(
            offset=offset, limit=self.ITEMS_PER_PAGE, search_query=self.search_query
        )
        self.total_items = utils.get_tracked_file_count(self.search_query)

        # Clear the list widget
        self.file_widgets.clear()

        # Populate with new files
        for file in tracked_files:
            file_widget = QListWidgetItem(f"{file.namespace}/{file.og_name}")
            self.file_widgets.addItem(file_widget)
            file_widget.setFlags(Qt.ItemFlag.ItemIsUserCheckable)
            file_widget.setCheckState(Qt.CheckState.Unchecked)

        # Update pagination info
        self._update_pagination_info()

    def _update_pagination_info(self):
        """Update pagination buttons and label."""
        total_pages = (self.total_items + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE
        if total_pages == 0:
            total_pages = 1

        page_display = self.current_page + 1
        self.page_info_label.setText(f"Page {page_display} of {total_pages}")

        # Enable/disable pagination buttons
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def _previous_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._load_page()

    def _next_page(self):
        """Go to next page."""
        total_pages = (self.total_items + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE
        if self.total_items == 0:
            total_pages = 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._load_page()

    def _on_search_changed(self, text: str):
        """Handle search query changes."""
        self.search_query = text.strip()
        self.current_page = 0  # Reset to first page when searching
        self._load_page()

    def _select_checkbox(self, clicked_item: QListWidgetItem, *args, **kwargs):
        if clicked_item.checkState() == Qt.CheckState.Checked:
            clicked_item.setCheckState(Qt.CheckState.Unchecked)
            clicked_item.setSelected(False)
        else:
            clicked_item.setCheckState(Qt.CheckState.Checked)
            clicked_item.setSelected(True)

    def _untracked_selected_checkboxes(self):
        selected_items = []
        for index in range(self.file_widgets.count()):
            item = self.file_widgets.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                selected_items.append(item)

        if not selected_items:
            logger.info("Nothing selected")
            return

        untrack_list: List[ChunkInfo] = []
        for item in selected_items:
            item: QListWidgetItem
            namespace, og_name = os.path.split(item.text())
            untrack_list.append(ChunkInfo(og_name=og_name, namespace=namespace))

        manager = ClientManager()
        client = manager.get_client()
        entity = client.get_entity(PeerChat(settings.CHAT_ID))
        for info in untrack_list:
            tracked_chunks = utils.get_file_tracked_chunks(info.og_name, info.namespace)
            for chunk in tracked_chunks:
                client.delete_messages(entity, message_ids=chunk.tele_id)
                logger.info(f"Deleted Telegram message of {info.og_name}")
                utils.untrack_chunks_in_db(info.og_name, info.namespace)
                logger.info(f"Untracked all chunks of {info.og_name}")

        # Reload page to reflect removed files
        self._load_page()

    def _download_selected_checkboxes(self):
        selected_items = []
        for index in range(self.file_widgets.count()):
            item = self.file_widgets.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                selected_items.append(item)

        if not selected_items:
            logger.info("Nothing selected")
            return

        download_list: List[ChunkInfo] = []
        for item in selected_items:
            item: QListWidgetItem
            namespace, og_name = os.path.split(item.text())
            download_list.append(ChunkInfo(og_name=og_name, namespace=namespace))

        dialog = ConfirmDownloadDialog(self)
        dialog_result = dialog.exec()

        if dialog_result == dialog.DialogCode.Accepted:
            manager = ClientManager()
            for info in download_list:
                tracked_chunks = utils.get_file_tracked_chunks(info.og_name, info.namespace)
                for chunk in tracked_chunks:
                    # Create progress dialog
                    progress_dialog = QProgressDialog(f"Downloading {chunk.chunk_name}", "Cancel", 0, chunk.size, self)
                    progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)

                    # Add progress dialog to manager
                    callback_manager = PySideProgressBarDialogCallback()
                    callback_manager.add_progress_dialog(progress_dialog, chunk.chunk_name)

                    manager.download_chunk(chunk, dialog.delete_after)

                logger.info(f"Complete download all chunks of {info.og_name}")
                # Join all chunks into 1 file
                utils.join_chunks_to_file(tracked_chunks)

                # Delete tracked chunks in db and telegram messages
                if dialog.delete_after and tracked_chunks:
                    utils.untrack_chunks_in_db(info.og_name, info.namespace)
                    logger.info(f"Untracked all chunks of {info.og_name}")

            if dialog.delete_after:
                # Reload page to reflect deleted files
                self._load_page()

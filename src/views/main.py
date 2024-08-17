# -*- coding: utf-8 -*-
import os
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QListWidget, QListWidgetItem, QProgressDialog, QVBoxLayout, QWidget

import constants
import utils
from client import ClientManager
from logger import get_logger
from settings import DownloadInfo
from utils.pyside import PySideProgressBarDialogCallback
from widgets.dialogs import ConfirmDownloadDialog, UploadNamespaceDialog

logger = get_logger(__name__)


class MainView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        tracked_files = utils.list_tracked_file()
        self.file_widgets = QListWidget(self)
        layout.addWidget(self.file_widgets)
        self.file_widgets.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.file_widgets.itemClicked.connect(self._select_checkbox)

        for file in tracked_files:
            file_widget = QListWidgetItem(f"{file.namespace}/{file.og_name}")
            self.file_widgets.addItem(file_widget)
            file_widget.setFlags(Qt.ItemFlag.ItemIsUserCheckable)
            file_widget.setCheckState(Qt.CheckState.Unchecked)

        self.setLayout(layout)

    def _select_checkbox(self, clicked_item: QListWidgetItem, *args, **kwargs):
        if clicked_item.checkState() == Qt.CheckState.Checked:
            clicked_item.setCheckState(Qt.CheckState.Unchecked)
            clicked_item.setSelected(False)
        else:
            clicked_item.setCheckState(Qt.CheckState.Checked)
            clicked_item.setSelected(True)

    def _download_selected_checkboxes(self):
        selected_items = []
        for index in range(self.file_widgets.count()):
            item = self.file_widgets.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                selected_items.append(item)

        if not selected_items:
            logger.info("Nothing selected")
            return

        download_list: List[DownloadInfo] = []
        for item in selected_items:
            item: QListWidgetItem
            namespace, og_name = os.path.split(item.text())
            download_list.append(DownloadInfo(og_name=og_name, namespace=namespace))

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
                for item in selected_items:
                    self.file_widgets.takeItem(self.file_widgets.row(item))

    def _select_files_to_upload(self):
        file_paths, extension_desc = QFileDialog.getOpenFileNames(self)
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
                        # Add progress dialog to manager
                        callback_manager = PySideProgressBarDialogCallback()
                        callback_manager.add_progress_dialog(progress_dialog, chunk.chunk_name)

                        # Upload chunk
                        manager.upload_chunk(dialog.namespace, chunk)

                    # Delete chunk file after upload
                    chunk_path = os.path.join(constants.LOCAL_TEMP_DIR, chunk.namespace, chunk.chunk_name)
                    os.remove(chunk_path)
                    logger.info(f"Removed {chunk.chunk_name} chunk")
                # Clean up temp zip of folder
                manager.cleanup_upload(path, False)

                # Add uploaded file to UI list
                og_name = os.path.basename(path)
                file_widget = QListWidgetItem(f"{dialog.namespace}/{og_name}")
                self.file_widgets.addItem(file_widget)
                file_widget.setFlags(Qt.ItemFlag.ItemIsUserCheckable)
                file_widget.setCheckState(Qt.CheckState.Unchecked)

    def _select_folder_to_upload(self):
        folder_path = QFileDialog.getExistingDirectory(self)
        dialog = UploadNamespaceDialog(self)
        dialog_result = dialog.exec()
        if dialog_result == dialog.DialogCode.Accepted:
            manager = ClientManager()
            file_chunks = utils.split_file_into_chunks(folder_path, dialog.namespace)
            for chunk in file_chunks:
                if utils.is_tracked_file_in_db(chunk):
                    logger.warn(f"Already tracked: {chunk.chunk_name}.")
                else:
                    # Create progress dialog
                    progress_dialog = QProgressDialog(f"Uploading {chunk.chunk_name}", "Cancel", 0, chunk.size, self)
                    progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)

                    # Add progress dialog to manager
                    callback_manager = PySideProgressBarDialogCallback()
                    callback_manager.add_progress_dialog(progress_dialog, chunk.chunk_name)

                    # Upload chunk
                    manager.upload_chunk(dialog.namespace, chunk)

            # Clean up temp zip of folder
            manager.cleanup_upload(chunk.get_local_path(), True)

            # Add uploaded folder zip to UI list
            og_name = os.path.basename(folder_path)
            file_widget = QListWidgetItem(f"{dialog.namespace}/{og_name}.zip")
            self.file_widgets.addItem(file_widget)
            file_widget.setFlags(Qt.ItemFlag.ItemIsUserCheckable)
            file_widget.setCheckState(Qt.CheckState.Unchecked)

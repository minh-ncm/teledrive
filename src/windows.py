# -*- coding: utf-8 -*-
from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QStackedLayout, QWidget

from client import ClientManager
from settings import settings
from views import FirstTimeView, MainView


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Teledrive")

        central_widget = QWidget()
        central_widget.setMinimumSize(300, 300)
        self.setCentralWidget(central_widget)

        layout = QStackedLayout()

        if not settings:
            Path("anon.session").unlink(True)
            first_time_view = FirstTimeView(self)
            layout.addWidget(first_time_view)
        else:
            manager = ClientManager()
            manager.create_client(settings.API_APP_ID, settings.API_APP_HASH)
        main_view = MainView(self)
        layout.addWidget(main_view)

        menu = self.menuBar()
        upload_menu = menu.addMenu("Upload")

        self.upload_file_action = QAction(text="Upload File", parent=self)
        upload_menu.addAction(self.upload_file_action)
        self.upload_file_action.triggered.connect(main_view._select_files_to_upload)

        self.upload_folder_action = QAction(text="Upload Folder", parent=self)
        upload_menu.addAction(self.upload_folder_action)
        self.upload_folder_action.triggered.connect(main_view._select_folder_to_upload)

        self.download_action = QAction(text="Download", parent=self)
        download_menu = menu.addAction(self.download_action)
        self.download_action.triggered.connect(main_view._download_selected_checkboxes)

        self.setWindowTitle("Teledrive")

        central_widget = QWidget()
        central_widget.setMinimumSize(300, 300)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

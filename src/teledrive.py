# -*- coding: utf-8 -*-
import sys

# Fix flood wait errors
import telethon
from PySide6.QtWidgets import QApplication

from init import init_db, init_tmp_dir
from windows import MainWindow

telethon.errors.rpc_errors_re += (("FLOOD_PREMIUM_WAIT_(\\d+)", telethon.errors.FloodWaitError),)


def main():
    init_db()
    init_tmp_dir()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()

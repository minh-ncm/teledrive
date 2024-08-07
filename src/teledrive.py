# -*- coding: utf-8 -*-
import sys

from PySide6.QtWidgets import QApplication

from init import init_db
from windows import MainWindow


def main():
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()

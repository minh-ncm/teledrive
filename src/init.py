# -*- coding: utf-8 -*-
import json
import os

from database import get_engine
from logger import get_logger
from models import FileModel

logger = get_logger(__name__)


def init_db():
    if not os.path.exists("database.db"):
        engine = get_engine()
        FileModel.metadata.create_all(engine)
        logger.info("Database initialized")


def init_configs():
    if not os.path.exists("config.json"):
        json.dump({}, open("config.json", "w+"))

    if not os.path.exists("upload.json"):
        json.dump([], open("upload.json", "w+"))

    if not os.path.exists("download.json"):
        json.dump([], open("download.json", "w+"))


def init_tmp_dir():
    if not os.path.exists("tmp"):
        os.mkdir("tmp")


def init_all():
    init_db()
    init_configs()
    init_tmp_dir()


if __name__ == "__main__":
    init_all()

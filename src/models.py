# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass
from typing import Optional

import sqlalchemy
from sqlalchemy.orm import DeclarativeBase, mapped_column

import constants


@dataclass
class FileChunk:
    og_name: str
    chunk_name: str
    namespace: str
    size: int
    tele_id: Optional[int] = 0

    def get_local_path(self) -> str:
        namespace = os.path.normpath(self.namespace[1:] if self.namespace.startswith("/") else self.namespace)
        chunk_output_dir = os.path.join(constants.LOCAL_TEMP_DIR, namespace)
        local_path = os.path.join(chunk_output_dir, self.chunk_name)
        return local_path


class Base(DeclarativeBase):
    pass


class FileModel(Base):
    __tablename__ = "files"

    id = mapped_column(sqlalchemy.Integer(), primary_key=True, autoincrement=True)
    og_name = mapped_column(sqlalchemy.String())
    chunk_name = mapped_column(sqlalchemy.String())
    namespace = mapped_column(sqlalchemy.String())
    tele_id = mapped_column(sqlalchemy.Integer())
    size = mapped_column(sqlalchemy.Integer())

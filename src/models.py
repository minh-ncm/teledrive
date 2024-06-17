from uuid import uuid4
from sqlalchemy.orm import DeclarativeBase, mapped_column
import sqlalchemy
from dataclasses import dataclass


@dataclass
class FileSchema:
    name: str
    path: str
    tele_id: str


@dataclass
class FileChunk:
    path: str
    size: int



class Base(DeclarativeBase):
    pass


class FileModel(Base):
    __tablename__ = "files"

    id = mapped_column(sqlalchemy.Integer(), primary_key=True, autoincrement=True)
    name = mapped_column(sqlalchemy.String())
    path = mapped_column(sqlalchemy.String())
    tele_id = mapped_column(sqlalchemy.String())
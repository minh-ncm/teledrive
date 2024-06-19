from uuid import uuid4
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, mapped_column
import sqlalchemy
from dataclasses import dataclass


@dataclass
class FileChunk:
    og_name: str
    chunk_name: str
    namespace: str
    size: int
    tele_id: Optional[int] = 0



class Base(DeclarativeBase):
    pass


class FileModel(Base):
    __tablename__ = "files"

    id = mapped_column(sqlalchemy.Integer(), primary_key=True, autoincrement=True)
    og_name = mapped_column(sqlalchemy.String())
    chunk_name = mapped_column(sqlalchemy.String())
    namespace = mapped_column(sqlalchemy.String())
    tele_id = mapped_column(sqlalchemy.Integer())
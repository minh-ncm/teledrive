# -*- coding: utf-8 -*-
import math
import os
import shutil
from pathlib import Path, PureWindowsPath
from typing import Generator, List

import sqlalchemy as sql
from PySide6.QtWidgets import QProgressDialog
from rich.progress import Progress
from sqlalchemy.orm import Session

import constants
from database import get_engine
from logger import get_logger
from models import FileChunk, FileModel

logger = get_logger(__name__)


def get_progress_callback(progress: Progress, label: str, total: int):
    task = progress.add_task(label, total=total)

    def progress_callback(sent_bytes, total):
        progress.update(task, completed=sent_bytes)

    return progress_callback


def get_pyside_progress_bar_callback(progress_dialog: QProgressDialog):
    def progress_callback(sent_bytes, total):
        progress_dialog.setValue(sent_bytes)

    return progress_callback


def is_tracked_file_in_db(file: FileChunk):
    # Convert window path to unix path
    if os.name == "nt":
        file.namespace = PureWindowsPath(file.namespace).as_posix()

    engine = get_engine()
    with Session(engine) as session:
        stmt = sql.select(FileModel).where(
            FileModel.chunk_name == file.chunk_name, FileModel.namespace == file.namespace
        )
        tracked_file = session.scalar(stmt)
        if tracked_file is None:
            return False
        return True


def track_upload_file_to_db(file: FileChunk):
    # Convert window path to unix path
    if os.name == "nt":
        file.namespace = PureWindowsPath(file.namespace).as_posix()

    engine = get_engine()
    with Session(engine) as session:
        new_file = FileModel(
            og_name=file.og_name,
            chunk_name=file.chunk_name,
            namespace=file.namespace,
            tele_id=file.tele_id,
            size=file.size,
        )
        session.add(new_file)
        session.commit()
        logger.info(f"Tracked: {file.chunk_name}")


def get_file_tracked_chunks(og_name: str, namespace: str) -> List[FileModel]:
    tracked_chunks = []
    engine = get_engine()
    with Session(engine) as session:
        stmt = (
            sql.select(FileModel)
            .where(FileModel.og_name == og_name, FileModel.namespace == namespace)
            .order_by(FileModel.chunk_name)
        )
        for file in session.scalars(stmt):
            tracked_chunks.append(file)

    return tracked_chunks


def create_local_path(path):
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Create local path: {path}")


def untrack_chunks_in_db(og_name: str, namespace: str):
    engine = get_engine()
    with Session(engine) as session:
        stmt = sql.delete(FileModel).where(FileModel.og_name == og_name, FileModel.namespace == namespace)
        session.execute(stmt)
        session.commit()


def create_zip_file(path: str, namespace: str):
    logger.info("Creating zip file")
    zip_dir_from = path
    zip_dir_name = os.path.split(path)[-1]

    zip_dir_to = os.path.join(constants.LOCAL_TEMP_DIR, namespace, zip_dir_name)
    if not os.path.isdir(zip_dir_from):
        raise ValueError(f"Source folder {zip_dir_from} does not exist or is not a directory.")
    shutil.make_archive(zip_dir_to, "zip", zip_dir_from)
    logger.info(f"Created zip file: {zip_dir_to}.zip")
    return f"{zip_dir_to}.zip"


def list_tracked_file(offset: int = 0, limit: int = 50, search_query: str = "") -> List[FileModel]:
    """
    List tracked files with pagination and optional search filtering.

    Args:
        offset (int): Number of records to skip (for pagination)
        limit (int): Number of records to return
        search_query (str): Optional search query to filter by og_name or namespace

    Returns:
        List[FileModel]: List of tracked files matching the criteria
    """
    engine = get_engine()
    with Session(engine) as session:
        stmt = sql.select(FileModel.og_name, FileModel.namespace).group_by(FileModel.namespace, FileModel.og_name)

        # Apply search filter if provided
        if search_query:
            stmt = stmt.where(
                sql.or_(
                    FileModel.og_name.ilike(f"%{search_query}%"),
                    FileModel.namespace.ilike(f"%{search_query}%"),
                )
            )

        # Apply pagination and ordering
        stmt = stmt.order_by(FileModel.namespace).offset(offset).limit(limit)

        result = []
        for og_name, namespace in session.execute(stmt).all():
            file = FileModel(og_name=og_name, namespace=namespace)
            result.append(file)
    return result


def get_tracked_file_count(search_query: str = "") -> int:
    """
    Get total count of tracked files (unique og_name + namespace combinations).

    Args:
        search_query (str): Optional search query to filter by og_name or namespace

    Returns:
        int: Total count of tracked files matching the criteria
    """
    engine = get_engine()
    with Session(engine) as session:
        stmt = sql.select(sql.func.count(sql.distinct(sql.func.concat(FileModel.og_name, FileModel.namespace))))

        # Apply search filter if provided
        if search_query:
            stmt = sql.select(sql.func.count()).select_from(
                sql.select(FileModel.og_name, FileModel.namespace)
                .distinct()
                .where(
                    sql.or_(
                        FileModel.og_name.ilike(f"%{search_query}%"),
                        FileModel.namespace.ilike(f"%{search_query}%"),
                    )
                )
                .subquery()
            )
        else:
            stmt = sql.select(sql.func.count()).select_from(
                sql.select(FileModel.og_name, FileModel.namespace).distinct().subquery()
            )

        count = session.scalar(stmt) or 0
    return count


def split_file_into_chunks(file_path: str, namespace: str) -> Generator[FileChunk, None, None]:
    """
    Split file into multiple chunks if larger than FILE_MAX_SIZE. Chunks will be saved in LOCAL_TEMP_DIR/namespace dir

    Args:
        file_path (str): path to the original file
        namespace (str): path from the root of LOCAL_TEMP_DIR to store the chunks

    Returns:
        Generator[FileChunk]: _description_

    Yields:
        Generator[FileChunk]: _description_
    """
    # Create zip file if the file is a folder
    if os.path.isdir(file_path):
        zip_path = create_zip_file(file_path, namespace)
        file_path = zip_path

    # Create namespace folder in local temp dir
    namespace = os.path.normpath(namespace[1:] if namespace.startswith("/") else namespace)
    chunk_output_dir = os.path.join(constants.LOCAL_TEMP_DIR, namespace)
    create_local_path(chunk_output_dir)

    # Open file and calculate total number of chunks
    f = open(file_path, "rb")
    file_size = os.path.getsize(file_path)
    file_name, file_ext = os.path.splitext(os.path.basename(file_path))
    total_chunks = math.ceil(file_size / constants.FILE_MAX_SIZE)
    remain_size = file_size
    logger.info(f"Spliting {file_name}{file_ext} into {total_chunks} chunks")

    for chunk_index in range(total_chunks):
        # Move cursor to the beginning of the next chunk
        chunk_cursor_index = chunk_index * constants.FILE_MAX_SIZE
        f.seek(chunk_cursor_index)
        chunk_name = f"{file_name}.{chunk_index:03d}{file_ext}"

        # Write the chunk to disk
        chunk_path = os.path.join(chunk_output_dir, chunk_name)
        chunk_size = min(constants.FILE_MAX_SIZE, remain_size)

        with open(chunk_path, "wb") as part_file:
            chunk = f.read(chunk_size)
            part_file.write(chunk)

        # Calculate remaining size for reading final chunk
        remain_size = file_size - (chunk_index + 1) * constants.FILE_MAX_SIZE

        logger.info(f"Created file chunk: {chunk_name}")
        yield FileChunk(namespace=namespace, size=chunk_size, og_name=file_name + file_ext, chunk_name=chunk_name)
    f.close()


def join_chunks_to_file(chunks: List[FileModel]):
    """
    Join all chunks to one file

    Args:
        chunks (List[FileModel]): _description_
    """
    # Exit if chunk only has one file or less
    if len(chunks) <= 1:
        logger.warning(f"No need to join {len(chunks)} chunk")
        return

    first_file = chunks[0]
    output_dir = os.path.join(constants.LOCAL_TEMP_DIR, first_file.namespace)
    joined_file_path = os.path.join(output_dir, first_file.og_name)
    with open(joined_file_path, "wb") as joined_file:
        for path in chunks:
            # Write each chunk to the joined file
            logger.info(f"Joining {path.chunk_name}")
            chunk_path = os.path.join(output_dir, path.chunk_name)
            with open(chunk_path, "rb") as f:
                joined_file.write(f.read())

            # Remove the chunk from disk after joining
            os.remove(chunk_path)
            logger.info(f"Removed {path.chunk_name}")

    if os.path.splitext(joined_file_path)[-1] == ".zip":
        shutil.unpack_archive(joined_file_path, output_dir, "zip")
        logger.info(f"Unziped {joined_file_path}")
        os.remove(joined_file_path)
        logger.info(f"Removed {joined_file_path}")

    logger.info(f"Joined all chunks for {first_file.og_name} in {output_dir}")

from pathlib import Path
from sqlalchemy.orm import Session
from rich.progress import Progress
from database import get_engine
from models import FileChunk, FileModel
from logger import get_logger


logger = get_logger(__name__)


def get_progress_callback(progress: Progress, label: str, total: int):
    task = progress.add_task(label, total=total)

    def progress_callback(sent_bytes, total):
        progress.update(task, completed=sent_bytes)

    return progress_callback


def is_tracked_file_in_db(file: FileChunk):
    engine = get_engine()
    with Session(engine) as session:
        tracked_file = session.query(FileModel).filter_by(og_name=file.og_name, path=file.path).first()
        if tracked_file is None:
            return False
        return True
    

def track_upload_file_to_db(file: FileChunk):
    engine = get_engine()
    with Session(engine) as session:
        new_file = FileModel(og_name=file.og_name, path=file.path, tele_id=file.tele_id)
        session.add(new_file)
        session.commit()
        logger.info(f"Tracked: {new_file}")


def create_local_path(path):
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Create local path: {path}")
from models import FileModel
from database import get_engine


def main():
    engine = get_engine()
    FileModel.metadata.create_all(engine)


if __name__ == "__main__":
    main()
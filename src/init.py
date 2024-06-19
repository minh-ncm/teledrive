from models import FileModel
from database import get_engine
import json


def main():
    engine = get_engine()
    FileModel.metadata.create_all(engine)
    json.dump([], open("upload.json", "w"))
    json.dump([], open("config.json", "w"))



if __name__ == "__main__":
    main()
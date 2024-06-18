from sqlalchemy import create_engine


def get_engine():
    engine = create_engine("sqlite:///tmp/database.db")
    return engine
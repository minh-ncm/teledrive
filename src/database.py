from sqlalchemy import create_engine


def get_engine():
    create_engine("sqlite:///database.db")
    pass
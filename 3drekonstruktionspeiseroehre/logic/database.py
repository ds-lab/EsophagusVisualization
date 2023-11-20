from sqlalchemy import create_engine
from logic import data_models

engine = create_engine("sqlite:///database.db", echo=True)


def create_db_and_tables():
    data_models.metadata_obj.create_all(engine)

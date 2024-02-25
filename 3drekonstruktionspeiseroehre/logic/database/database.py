import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from logic.database.data_declarative_models import Base


# ToDo: Pfad anpassen - Wo soll die lokale DB später gespeichert werden?
if os.environ.get('TESTING'):
    DATABASE_URL = 'sqlite:///test_database.db'
else:
    DATABASE_URL = 'postgresql+psycopg2://admin:123+qwe@127.0.0.1:5432/3drekonstruktion'


# echo in Produktion auf false setzen
engine_local = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine_local)


#def create_db_and_tables_local():
#    data_models.metadata_obj.create_all(engine_local)


def create_db_and_tables_local_declarative():
    Base.metadata.create_all(engine_local)


def create_db_and_tables_remote():  # für Postgresql-Server (oder Docker-Container...)
    pass


def get_db():
    db = Session()
    return db

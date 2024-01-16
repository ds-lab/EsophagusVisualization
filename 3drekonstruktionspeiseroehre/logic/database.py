import os
from sqlalchemy import create_engine
from logic import data_models
from sqlalchemy.orm import sessionmaker
from logic.data_declarative_models import Base

# ToDo: Pfad anpassen - Wo soll die lokale DB später gespeichert werden?
if os.environ.get('TESTING'):
    DATABASE_URL = 'sqlite:///test_database.db'
else:
    DATABASE_URL = 'sqlite:///database.db'

# echo in Produktion auf false setzen
engine_local = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine_local)


def create_db_and_tables_local():
    data_models.metadata_obj.create_all(engine_local)


def create_db_and_tables_local_declarative():
    Base.metadata.create_all(engine_local)


def create_db_and_tables_remote():  # für Postgresql-Server (oder Docker-Container...)
    pass


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

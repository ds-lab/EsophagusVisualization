import os

from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from logic.database.data_declarative_models import Base

# ToDo: Pfad anpassen - Wo soll die lokale DB später gespeichert werden?
if os.environ.get('TESTING'):
    DATABASE_URL = 'sqlite:///test_database.db'
else:
    DATABASE_URL = 'postgresql+psycopg2://admin:123+qwe@127.0.0.1:5432/3drekonstruktion'

# echo in Produktion auf false setzen
engine_local = create_engine(DATABASE_URL, pool_pre_ping=True, echo=True)
Session = sessionmaker(bind=engine_local)


# def create_db_and_tables_local():
#    data_models.metadata_obj.create_all(engine_local)


def create_db_and_tables_local_declarative():
    try:
        Base.metadata.create_all(engine_local)
    except OperationalError as e:
        show_error_msg()


def create_db_and_tables_remote():  # für Postgresql-Server (oder Docker-Container...)
    pass


def get_db():
    try:
        db = Session()
        return db
    except OperationalError as e:
        show_error_msg()
        return None


def show_error_msg():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("Error")
    msg.setText("An error occurred.")
    msg.setInformativeText("Please check the connection to the database.")
    msg.exec()

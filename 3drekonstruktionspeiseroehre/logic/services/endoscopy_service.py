from PyQt6.QtWidgets import QMessageBox
from flask import jsonify
from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import EndoscopyFile
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError


class EndoscopyFileService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_endoscopy_file(self, id: str):
        stmt = select(EndoscopyFile).where(EndoscopyFile.endoscopy_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def delete_endoscopy_file(self, id: str):
        stmt = delete(EndoscopyFile).where(EndoscopyFile.endoscopy_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_endoscopy_file(self, id: str, data: dict):
        stmt = update(EndoscopyFile).where(EndoscopyFile.endoscopy_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_endoscopy_file(self, data: dict):
        stmt = insert(EndoscopyFile).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def get_all_endoscopy_files(self) -> list[EndoscopyFile, None]:
        stmt = select(EndoscopyFile)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()


    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()


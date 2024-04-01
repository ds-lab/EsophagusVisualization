from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Endoflip, EndoflipFile



class EndoflipFileService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_endoflip_file(self, id: int):
        stmt = select(EndoflipFile).where(EndoflipFile.endoflip_file_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_endoflip_file_for_visit(self, visit_id: int) -> list[EndoflipFile, None]:
        stmt = select(EndoflipFile).where(EndoflipFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def delete_endoflip_file_for_visit(self, visit_id: int):
        stmt = delete(EndoflipFile).where(EndoflipFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_endoflip_file(self, id: int):
        stmt = delete(EndoflipFile).where(EndoflipFile.endoflip_file_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_endoflip_file(self, id: int, data: dict):
        stmt = update(EndoflipFile).where(EndoflipFile.endoflip_file_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_endoflip_file(self, data: dict):
        stmt = insert(EndoflipFile).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()

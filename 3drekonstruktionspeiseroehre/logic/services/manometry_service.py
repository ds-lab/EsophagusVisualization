from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Manometry, ManometryFile


class ManometryService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_manometry(self, id: int):
        stmt = select(Manometry).where(Manometry.manometry_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_manometry_for_visit(self, visit_id: int) -> list[Manometry, None]:
        stmt = select(Manometry).where(Manometry.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def delete_manometry_for_visit(self, visit_id: int):
        stmt = delete(Manometry).where(Manometry.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_manometry(self, id: int):
        stmt = delete(Manometry).where(Manometry.manometry_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_manometry(self, id: int, data: dict):
        stmt = update(Manometry).where(Manometry.manometry_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_manometry(self, data: dict):
        stmt = insert(Manometry).values(**data)
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


class ManometryFileService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_manometry_file(self, id: int):
        stmt = select(ManometryFile).where(ManometryFile.manometry_file_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_manometry_file_for_visit(self, visit_id: int) -> list[ManometryFile, None]:
        stmt = select(ManometryFile).where(ManometryFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def delete_manometry_file_for_visit(self, visit_id: int):
        stmt = delete(ManometryFile).where(ManometryFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_manometry_file(self, id: int):
        stmt = delete(ManometryFile).where(ManometryFile.manometry_file_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_manometry_file(self, id: int, data: dict):
        stmt = update(ManometryFile).where(ManometryFile.manometry_file_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_manometry_file(self, data: dict):
        stmt = insert(ManometryFile).values(**data)
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

from PyQt6 import QtGui
from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Reconstruction
from sqlalchemy.exc import OperationalError


class ReconstructionService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_reconstruction(self, id: int):
        stmt = select(Reconstruction).where(Reconstruction.reconstruction_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_reconstruction_for_visit(self, visit_id: int) -> list[Reconstruction, None]:
        stmt = select(Reconstruction).where(Reconstruction.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def delete_reconstruction(self, id: str):
        stmt = delete(Reconstruction).where(Reconstruction.reconstruction_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_reconstruction_for_visit(self, visit_id: str):
        stmt = delete(Reconstruction).where(Reconstruction.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_reconstruction(self, id: str, data: dict):
        stmt = update(Reconstruction).where(Reconstruction.reconstruction_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_reconstruction(self, data: dict):
        stmt = insert(Reconstruction).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def get_all_reconstructions(self) -> list[Reconstruction, None]:
        stmt = select(Reconstruction)
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

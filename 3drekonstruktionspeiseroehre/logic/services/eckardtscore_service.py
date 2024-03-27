from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Visit, Patient, EckardtScore


class EckardtscoreService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_eckardtscore(self, id: int):
        stmt = select(EckardtScore).where(EckardtScore.eckardt_id == id)
        try:
            result = self.db.execute(stmt).first()
            return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_eckardtscores_for_visit(self, visit_id: int) -> list[EckardtScore, None]:
        stmt = select(EckardtScore).where(EckardtScore.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()

    def delete_eckardtscore_for_visit(self, visit_id: int):
        stmt = delete(EckardtScore).where(EckardtScore.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_eckardtscore(self, id: int):
        stmt = delete(Visit).where(EckardtScore.eckardt_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_eckardtscore(self, id: int, data: dict):
        stmt = update(EckardtScore).where(EckardtScore.eckardt_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_eckardtscore(self, data: dict):
        stmt = insert(EckardtScore).values(**data)
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












from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import PreviousTherapy, Patient


class PreviousTherapyService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_previous_therapy(self, id: int):
        stmt = select(PreviousTherapy).where(PreviousTherapy.previous_therapy_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_prev_therapies_for_patient(self, patient_id: str) -> list[PreviousTherapy, None]:
        stmt = select(PreviousTherapy).join(Patient).where(Patient.patient_id == patient_id)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()

    def delete_previous_therapy(self, id: int):
        stmt = delete(PreviousTherapy).where(PreviousTherapy.previous_therapy_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_previous_therapy(self, id: str, data: dict):
        stmt = update(PreviousTherapy).where(PreviousTherapy.previous_therapy_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_previous_therapy(self, data: dict):
        stmt = insert(PreviousTherapy).values(**data)
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


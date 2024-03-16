from PyQt6.QtWidgets import QMessageBox
from flask import jsonify
from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Patient
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError


class PatientService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_patient_by_id(self, id: str):
        stmt = select(Patient).where(Patient.patient_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def delete_patient(self, id: str):
        stmt = delete(Patient).where(Patient.patient_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_patient(self, id: str, data: dict):
        stmt = update(Patient).where(Patient.patient_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_patient(self, data: dict):
        stmt = insert(Patient).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def get_all_patients(self) -> list[Patient, None]:
        stmt = select(Patient)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()

    def get_patients_by_birthyear(self, birth_year: int):
        stmt = select(Patient).where(Patient.birth_year == birth_year)
        try:
            result = self.db.execute(stmt).all()
            if result:
                return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()

    def get_patients_by_gender(self):
        pass

    def get_patients_by_ethnicity(self):
        pass

    def get_patients_by_yearfirstdiagnosis(self):
        pass

    def get_patients_by_yearfirstsymptoms(self):
        pass

    def get_patients_by_center(self):
        pass


    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()


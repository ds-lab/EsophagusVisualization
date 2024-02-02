from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.data_declarative_models import Patient


class PatientService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_patient(self, id: str):
        stmt = select(Patient).where(Patient.patient_id == id)
        try:
            result = self.db.execute(stmt).first()[0]
            return result
        except Exception as e:
            raise e

    def get_all_patients(self):
        stmt = select(Patient)
        try:
            result = self.db.execute(stmt).all()
            return result
        except Exception as e:
            raise e

    def delete_patient(self, id: str):
        stmt = delete(Patient).where(Patient.patient_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            raise e

    def update_patient(self, id: str, data: dict):
        stmt = update(Patient).where(Patient.patient_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            raise e

    def create_patient(self, data: dict):
        stmt = insert(Patient).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except Exception as e:
            self.db.rollback()
            raise e

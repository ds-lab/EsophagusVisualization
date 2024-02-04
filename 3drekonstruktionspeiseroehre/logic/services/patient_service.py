from flask import jsonify
from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.data_declarative_models import Patient
from sqlalchemy import inspect


class PatientService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_patient(self, id: str):
        stmt = select(Patient).where(Patient.patient_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
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

    def get_all_patients(self):
        rows = []
        stmt = select(Patient)
        try:
            result = self.db.execute(stmt)
            if result:
                for row in result:
                    rows.append((row[0].patient_id, row[0].ancestry, row[0].birth_year, row[0].previous_therapies))
                    return rows
        except Exception as e:
            raise e

    def get_all_patients2(self):
        patients = Patient.query.all()
        patientsArr = []
        for patient in patients:
            patientsArr.append(patient.toDict())
        print(jsonify(patientsArr))
        return jsonify(patientsArr)

from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import PreviousTherapy


class PreviousTherapyService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_previous_therapy(self, id: int):
        stmt = select(PreviousTherapy).where(PreviousTherapy.previous_therapy_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except Exception as e:
            raise e

    def get_prev_therapies_for_patient(self, patient_id: int) -> list[PreviousTherapy, None]:
        stmt = select(PreviousTherapy).where(patient_id == patient_id)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except Exception as e:
            raise e

    def delete_previous_therapy(self, id: int):
        stmt = delete(PreviousTherapy).where(PreviousTherapy.previous_therapy_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            raise e

    def update_previous_therapy(self, id: str, data: dict):
        stmt = update(PreviousTherapy).where(PreviousTherapy.previous_therapy_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            raise e

    def create_previous_therapy(self, data: dict):
        stmt = insert(PreviousTherapy).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except Exception as e:
            self.db.rollback()
            raise e

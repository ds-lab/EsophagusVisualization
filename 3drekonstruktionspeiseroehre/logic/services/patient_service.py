from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.data_declarative_models import Patient


def get_patient(id: str, db_session: Session):
    stmt = select(Patient).where(Patient.patient_id == id)
    return db_session.execute(stmt).first()


def delete_patient(id: str, db_session: Session):
    stmt = delete(Patient).where(Patient.patient_id == id)
    result = db_session.execute(stmt)
    db_session.commit()
    return bool(result.rowcount)


def update_patient(id: str, data: dict, db_session: Session):
    stmt = update(Patient).where(Patient.patient_id == id).values(**data)
    try:
        result = db_session.execute(stmt)
        db_session.commit()
        return result.rowcount
    except Exception as e:
        db_session.rollback()
        raise e


def create_patient(data: dict, db_session: Session):
    stmt = insert(Patient).values(**data)
    try:
        result = db_session.execute(stmt)
        db_session.commit()
        return result.rowcount  # Return the number of rows affected
    except Exception as e:
        db_session.rollback()
        raise e

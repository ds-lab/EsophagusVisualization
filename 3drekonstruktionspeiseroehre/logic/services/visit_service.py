from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.data_declarative_models import Visit


def get_visit(id: int, db_session: Session):
    stmt = select(Visit).where(Visit.visit_id == id)
    try:
        result = db_session.execute(stmt).first()
        return result
    except Exception as e:
        raise e


def delete_visit(id: int, db_session: Session):
    stmt = delete(Visit).where(Visit.visit_id == id)
    try:
        result = db_session.execute(stmt)
        db_session.commit()
        return result.rowcount
    except Exception as e:
        db_session.rollback()
        raise e


def update_visit(id: int, data: dict, db_session: Session):
    stmt = update(Visit).where(Visit.visit_id == id).values(**data)
    try:
        result = db_session.execute(stmt)
        db_session.commit()
        return result.rowcount
    except Exception as e:
        db_session.rollback()
        raise e


def create_visit(data: dict, db_session: Session):
    stmt = insert(Visit).values(**data)
    try:
        result = db_session.execute(stmt)
        db_session.commit()
        return result.rowcount  # Return the number of rows affected
    except Exception as e:
        db_session.rollback()
        raise e

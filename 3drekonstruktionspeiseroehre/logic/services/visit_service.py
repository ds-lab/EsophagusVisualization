from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Visit

class VisitService:
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_visit(self, id: int):
        stmt = select(Visit).where(Visit.visit_id == id)
        try:
            result = self.db.execute(stmt).first()
            return result
        except Exception as e:
            raise e
        
    def delete_visit(self, id: int):
        stmt = delete(Visit).where(Visit.visit_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            raise e
        
    def update_visit(self, id: int, data: dict):
        stmt = update(Visit).where(Visit.visit_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            raise e
        
    def create_visit(self, data: dict):
        stmt = insert(Visit).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except Exception as e:
            self.db.rollback()
            raise e







    
    






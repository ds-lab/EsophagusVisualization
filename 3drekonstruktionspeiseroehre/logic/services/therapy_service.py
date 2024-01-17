from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.data_declarative_models import Therapy


class therapyService:
    
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_therapy(self, id: int):
        stmt = select(Therapy).where(Therapy.therapy_id == id)
        try:
            result = self.db.execute(stmt)
            return result
        except Exception as e:
            raise e
        
    def delete_therapy(self, id: int):
        pass

    def update_therapy(self, id: int):
        pass







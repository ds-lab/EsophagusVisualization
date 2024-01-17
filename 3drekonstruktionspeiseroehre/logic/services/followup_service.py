from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.data_declarative_models import Followup


class FollowupService:
    
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_followup(self, id: int):
        stmt = select(Followup).where(Followup.folloup_id == id)
        try:
            result = self.db.execute(stmt)
            return result
        except Exception as e:
            raise e

    def delete_followup(self, id: int):
        pass

    def update_followup(self, id: int):
        pass

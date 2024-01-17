from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.data_declarative_models import Metric


class MetricService:
    
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_metric(self, id: int):
        stmt = select(Metric).where(Metric.metric_id == id)
        try:
            result = self.db_session.execute(stmt)
            return result
        except Exception as e:
            raise e

    def delete_metric(self, id: int):
        pass

    def update_metric(self, id: int):
        pass

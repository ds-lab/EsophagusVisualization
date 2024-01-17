from sqlalchemy import select, delete, update, insert
from sqlalchemy.orm import Session
from logic.data_declarative_models import VisualizationData


class VisualizationDataService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_visualization_data(self, id: int):
        stmt = select(VisualizationData).where(
            VisualizationData.visualization_id == id)
        try:
            result = self.db.execute(stmt)
            return result
        except Exception as e:
            raise e

    def delete_visualization_data(self, id: int):
        pass

    def update_visualization_data(self, id: int):
        pass

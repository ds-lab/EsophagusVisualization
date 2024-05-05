from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert, and_
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Patient, PreviousTherapy, Visit, EckardtScore, Gerd, Medication, BotoxInjection, PneumaticDilatation, LHM, POEM, Complications, Manometry, ManometryFile, BariumSwallow, BariumSwallowFile, Endoscopy, EndoscopyFile, Endoflip, EndoflipFile, EndoflipImage, Endosonography, EndosonographyFile, Metric, VisualizationData

class VisitService:
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_visit(self, id: int):
        stmt = select(Visit).where(Visit.visit_id == id)
        try:
            result = self.db.execute(stmt).first()
            return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_visits_for_patient(self, patient_id: str) -> list[Visit, None]:
        stmt = select(Visit).where(Visit.patient_id == patient_id)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()
        
    def delete_visit(self, id: int):
        stmt = delete(Visit).where(Visit.visit_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()
        
    def update_visit(self, id: int, data: dict):
        stmt = update(Visit).where(Visit.visit_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()
        
    def create_visit(self, data: dict):
        stmt = insert(Visit).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def get_all_data_for_visit(self, visit_id: int):
        try:
            patients = Patient.__table__
            visits = Visit.__table__
            previous_therapies = PreviousTherapy.__table__

            stmt = (
                select(patients, visits, previous_therapies)
                .select_from(visits.outerjoin(patients, visits.c.patient_id == patients.c.patient_id).
                             outerjoin(previous_therapies, patients.c.patient_id == previous_therapies.c.patient_id))
                .where(visits.c.visit_id == visit_id)
            )

            result = self.db.execute(stmt).all()
            if result:
                print(result)
                return result
            else:
                return None

        except OperationalError as e:
            self.show_error_msg()

    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()




    
    






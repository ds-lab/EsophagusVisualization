from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert, and_
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Patient, PreviousTherapy, Visit, EckardtScore, Gerd, Medication, \
    BotoxInjection, PneumaticDilatation, LHM, POEM, Complications, Manometry, ManometryFile, BariumSwallow, \
    BariumSwallowFile, Endoscopy, EndoscopyFile, Endoflip, EndoflipFile, EndoflipImage, Endosonography, \
    EndosonographyFile, Metric, VisualizationData


class GetExportData:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_all_data_for_visit(self, visit_id: int):
        try:
            patients = Patient.__table__
            visits = Visit.__table__
            previous_therapies = PreviousTherapy.__table__
            eckardt_scores = EckardtScore.__table__
            gerd_scores = Gerd.__table__
            medications = Medication.__table__
            botox_injections = BotoxInjection.__table__
            pneumatic_dilatations = PneumaticDilatation.__table__
            lhms = LHM.__table__
            poems = POEM.__table__
            complications = Complications.__table__
            manometries = Manometry.__table__
            barium_swallows = BariumSwallow.__table__
            endoscopies = Endoscopy.__table__
            endoflips = Endoflip.__table__
            endosonographies = Endosonography.__table__

            stmt = (
                select(patients, visits, previous_therapies, eckardt_scores, gerd_scores, medications,
                       botox_injections, pneumatic_dilatations, lhms, poems, complications, manometries,
                       barium_swallows, endoscopies, endoflips, endosonographies)
                .select_from(visits.outerjoin(patients, visits.c.patient_id == patients.c.patient_id)
                             .outerjoin(previous_therapies, visits.c.visit_id == previous_therapies.c.visit_id)
                             .outerjoin(eckardt_scores, visits.c.visit_id == eckardt_scores.c.visit_id)
                             .outerjoin(gerd_scores, visits.c.visit_id == gerd_scores.c.visit_id)
                             .outerjoin(medications, visits.c.visit_id == medications.c.visit_id)
                             .outerjoin(botox_injections, visits.c.visit_id == botox_injections.c.visit_id)
                             .outerjoin(pneumatic_dilatations, visits.c.visit_id == pneumatic_dilatations.c.visit_id)
                             .outerjoin(lhms, visits.c.visit_id == lhms.c.visit_id)
                             .outerjoin(poems, visits.c.visit_id == poems.c.visit_id)
                             .outerjoin(complications, visits.c.visit_id == complications.c.visit_id)
                             .outerjoin(manometries, visits.c.visit_id == manometries.c.visit_id)
                             .outerjoin(barium_swallows, visits.c.visit_id == barium_swallows.c.visit_id)
                             .outerjoin(endoscopies, visits.c.visit_id == endoscopies.c.visit_id)
                             .outerjoin(endoflips, visits.c.visit_id == endoflips.c.visit_id)
                             .outerjoin(endosonographies, visits.c.visit_id == endosonographies.c.visit_id))
                .where(visits.c.visit_id == visit_id)
            )

            result = self.db.execute(stmt).all()
            if result:
                return result
            else:
                return None

        except OperationalError as e:
            self.show_error_msg()

    def get_all_data(self):
        try:
            patients = Patient.__table__
            visits = Visit.__table__
            previous_therapies = PreviousTherapy.__table__
            eckardt_scores = EckardtScore.__table__
            gerd_scores = Gerd.__table__
            medications = Medication.__table__
            botox_injections = BotoxInjection.__table__
            pneumatic_dilatations = PneumaticDilatation.__table__
            lhms = LHM.__table__
            poems = POEM.__table__
            complications = Complications.__table__
            manometries = Manometry.__table__
            barium_swallows = BariumSwallow.__table__
            endoscopies = Endoscopy.__table__
            endoflips = Endoflip.__table__
            endosonographies = Endosonography.__table__

            stmt = (
                select(patients, visits, previous_therapies, eckardt_scores, gerd_scores, medications,
                       botox_injections, pneumatic_dilatations, lhms, poems, complications, manometries,
                       barium_swallows, endoscopies, endoflips, endosonographies)
                .select_from(visits.outerjoin(patients, visits.c.patient_id == patients.c.patient_id)
                             .outerjoin(previous_therapies, visits.c.visit_id == previous_therapies.c.visit_id)
                             .outerjoin(eckardt_scores, visits.c.visit_id == eckardt_scores.c.visit_id)
                             .outerjoin(gerd_scores, visits.c.visit_id == gerd_scores.c.visit_id)
                             .outerjoin(medications, visits.c.visit_id == medications.c.visit_id)
                             .outerjoin(botox_injections, visits.c.visit_id == botox_injections.c.visit_id)
                             .outerjoin(pneumatic_dilatations,
                                        visits.c.visit_id == pneumatic_dilatations.c.visit_id)
                             .outerjoin(lhms, visits.c.visit_id == lhms.c.visit_id)
                             .outerjoin(poems, visits.c.visit_id == poems.c.visit_id)
                             .outerjoin(complications, visits.c.visit_id == complications.c.visit_id)
                             .outerjoin(manometries, visits.c.visit_id == manometries.c.visit_id)
                             .outerjoin(barium_swallows, visits.c.visit_id == barium_swallows.c.visit_id)
                             .outerjoin(endoscopies, visits.c.visit_id == endoscopies.c.visit_id)
                             .outerjoin(endoflips, visits.c.visit_id == endoflips.c.visit_id)
                             .outerjoin(endosonographies, visits.c.visit_id == endosonographies.c.visit_id))
            )

            result = self.db.execute(stmt).all()
            if result:
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

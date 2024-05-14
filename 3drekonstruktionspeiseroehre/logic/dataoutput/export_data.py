from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert, and_
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Patient, PreviousTherapy, Visit, EckardtScore, Gerd, Medication, \
    BotoxInjection, PneumaticDilatation, LHM, POEM, Complications, Manometry, BariumSwallow, \
    Endoscopy, Endoflip, Endosonography
import csv


class ExportData:

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

            stmt = (
                select(patients, visits, previous_therapies, eckardt_scores, gerd_scores, medications,
                       botox_injections, pneumatic_dilatations, lhms, poems, complications, manometries,
                       barium_swallows, endoscopies, endoflips, endosonographies)
                .select_from(visits.outerjoin(patients, visits.c.patient_id == patients.c.patient_id)
                             .outerjoin(previous_therapies, patients.c.patient_id == previous_therapies.c.patient_id)
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
                             .outerjoin(endoflips, visits.c.visit_id == endoflips.c.visit_id))
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

            stmt = (
                select(patients, visits, previous_therapies, eckardt_scores, gerd_scores, medications,
                       botox_injections, pneumatic_dilatations, lhms, poems, complications, manometries,
                       barium_swallows, endoscopies, endoflips, endosonographies)
                .select_from(patients.outerjoin(visits, visits.c.patient_id == patients.c.patient_id)
                             .outerjoin(previous_therapies, patients.c.patient_id == previous_therapies.c.patient_id)
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
                             .outerjoin(endoflips, visits.c.visit_id == endoflips.c.visit_id))
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

    @staticmethod
    def export_csv(data, csv_file_path):
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            headers = [
                "patients.patient_id", "patients.gender", "patients.ethnicity", "patients.birth_year",
                "patients.year_first_diagnosis", "patients.year_first_symptoms", "patients.center",
                "visits.visit_id", "visits.patient_id", "visits.year_of_visit", "visits.visit_type",
                "visits.therapy_type", "visits.months_after_therapy",
                "previous_therapies.previous_therapy_id", "previous_therapies.patient_id",
                "previous_therapies.therapy", "previous_therapies.year", "previous_therapies.center",
                "eckardt_scores.eckardt_id", "eckardt_scores.visit_id",
                "eckardt_scores.dysphagia", "eckardt_scores.retrosternal_pain",
                "eckardt_scores.regurgitation", "eckardt_scores.weightloss", "eckardt_scores.total_score",
                "gerd_scores.gerd_id", "gerd_scores.visit_id",
                "gerd_scores.grade", "gerd_scores.heart_burn", "gerd_scores.ppi_use", "gerd_scores.acid_exposure_time",
                "medications.medication_id", "medications.visit_id", "medications.medication_use",
                "medications.medication_name", "medications.medication_dose",
                "botox_injections.botox_id", "botox_injections.visit_id", "botox_injections.botox_units",
                "botox_injections.botox_height",
                "pneumatic_dilatations.pneumatic_dilatation_id", "pneumatic_dilatations.pneumatic_visit_id",
                "pneumatic_dilatations.balloon_volume", "pneumatic_dilatations.quantity",
                "lhms.lhm_id", "lhms.visit_id",
                "lhms.op_duration", "lhms.length_myotomy", "lhms.fundoplicatio", "lhms.type_fundoplicatio",
                "poems.poem_id", "poems.visit_id", "poems.procedure_duration", "poems.height_mucosal_incision",
                "poems.length_mucosal_incision", "poems.length_submuscosal_tunnel", "poems.localization_myotomy",
                "poems.length_tubular_myotomy", "poems.length_gastric_myotomy",
                "complications.complication_id", "complications.visit_id",
                "complications.bleeding", "complications.perforation", "complications.capnoperitoneum",
                "complications.mucosal_tears", "complications.pneumothorax", "complications.pneumomediastinum",
                "complications.other_complication",
                "manometries.manometry_id", "manometries.visit_id", "manometries.catheder_type",
                "manometries.patient_position", "manometries.resting_pressure", "manometries.ipr4", "manometries.dci",
                "manometries.dl", "manometries.ues_upper_boundary", "manometries.ues_lower_boundary",
                "manometries.les_upper_boundary", "manometries.les_lower_boundary", "manometries.les_length",
                "barium_swallows.tbe_id", "barium_swallows.visit_id", "barium_swallows.type_contrast_medium",
                "barium_swallows.amount_contrast_medium",
                "barium_swallows.height_contrast_medium_1min", "barium_swallows.height_contrast_medium_2min",
                "barium_swallows.height_contrast_medium_5min", "barium_swallows.width_contrast_medium_1min",
                "barium_swallows.width_contrast_medium_2min", "barium_swallows.width_contrast_medium_5min",
                "endoscopies.egd_id", "endoscopies.visit_id", "endoscopies.position_les",
                "endoflips.endoflip_id", "endoflips.visit_id", "endoflips.csa_before",
                "endoflips.di_before", "endoflips.dmin_before", "endoflips.ibp_before", "endoflips.csa_during",
                "endoflips.di_during", "endoflips.dmin_during", "endoflips.ibp_during", "endoflips.csa_after",
                "endoflips.di_after", "endoflips.dmin_after", "endoflips.ibp_after"
            ]

            writer.writerow(headers)

            writer.writerows(data)

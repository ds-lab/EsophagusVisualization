from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert, and_
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Patient, PreviousTherapy, Visit, EckardtScore, Gerd, Medication, \
    BotoxInjection, PneumaticDilatation, LHM, POEM, Complications, Manometry, BariumSwallow, \
    Endoscopy, Endoflip
import csv


class ExportData:

    def __init__(self, db_session: Session):
        self.db = db_session

    # def get_all_data(self):
    #     try:
    #         patients = Patient.__table__
    #         visits = Visit.__table__
    #         previous_therapies = PreviousTherapy.__table__
    #         eckardt_scores = EckardtScore.__table__
    #         gerd_scores = Gerd.__table__
    #         medications = Medication.__table__
    #         botox_injections = BotoxInjection.__table__
    #         pneumatic_dilatations = PneumaticDilatation.__table__
    #         lhms = LHM.__table__
    #         poems = POEM.__table__
    #         complications = Complications.__table__
    #         manometries = Manometry.__table__
    #         barium_swallows = BariumSwallow.__table__
    #         endoscopies = Endoscopy.__table__
    #         endoflips = Endoflip.__table__
    #
    #         stmt = (
    #             select(patients, visits, previous_therapies, eckardt_scores, gerd_scores, medications,
    #                    botox_injections, pneumatic_dilatations, lhms, poems, complications, manometries,
    #                    barium_swallows, endoscopies, endoflips)
    #             .select_from(patients.outerjoin(visits, visits.c.patient_id == patients.c.patient_id)
    #                          .outerjoin(previous_therapies, patients.c.patient_id == previous_therapies.c.patient_id)
    #                          .outerjoin(eckardt_scores, visits.c.visit_id == eckardt_scores.c.visit_id)
    #                          .outerjoin(gerd_scores, visits.c.visit_id == gerd_scores.c.visit_id)
    #                          .outerjoin(medications, visits.c.visit_id == medications.c.visit_id)
    #                          .outerjoin(botox_injections, visits.c.visit_id == botox_injections.c.visit_id)
    #                          .outerjoin(pneumatic_dilatations,
    #                                     visits.c.visit_id == pneumatic_dilatations.c.visit_id)
    #                          .outerjoin(lhms, visits.c.visit_id == lhms.c.visit_id)
    #                          .outerjoin(poems, visits.c.visit_id == poems.c.visit_id)
    #                          .outerjoin(complications, visits.c.visit_id == complications.c.visit_id)
    #                          .outerjoin(manometries, visits.c.visit_id == manometries.c.visit_id)
    #                          .outerjoin(barium_swallows, visits.c.visit_id == barium_swallows.c.visit_id)
    #                          .outerjoin(endoscopies, visits.c.visit_id == endoscopies.c.visit_id)
    #                          .outerjoin(endoflips, visits.c.visit_id == endoflips.c.visit_id))
    #         )
    #
    #         result = self.db.execute(stmt).all()
    #         if result:
    #             return result
    #         else:
    #             return None
    #
    #     except OperationalError as e:
    #         self.show_error_msg()

    def get_data(self, selected_tables):
        try:
            tables = {
                "patients": Patient.__table__,
                "visits": Visit.__table__,
                "previous_therapies": PreviousTherapy.__table__,
                "eckardt_scores": EckardtScore.__table__,
                "gerd_scores": Gerd.__table__,
                "medications": Medication.__table__,
                "botox_injections": BotoxInjection.__table__,
                "pneumatic_dilations": PneumaticDilatation.__table__,
                "lhms": LHM.__table__,
                "poems": POEM.__table__,
                "complications": Complications.__table__,
                "manometries": Manometry.__table__,
                "barium_swallows": BariumSwallow.__table__,
                "endoscopies": Endoscopy.__table__,
                "endoflips": Endoflip.__table__,
            }

            selected_tables = selected_tables

            selected_table_objs = [tables[table] for table in selected_tables]

            base_stmt = select(*selected_table_objs)
            join_stmt = tables["patients"].outerjoin(tables["visits"], tables["visits"].c.patient_id == tables[
                "patients"].c.patient_id)

            if "previous_therapies" in selected_tables:
                join_stmt = join_stmt.outerjoin(tables["previous_therapies"],
                                                tables["patients"].c.patient_id == tables[
                                                    "previous_therapies"].c.patient_id)

            for table in selected_tables:
                if table not in ["patients", "visits", "previous_therapies"]:
                    join_stmt = join_stmt.outerjoin(tables[table],
                                                    tables[table].c.visit_id == tables["visits"].c.visit_id)

            stmt = base_stmt.select_from(join_stmt)

            result = self.db.execute(stmt).all()
            return result if result else None

        except OperationalError as e:
            self.show_error_msg()
            return None

    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()

    @staticmethod
    def export_csv(data, selected_tables, csv_file_path):
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            headers_dict = {
                "patients": ["patient_id", "gender", "ethnicity", "birth_year", "year_first_diagnosis",
                             "year_first_symptoms", "center"],
                "visits": ["visit_id", "patient_id", "year_of_visit", "visit_type", "therapy_type",
                           "months_after_therapy"],
                "previous_therapies": ["previous_therapy_id", "patient_id", "therapy", "year", "center"],
                "eckardt_scores": ["eckardt_id", "visit_id", "dysphagia", "retrosternal_pain", "regurgitation",
                                   "weightloss", "total_score"],
                "gerd_scores": ["gerd_id", "visit_id", "grade", "heart_burn", "ppi_use", "acid_exposure_time"],
                "medications": ["medication_id", "visit_id", "medication_use", "medication_name", "medication_dose"],
                "botox_injections": ["botox_id", "visit_id", "botox_units", "botox_height"],
                "pneumatic_dilations": ["pneumatic_dilatation_id", "visit_id", "balloon_volume", "quantity"],
                "lhms": ["lhm_id", "visit_id", "op_duration", "length_myotomy", "fundoplicatio", "type_fundoplicatio"],
                "poems": ["poem_id", "visit_id", "procedure_duration", "height_mucosal_incision",
                          "length_mucosal_incision", "length_submuscosal_tunnel", "localization_myotomy",
                          "length_tubular_myotomy", "length_gastric_myotomy"],
                "complications": ["complication_id", "visit_id", "bleeding", "perforation", "capnoperitoneum",
                                  "mucosal_tears", "pneumothorax", "pneumomediastinum", "other_complication"],
                "manometries": ["manometry_id", "visit_id", "catheder_type", "patient_position", "resting_pressure",
                                "ipr4", "dci", "dl", "ues_upper_boundary", "ues_lower_boundary", "les_upper_boundary",
                                "les_lower_boundary", "les_length"],
                "barium_swallows": ["tbe_id", "visit_id", "type_contrast_medium", "amount_contrast_medium",
                                    "height_contrast_medium_1min", "height_contrast_medium_2min",
                                    "height_contrast_medium_5min", "width_contrast_medium_1min",
                                    "width_contrast_medium_2min", "width_contrast_medium_5min"],
                "endoscopies": ["egd_id", "visit_id", "position_les"],
                "endoflips": ["endoflip_id", "visit_id", "csa_before", "di_before", "dmin_before", "ibp_before",
                              "csa_during", "di_during", "dmin_during", "ibp_during", "csa_after", "di_after",
                              "dmin_after", "ibp_after"]
            }

            headers = [f"{table}.{col}" for table in selected_tables for col in headers_dict[table]]
            writer.writerow(headers)

            writer.writerows(data)

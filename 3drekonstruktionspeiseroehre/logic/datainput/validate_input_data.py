from datetime import datetime

from PyQt6.QtWidgets import QMessageBox


class DataValidation:
    @staticmethod
    def validate_patient(patient_id_field, gender_dropdown, ethnicity_dropdown, birthyear_calendar, firstdiagnosis_calendar, firstsymptoms_calendar, center_text):
        if (
                len(patient_id_field) > 0
                and gender_dropdown != "---"
                and ethnicity_dropdown != "---"
                and 1900 < birthyear_calendar <= datetime.now().year
                and 1900 < firstdiagnosis_calendar <= datetime.now().year
                and 1900 < firstsymptoms_calendar <= datetime.now().year
                and center_text != ""
        ):
            return True
        return False

    @staticmethod
    def validate_visit(year_of_visit_calendar, visit_type_dropdown, therapy_type_dropdown, months_after_therapy_spin):
        if (
                1900 < year_of_visit_calendar <= datetime.now().year
                and visit_type_dropdown != "---"
                and (visit_type_dropdown != "Therapy" or therapy_type_dropdown != "---")
                and (therapy_type_dropdown == "---" or visit_type_dropdown == "Therapy")
                and months_after_therapy_spin != -1
        ):
            return True
        return False

    @staticmethod
    def validate_eckardtscore(eckardt_dysphagia_dropdown, eckardt_retro_pain_dropdown, eckardt_regurgitation_dropdown, eckardt_weightloss_dropdown, eckardt_totalscore_dropdown):
        if (
                eckardt_dysphagia_dropdown != '---' and
                eckardt_retro_pain_dropdown != '---' and
                eckardt_regurgitation_dropdown != '---' and
                eckardt_weightloss_dropdown != '---' and
                eckardt_totalscore_dropdown != '---'
        ):
            return True
        return False

    @staticmethod
    def validate_manometry(manometry_dict):
        null_values = []
        for key, value in manometry_dict.items():
            if value == -1 or value == "---":
                null_values.append(key)
                manometry_dict[key] = None
        return manometry_dict, null_values
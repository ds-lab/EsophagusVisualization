from datetime import datetime
import config

from PyQt6.QtWidgets import QMessageBox


class DataValidation:
    @staticmethod
    def validate_patient(patient_dict):
        null_values = []
        invalid_values = []
        error = False
        for key, value in patient_dict.items():
            if value == config.min_value_year or value == config.missing_dropdown or value == config.missing_text:
                null_values.append(key)
                patient_dict[key] = None
            # For Years, check that the date is not greater than the current date
            if isinstance(value, int) and len(str(value)) == 4:  # check only for years
                if value > datetime.now().year:
                    invalid_values.append(key)
        if invalid_values:
            invalid_message = "The values for the following variable(s) are invalid: " + ", ".join(
                invalid_values) + ". Please provide valid values."
            QMessageBox.critical(None, 'Invalid Value(s) Detected', invalid_message)
            error = True
            return patient_dict, null_values, error
        if null_values:
            # check if mandatory values are set
            for key in config.mandatory_values_patient:
                if key in patient_dict and patient_dict[key] is None:
                    null_message = f"The following mandatory value is not set: {key}. Please provide this value."
                    QMessageBox.critical(None, 'Null Value Detected', null_message)
                    error = True
                    return patient_dict, null_values, error
            # Check if other values are set and ask if they should be set to NULL
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
        return patient_dict, null_values, error

    @staticmethod
    def validate_previous_therapy(prev_therapy_dict):
        null_values = []
        invalid_values = []
        error = False
        for key, value in prev_therapy_dict.items():
            if key == "patient_id" and value is None:
                QMessageBox.critical(None, "No patient selected", "Error: Please select a patient.")
                error = True
                return prev_therapy_dict, null_values, error
            if value == config.min_value_year or value == config.missing_dropdown or value == config.missing_text:
                null_values.append(key)
                prev_therapy_dict[key] = None
            # For Years, check that the date is not greater than the current date
            if isinstance(value, int) and len(str(value)) == 4:  # check only for years
                if value > datetime.now().year:
                    invalid_values.append(key)
        if invalid_values:
            invalid_message = "The values for the following variable(s) are invalid: " + ", ".join(
                invalid_values) + ". Please provide valid values."
            QMessageBox.critical(None, 'Invalid Value(s) Detected', invalid_message)
            error = True
            return prev_therapy_dict, null_values, error
        if null_values:
            # check if mandatory values are set
            for key in config.mandatory_values_prev_therapy:
                if key in prev_therapy_dict and prev_therapy_dict[key] is None:
                    null_message = f"The following mandatory value is not set: {key}. Please provide this value."
                    QMessageBox.critical(None, 'Null Value Detected', null_message)
                    error = True
                    return prev_therapy_dict, null_values, error
            # Check if other values are set and ask if they should be set to NULL
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
        return prev_therapy_dict, null_values, error


    @staticmethod
    def validate_visit(visit_dict):
        null_values = []
        invalid_values = []
        mandatory_values = []
        error = False
        for key, value in visit_dict.items():
            print(f"key: {key}, value: {value}")
            if key == "patient_id" and value is None:
                QMessageBox.critical(None, "No patient selected", "Error: Please select a patient.")
                error = True
                return visit_dict, null_values, error
            if value == config.min_value_year or value == config.missing_dropdown or value == config.missing_int:
                null_values.append(key)
                visit_dict[key] = None
            # For Years, check that the date is not greater than the current date
            if isinstance(value, int) and len(str(value)) == 4:  # check only for years
                if value > datetime.now().year:
                    invalid_values.append(key)
        for key, value in visit_dict.items():
            if value is None and key in config.mandatory_values_visit:
                mandatory_values.append(key)
        if mandatory_values:
            null_message = (f"The following mandatory value(s) are not set: " + ", ".join(mandatory_values) +
                            ". Please provide these/this value(s).")
            QMessageBox.critical(None, 'Null Value Detected', null_message)
            error = True
            return visit_dict, null_values, error
        if invalid_values:
            invalid_message = "The values for the following variable(s) are invalid: " + ", ".join(
                invalid_values) + ". Please provide valid values."
            QMessageBox.critical(None, 'Invalid Value(s) Detected', invalid_message)
            error = True
            return visit_dict, null_values, error
        if visit_dict.get('visit_type') == 'Therapy' and visit_dict.get('therapy_type') is None:
            error_message = "Please select the Therapy type for this visit."
            QMessageBox.critical(None, 'Select Therapy type', error_message)
            error = True
            return visit_dict, null_values, error
        if visit_dict.get('visit_type') != 'Therapy' and visit_dict.get('therapy_type') is not None:
            error_message = ("If a therapy was applied at this visit, please select 'Therapy' for this visit.\n If "
                             "no therapy was applied, please do not fill out the therapy type for this visit.")
            QMessageBox.critical(None, 'Invalid data', error_message)
            error = True
            return visit_dict, null_values, error
        return visit_dict, null_values, error

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
    def validate_visitdata(visit_data_dict):
        null_values = []
        error = False
        for key, value in visit_data_dict.items():
            if key == "visit_id" and value is None:
                QMessageBox.critical(None, "No visit selected", "Error: Please select a visit.")
                error = True
                return visit_data_dict, null_values, error
            if value == config.missing_int or value == config.missing_dropdown:
                null_values.append(key)
                visit_data_dict[key] = None
        if null_values:
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
        return visit_data_dict, null_values, error


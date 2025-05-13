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
            return patient_dict, error
        if null_values:
            # check if mandatory values are set
            for key in config.mandatory_values_patient:
                if key in patient_dict and patient_dict[key] is None:
                    null_message = f"The following mandatory value is not set: {key}. Please provide this value."
                    QMessageBox.critical(None, 'Null Value Detected', null_message)
                    error = True
                    return patient_dict, error
            # Check if other values are set and ask if they should be set to NULL
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
        return patient_dict, error

    @staticmethod
    def validate_previous_therapy(prev_therapy_dict):
        null_values = []
        invalid_values = []
        error = False
        for key, value in prev_therapy_dict.items():
            if key == "patient_id" and value is None:
                QMessageBox.critical(None, "No patient selected", "Error: Please select a patient.")
                error = True
                return prev_therapy_dict, error
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
            return prev_therapy_dict, error
        if null_values:
            # check if mandatory values are set
            for key in config.mandatory_values_prev_therapy:
                if key in prev_therapy_dict and prev_therapy_dict[key] is None:
                    null_message = f"The following mandatory value is not set: {key}. Please provide this value."
                    QMessageBox.critical(None, 'Null Value Detected', null_message)
                    error = True
                    return prev_therapy_dict, error
            # Check if other values are set and ask if they should be set to NULL
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
        return prev_therapy_dict, error

    @staticmethod
    def validate_visit(visit_dict):
        null_values = []
        invalid_values = []
        mandatory_values = []
        error = False
        for key, value in visit_dict.items():
            if key == "patient_id" and value is None:
                QMessageBox.critical(None, "No patient selected", "Error: Please select a patient.")
                error = True
                return visit_dict, error
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
            print(f"key: {key}, value: {value}")

        # Uncommenteted: Additional restrictions for the data, that would probably make sense but are not stricly necessary

        # if visit_dict.get('visit_type') == "Initial Diagnostic" and visit_dict.get('months_after_initial_therapy') is not None:
        #     invalid_values.append('visit_type')
        #     invalid_values.append('months_after_initial_therapy')
        
        # if visit_dict.get('visit_type') == "Initial Diagnostic" and visit_dict.get('months_after_last_therapy') is not None:
        #     invalid_values.append('visit_type')
        #     invalid_values.append('months_after_last_therapy')
        if visit_dict.get('visit_type') == "Follow-Up Diagnostic" and visit_dict.get('months_after_last_therapy') is None:
            invalid_values.append('visit_type')
            invalid_values.append('months_after_last_therapy')
        # if visit_dict.get('visit_type') == "Therapy" and visit_dict.get('months_after_diagnosis') is None:
        #     invalid_values.append('visit_type')
        #     invalid_values.append('months_after_diagnosis')
        if visit_dict.get('visit_type') == "Therapy" and visit_dict.get('therapy_type') is None:
            invalid_values.append('visit_type')
            invalid_values.append('therapy_type')
        if mandatory_values:
            null_message = (f"The following mandatory value(s) are not set: " + ", ".join(mandatory_values) +
                            ". Please provide these/this value(s).")
            QMessageBox.critical(None, 'Null Value Detected', null_message)
            error = True
            return visit_dict, error
        if invalid_values:
            invalid_message = "The values for the following variable(s) are invalid/incompatible: " + ", ".join(
                invalid_values) + ". Please provide valid values."
            QMessageBox.critical(None, 'Invalid Value(s) Detected', invalid_message)
            error = True
            return visit_dict, error
        if visit_dict.get('visit_type') == 'Therapy' and visit_dict.get('therapy_type') is None:
            error_message = "Please select the Therapy type for this visit."
            QMessageBox.critical(None, 'Select Therapy type', error_message)
            error = True
            return visit_dict, error
        if visit_dict.get('visit_type') != 'Therapy' and visit_dict.get('therapy_type') is not None:
            error_message = ("If a therapy was applied at this visit, please select 'Therapy' for this visit.\n If "
                             "no therapy was applied, please do not fill out the therapy type for this visit.")
            QMessageBox.critical(None, 'Invalid data', error_message)
            error = True
            return visit_dict, error
        return visit_dict, error

    @staticmethod
    def validate_visitdata(visit_data_dict):
        null_values = []
        error = False
        for key, value in visit_data_dict.items():
            if key == "visit_id" and value is None:
                QMessageBox.critical(None, "No visit selected", "Error: Please select a visit.")
                error = True
                return visit_data_dict, error
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
        return visit_data_dict, error

    @staticmethod
    def validate_complications(complications_dict):
        no_complications = []
        error = False
        for key, value in complications_dict.items():
            if key == "visit_id" and value is None:
                QMessageBox.critical(None, "No visit selected", "Error: Please select a visit.")
                error = True
                return complications_dict, error
            if value == "none":
                no_complications.append(key)
        if len(no_complications) == 7:
            reply = QMessageBox.question(None, 'No Complications', 'No Complications are set. Is this correct?',
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
        return complications_dict, error

    @staticmethod
    def validate_lhm(lhm_dict):
        null_values = []
        error = False
        for key, value in lhm_dict.items():
            if key == "visit_id" and value is None:
                QMessageBox.critical(None, "No visit selected", "Error: Please select a visit.")
                error = True
                return lhm_dict, error
            if value == config.missing_int or value == 0:
                null_values.append(key)
                lhm_dict[key] = None
        if null_values:
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
                return lhm_dict, error
        if lhm_dict.get('type_fundoplicatio') == '---':
            lhm_dict['type_fundoplicatio'] = None
        if lhm_dict.get('fundoplicatio') is None:
            lhm_dict['fundoplicatio'] = False
        if lhm_dict.get('fundoplicatio') is False and lhm_dict.get('type_fundoplicatio') is not None:
            invalid_message = ("The values for the following variable(s) are incompatible: "
                               "'Fundoplicatio' and 'Type of Fundoplicatio'. Please provide valid values.")
            QMessageBox.critical(None, 'Invalid Value(s) Detected', invalid_message)
            error = True
            return lhm_dict, error
        if lhm_dict.get('fundoplicatio') is True and lhm_dict.get('type_fundoplicatio') is None:
            null_message = "Is the type of fundoplicatio unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
                lhm_dict, error
        return lhm_dict, error

    @staticmethod
    def validate_poem(poem_dict):
        null_values = []
        error = False
        for key, value in poem_dict.items():
            if key == "visit_id" and value is None:
                QMessageBox.critical(None, "No visit selected", "Error: Please select a visit.")
                error = True
                return poem_dict, error
            if value == config.missing_int or value == config.missing_dropdown:
                null_values.append(key)
                poem_dict[key] = None
        if poem_dict.get('procedure_duration') == 0:
            null_values.append('procedure_duration')
            poem_dict['procedure_duration'] = None
        if null_values:
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
                return poem_dict, error
        return poem_dict, error

    @staticmethod
    def validate_eckardt(eckardt_dict):
        null_values = []
        values_sum = 0
        error = False
        for key, value in eckardt_dict.items():
            if key != "total_score":
                if key == "visit_id" and value is None:
                    QMessageBox.critical(None, "No visit selected", "Error: Please select a visit.")
                    error = True
                    return eckardt_dict, error
                if value == config.missing_dropdown:
                    null_values.append(key)
                    eckardt_dict[key] = None
                if key != "visit_id" and key != "eckardt_id" and key != "total_score":
                    if value != '---':
                        values_sum += int(value)
        if null_values:
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
                return eckardt_dict, error
        if eckardt_dict.get('total_score') == '---' and not null_values:
            eckardt_dict['total_score'] = values_sum
        elif eckardt_dict.get('total_score') == '---' and null_values:
            null_message = (f"Please set the total score.")
            QMessageBox.critical(None, 'Total Score not filled', null_message)
            error = True
            return eckardt_dict, error
        if values_sum > int(eckardt_dict.get('total_score')):
            invalid_message = ("Incompatible values: "
                               "The individual values and the total score are incompatible. Please provide valid "
                               "values.")
            QMessageBox.critical(None, 'Invalid Value(s) Detected', invalid_message)
            error = True
        if not null_values and values_sum != int(eckardt_dict.get('total_score')):
            invalid_message = ("Incompatible values: "
                               "The individual values and the total score are incompatible. Please provide valid "
                               "values.")
            QMessageBox.critical(None, 'Invalid Value(s) Detected', invalid_message)
            error = True
        return eckardt_dict, error

    @staticmethod
    def validate_gerd(gerd_dict):
        null_values = []
        error = False
        for key, value in gerd_dict.items():
            if key == "visit_id" and value is None:
                QMessageBox.critical(None, "No visit selected", "Error: Please select a visit.")
                error = True
                return gerd_dict, error
            if value == config.missing_int or value == config.missing_dropdown:
                null_values.append(key)
                gerd_dict[key] = None
        if gerd_dict.get('heart_burn') is None:
            null_values.append('heart_burn')
        if gerd_dict.get('ppi_use') is None:
            null_values.append('ppi_use')
        if null_values:
            null_message = "The following values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
        return gerd_dict, error

    @staticmethod
    def validate_medication(medication_dict):
        null_values = []
        invalid_values = []
        mandatory_values = []
        error = False
        for key, value in medication_dict.items():
            if key == "patient_id" and value is None:
                QMessageBox.critical(None, "No patient selected", "Error: Please select a patient.")
                error = True
                return medication_dict, error
            if value == config.missing_text or value == config.missing_dropdown or value == config.missing_int:
                null_values.append(key)
                medication_dict[key] = None
        for key, value in medication_dict.items():
            if value is None and key in config.mandatory_values_medication:
                mandatory_values.append(key)
        if mandatory_values:
            null_message = (f"The following mandatory value is not set: " + ", ".join(mandatory_values) +
                            ". Please provide this value.")
            QMessageBox.critical(None, 'Null Value Detected', null_message)
            error = True
            return medication_dict, error
        if (medication_dict.get('medication_use') != 'No relevant medication' and
                (medication_dict.get('medication_name') is None or medication_dict.get('medication_dose') is None)):
            null_message = "The following optional values are not set: " + ", ".join(
                null_values) + ". Do you want to set them to null/unknown?"
            reply = QMessageBox.question(None, 'Null Values Detected', null_message,
                                         QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                error = True
        return medication_dict, error

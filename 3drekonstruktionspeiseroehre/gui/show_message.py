from PyQt6.QtWidgets import QMessageBox


class ShowMessage:

    @staticmethod
    def to_update_for_visit(type_to_update: str):
        reply = QMessageBox.question(None, f'{type_to_update} already exist/s in the database.',
                                     f"Should the {type_to_update} for this visit be updated?",
                                     QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    @staticmethod
    def no_data_to_download(data_to_download: str):
        QMessageBox.critical(None, f'No {data_to_download}', f'There are no {data_to_download} for this visit.')

    @staticmethod
    def load_saved_reconstruction():
        reply = QMessageBox.question(None, f'Reconstruction found in the database.',
                                     f"Do you want to load the existing reconstruction for this visit (instead of creating a new one)?",
                                     QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    @staticmethod
    def wrong_format(fileextension, acceptable_formats):
        QMessageBox.critical(None, f'{fileextension} is no valid format', f'Please choose one of the following formats: ' + ", ".join(
                acceptable_formats))

    @staticmethod
    def update_confirmed():
        reply = QMessageBox.question(None, 'This Patient already exists in the database.',
                                     "Should the Patients data be updated?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    @staticmethod
    def add_confirmed():
        reply = QMessageBox.question(None, 'This Patient does not exists in the database.',
                                     "Should the patient be created?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

    @staticmethod
    def data_not_written():
        QMessageBox.critical(None, 'Error', "Could not write data to the CSV file. Please ensure the file is writable and not open in another program.")

    @staticmethod
    def deletion_confirmed(data_type):
        reply = QMessageBox.question(None, 'Confirm deletion',
                                     f"Are you absolutely sure you want to delete ALL data related to this {data_type}?\n"
                                     f"This action cannot be undone.", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False




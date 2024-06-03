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




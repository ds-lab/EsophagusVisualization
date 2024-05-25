from PyQt6.QtWidgets import QMessageBox


class PopupWindow:
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

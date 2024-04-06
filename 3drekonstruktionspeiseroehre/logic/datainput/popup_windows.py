from PyQt6.QtWidgets import QMessageBox


class PopupWindow:

    def update_confirmed(self):
        reply = QMessageBox.question(None, 'This Patient already exists in the database.',
                                     "Should the Patients data be updated?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            return True
        return False

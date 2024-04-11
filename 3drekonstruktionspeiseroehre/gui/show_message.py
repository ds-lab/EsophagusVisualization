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

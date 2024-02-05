from PyQt6.QtWidgets import QMainWindow, QCompleter, QMessageBox
from PyQt6.QtCore import Qt, QDate
from gui.master_window import MasterWindow
from logic.data_declarative_models import Patient
from PyQt6 import uic
from logic.database import get_db
from logic.services.patient_service import PatientService
from gui.file_selection_window import FileSelectionWindow


class SelectPatientWindow(QMainWindow):
    def __init__(self, master_window: MasterWindow):
        super().__init__()
        self.ui = uic.loadUi(
            "./ui-files/select_patient_window_design.ui", self)
        self.master_window = master_window
        self.ui.enter_button.clicked.connect(self.__onEnter)
        self.ui.new_patient_btn.clicked.connect(self.__onEnter)
        self.db = get_db()
        self.patient_service = PatientService(self.db)
        self.init_ui()
        self.patient = None

    def __onEnter(self):
        self.patient = [
            patient for patient in self.patients if patient.patient_id == self.ui.patient_id.text()
        ]
        if (self.patient):
            self.master_window.switch_to(FileSelectionWindow(self.master_window, "berlin", self.patient))
        else:
            QMessageBox.warning(self, None, "Please enter patient id.", QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)

    def __onNewPatient(self):
        # TODO switch new patient Data
        pass

    def init_ui(self):
        self.patients = self.patient_service.get_all_patients()
        suggestions = [patient.patient_id for patient in self.patients]
        completer = QCompleter(suggestions, self)
        # Case-insensitive autocomplete
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.patient_id.setCompleter(completer)
        self.ui.patient_id.editingFinished.connect(self.__patient_id_filled)

    def __patient_id_filled(self):
        # ToDo: Felder mit echten Daten aus der DB für den jeweiligen Patienten füllen, wenn vorhanden
        self.patient = [
            patient for patient in self.patients if patient.patient_id == self.ui.patient_id.text()
        ]

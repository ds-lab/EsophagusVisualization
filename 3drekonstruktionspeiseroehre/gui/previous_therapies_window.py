from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.xray_window_managment import ManageXrayWindows
from logic.endoflip_data_processing import process_endoflip_xlsx
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from logic.visualization_data import VisualizationData


class PreviousTherapiesWindow(QMainWindow):
    def __init__(self, master_window: MasterWindow, patient_data: PatientData = PatientData()):
        super().__init__()
        self.ui = uic.loadUi("./ui-files/previous_therapies_window_design.ui", self)
        self.master_window: MasterWindow = master_window
        self.patient_data: PatientData = patient_data
        self.ui.save_button.clicked.connect(self.__save_button_clicked)

    def __save_button_clicked(self):
        """
        checks data in previous therapies and saves them
        """
        if (not self.ui.botox_check.isChecked() and not self.ui.pneu_dil_30_check.isChecked() and not
        self.ui.pneu_dil_35_check.isChecked() and not self.ui.pneu_dil_40_check.isChecked() and not
        self.ui.poem_check.isChecked() and not self.ui.lapro_check.isChecked() and not
        self.ui.other_check.isChecked()
        ):
            QMessageBox.warning(self, "No Therapy selected.", "Please select at least one therapy.")
        elif (self.ui.botox_check.isChecked() and self.ui.botox_spin.value() == 0 or
              self.ui.pneu_dil_30_check.isChecked() and self.ui.botox_spin.value() == 0 or
              self.ui.pneu_dil_35_check.isChecked() and self.ui.pneu_dil_35_spin.value() == 0 or
              self.ui.pneu_dil_40_check.isChecked() and self.ui.pneu_dil_40_spin.value() == 0 or
              self.ui.poem_check.isChecked() and self.ui.poem_spin.value() == 0 or
              self.ui.lapro_check.isChecked() and self.ui.lapro_spin.value() == 0 or
              self.ui.other_check.isChecked() and self.ui.other.spin.value() == 0):
            QMessageBox.warning(self, "Check inputs", "Please check the consistency of your inputs.")

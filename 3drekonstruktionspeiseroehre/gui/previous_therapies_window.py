from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from gui.master_window import MasterWindow


class PreviousTherapiesWindow(QMainWindow):
    def __init__(self, master_window: MasterWindow):
        super().__init__()
        self.ui = uic.loadUi("./ui-files/previous_therapies_window_design.ui", self)
        self.master_window = master_window
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

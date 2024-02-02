from PyQt6.QtWidgets import QMainWindow
from gui.master_window import MasterWindow
from PyQt6 import uic

class SelectPatientWindow(QMainWindow):
    def __init__(self, master_window: MasterWindow):
        super().__init__()
        self.ui = uic.loadUi("./ui-files/select_patient_window_design.ui", self)
        self.master_window = master_window
        self.ui.enter_button.clicked.connect(self.__onEnter)
        self.ui.new_patient_btn.clicked.connect(self.__onEnter)

    def __onEnter(self):
        pass
    
    def __onNewPatient(self):
        self.master_window.switch_to()

from PyQt5 import uic
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QMessageBox
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

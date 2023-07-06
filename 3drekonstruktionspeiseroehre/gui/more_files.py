from PyQt5.QtWidgets import QMainWindow, QAction
from gui.master_window import MasterWindow
from gui.xray_region_selection_window import XrayRegionSelectionWindow
from logic.visit_data import VisitData
from logic.patient_data import PatientData


class ShowMoreWindows(QMainWindow):

    def __init__(self, master_window: MasterWindow, visit: VisitData, patient_data: PatientData):
        """
        init FileSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        """
        super().__init__()

        self.master_window: MasterWindow = master_window
        self.patient_data: PatientData = patient_data
        self.visit: VisitData = visit

        w_list = []

        # erzeuge alle Fenster aller Eingabedaten und speicher diese
        for n, visualization in enumerate(visit.visualization_data_list):
            xray_selection_window = XrayRegionSelectionWindow(self.master_window, self.patient_data, self.visit, n)
            w_list.append(xray_selection_window)

        # Initialize a linked list of Xray windows
        for i, w in enumerate(w_list):
            # Last window -> no next window
            if i == len(w_list)-1:
                w.next_window = None
            else:
                w.next_window = w_list[i+1]

        # Start with the first XraySelectionWindow
        self.master_window.switch_to(w_list[0])




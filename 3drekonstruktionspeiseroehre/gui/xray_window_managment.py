from gui.master_window import MasterWindow
from gui.xray_region_selection_window import XrayRegionSelectionWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData


class ManageXrayWindows:

    def __init__(self, master_window: MasterWindow, visit: VisitData, patient_data: PatientData):
        """
        Class to manage X-ray windows for a given visit and patient data.

        :param master_window: The MasterWindow in which the next window will be displayed.
        :param visit: The VisitData object representing the visit information.
        :param patient_data: The PatientData object representing the patient information.
        """
        # Initialize class attributes
        self.master_window: MasterWindow = master_window
        self.patient_data: PatientData = patient_data
        self.visit: VisitData = visit

        # Create a list to store all X-ray windows
        xray_windows = []

        # Create and store X-ray windows for each visualization data
        for n, visualization in enumerate(visit.visualization_data_list):
            xray_selection_window = XrayRegionSelectionWindow(self.master_window, self.patient_data, self.visit, n)
            xray_windows.append(xray_selection_window)

        # Initialize a linked list of X-ray windows
        for i, w in enumerate(xray_windows):
            # Last window -> no next window
            if i == len(xray_windows)-1:
                w.next_window = None
            else:
                w.next_window = xray_windows[i+1]

        # Start with the first X-ray selection window
        self.master_window.switch_to(xray_windows[0])




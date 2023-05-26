from PyQt5.QtWidgets import QMainWindow, QAction
from gui.master_window import MasterWindow
from gui.xray_region_selection_window import XrayRegionSelectionWindow


class ShowMoreWindows(QMainWindow):

    def __init__(self, master_window: MasterWindow, visualization_list):
        """
        init FileSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        """
        super().__init__()

        self.master_window: MasterWindow = master_window

        w_list = []

        for visualization in visualization_list:

            xray_selection_window = XrayRegionSelectionWindow(self.master_window, visualization)
            w_list.append(xray_selection_window)


        for i,w in enumerate(w_list):
            if i == len(w_list)-1:
                next_window = None
                w.all_visualization = w_list[i-1].all_visualization
            elif i == 0:
                next_window = w_list[i+1]
            else:
                next_window = w_list[i+1]
                w.all_visualization = w_list[i - 1].all_visualization
            w.next_window = next_window

        self.master_window.switch_to(w_list[0])



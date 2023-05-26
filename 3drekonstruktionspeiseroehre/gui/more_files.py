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

        # erzeuge alle Fenster aller Eingabedaten und speicher diese
        for visualization in visualization_list:

            xray_selection_window = XrayRegionSelectionWindow(self.master_window, visualization)
            w_list.append(xray_selection_window)

        # setze für jedes Fenster das nächste Fenster
        for i,w in enumerate(w_list):
            # falls das erste Fenster, dann initialisiere all_visualization mit leerer Liste
            if i == 0:
                next_window = w_list[i+1]
                w.all_visualization = []
            # falls letztes Fenster, setze kein nächstes Fenster
            elif i == len(w_list)-1:
                next_window = None
                w.all_visualization = w_list[i-1].all_visualization
            # falls in der Mitte, nächstes Fenster erzeugen
            # hole Daten (all_visualisation) vom vorherigen Fenster
            else:
                next_window = w_list[i+1]
                w.all_visualization = w_list[i - 1].all_visualization
            w.next_window = next_window

        # öffne erstes Fenster
        self.master_window.switch_to(w_list[0])



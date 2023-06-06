from PyQt5.QtWidgets import QMainWindow, QAction
from gui.master_window import MasterWindow
from gui.xray_region_selection_window import XrayRegionSelectionWindow


class ShowMoreWindows(QMainWindow):

    def __init__(self, master_window: MasterWindow, visualization_list):
    #def __init__(self, master_window: MasterWindow, visualization_dict):
        """
        init FileSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        """
        super().__init__()

        self.master_window: MasterWindow = master_window

        w_list = []
        # w_dict = {}

        # erzeuge alle Fenster aller Eingabedaten und speicher diese
        for n, visualization in enumerate(visualization_list):
            xray_selection_window = XrayRegionSelectionWindow(self.master_window, visualization, n)
            w_list.append(xray_selection_window)

        # keys = visualization_dict.keys()
        # w_dict = {x: XrayRegionSelectionWindow(self.master_window,visualization_dict[x]) for x in keys}

        #print(w_dict)
        # setze für jedes Fenster das nächste Fenster
        for i, w in enumerate(w_list):
            # falls das erste Fenster, dann initialisiere all_visualization mit leerer Liste
            if i == 0:
                next_window = w_list[i+1]
                w.all_visualization = []
            # falls letztes Fenster, setze kein nächstes Fenster
            elif i == len(w_list)-1:
                next_window = None
                w.all_visualization = w_list[i-1].all_visualization # wenn i==1/2 -> w_list[0/1].all_visualization
        #     # falls in der Mitte, nächstes Fenster erzeugen
        #     # hole Daten (all_visualisation) vom vorherigen Fenster
            else:
                next_window = w_list[i+1]
            w.all_visualization = w_list[i - 1].all_visualization
            w.next_window = next_window

        # for i, w in enumerate(w_dict):
        #     # falls das erste Fenster, dann initialisiere all_visualization mit leerer Liste
        #     if i == 0:
        #         print("erstes Fenster")
        #         next_window = w_dict[2]
        #         w_dict[w].all_visualization = []
        #         #print(i, w_dict[w].all_visualization)
        #     # falls letztes Fenster, dann setze kein nächstes Fenster
        #     elif (i == 1 & len(w_dict) == 2) | (i == 2 & len(w_dict) == 3): # elif i == len(w_dict)-1 & i != 0:
        #         print("letztes Fenster")
        #         next_window = None
        #         w_dict[w].all_visualization = w_dict[i].all_visualization
        #         #print(i, w_dict[w].all_visualization)
        #     # falls in der Mitte, nächstes Fenster erzeugen
        #     # hole Daten (all_visualisation) vom vorherigen Fenster
        #     elif i == 1 & len(w_dict) == 3:
        #         print("mittleres Fenster")
        #         next_window = w_dict[3]
        #         w_dict[w].all_visualization = w_dict[2].all_visualization #?????
        #         #print(i, w_dict[w].all_visualization)
        #     w_dict[w].next_window = next_window
        # # öffne erstes Fenster
        self.master_window.switch_to(w_list[0])
        # self.master_window.switch_to(w_dict[1])



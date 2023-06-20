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
        #next_window = None

        # erzeuge alle Fenster aller Eingabedaten und speicher diese
        for n, visualization in enumerate(visualization_list):
            # visualization ist None, wenn kein Bild an der Stelle n eingegeben wurde
            if visualization is not None:
                xray_selection_window = XrayRegionSelectionWindow(self.master_window, visualization, n)
                #xray_selection_window.next_window = next_window
                w_list.append(xray_selection_window)
            else:
                w_list.append(None)

        # setze für jedes Fenster das nächste Fenster
        for i, w in enumerate(w_list):
            # falls das erste Fenster, dann initialisiere all_visualization mit leerer Liste
            if i == 0 and w is not None: # erstes Bild ist not None
                # erstes Fenster ist auch letztes Fenster
                if w_list[1] is None and w_list[2] is None:
                    next_window = None
                    w.all_visualization = []
                # es gibt ein erstes Fenster und ein zweites Fenster → nächstes Fenster erzeugen
                elif w_list[1] is not None:
                    next_window = w_list[1]
                    w.all_visualization = []
                # es gibt das erste und das dritte Bild, aber nicht das zweite
                elif w_list[2] is not None and w_list[1] is None:
                    next_window = w_list[2]
                    w.all_visualization = []
                w.next_window = next_window
            # elif i == 0 and w is None: # erstes Bild ist None
            #     # es gibt kein weiteres Bild wird nicht überprüft, da Annahme, dass mind 1 geladen wird
            #     if w_list[1] is not None: # zweites Bild ist nicht None
            #         next_window = w_list[1]
            #         w.all_visualization = []
            #     # zweites Bild nicht geladen, drittes schon
            #     elif w_list[1] is None and w_list[2] is not None:
            #         next_window = w_list[2]
            #         w.all_visualization = []
            # zweites Fenster
            if i == 1 and w is not None:
                # zweites Fenster ist auch letztes Fenster, es gibt kein drittes Bild
                if w_list[2] is None:
                    next_window = None
                    # wenn es das erste Bild gab:
                    if w_list[0] is not None:
                        w.all_visualization = w_list[0].all_visualization
                    else:
                        w.all_visualization = []
                # es gibt ein zweites Fenster und ein drittes Fenster → nächstes Fenster erzeugen
                elif w_list[2] is not None:
                    next_window = w_list[2]
                    # wenn es das erste Bild gab:
                    if w_list[0] is not None:
                        w.all_visualization = w_list[0].all_visualization
                    else:
                        w.all_visualization = []
                w.next_window = next_window
            # drittes Fenster
            if i == 2 and w is not None:
                next_window = None
                if w_list[1] is not None:
                    w.all_visualization = w_list[1].all_visualization
                elif w_list[0] is not None:
                    w.all_visualization = w_list[0].all_visualization
                else:
                    w.all_visualization = []
                w.next_window = next_window

        # not_none = (el for el in w_list if el is not None)
        # value = next(not_none, None)
        # if value is not None:
        if w_list[0] is not None:
            self.master_window.switch_to(w_list[0])
        elif w_list[1] is not None:
            self.master_window.switch_to((w_list[1]))
        elif w_list[2] is not None:
            self.master_window.switch_to((w_list[2]))
        else:
            print("is None")




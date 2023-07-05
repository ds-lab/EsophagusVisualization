import numpy as np
from shapely.geometry import Polygon
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QAction
from skimage import io
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.widgets import PolygonSelector
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
from gui.position_selection_window import PositionSelectionWindow
from logic.visualization_data import VisualizationData
import logic.image_polygon_detection as image_polygon_detection

#ToDo: Linien sollen schräg eingezeichnet werden können

class XrayRegionSelectionWindow(QMainWindow):
    """Window where the user selects the shape of the esophagus on the x-ray image"""

    next_window = None
    all_visualization = []

    def __init__(self, master_window: MasterWindow, visualization, n):
        """
        init XrayRegionSelectionWindow
        :param master_window: the FlexibleWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        :param n: ??
        """

        super().__init__()
        self.ui = uic.loadUi("ui-files/xray_region_selection_window_design.ui", self)
        self.master_window = master_window
        self.master_window.maximize()
        self.visualization_data = visualization
        self.n = n
        self.polygon = []

        self.figure_canvas = FigureCanvasQTAgg(Figure())
        self.ui.gridLayout.addWidget(self.figure_canvas)
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        self.plot_ax = self.figure_canvas.figure.subplots()
        self.figure_canvas.figure.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.95)
        self.selector = PolygonSelector(self.plot_ax, self.__onselect, useblit=True, props=dict(color='red'))

        self.xray_image = io.imread(self.visualization_data.xray_filename)

        self.plot_ax.imshow(self.xray_image)
        self.plot_ax.axis('off')

        self.polygon = image_polygon_detection.calculate_xray_polygon(self.xray_image)

        if len(self.polygon) > 2:
            self.selector.verts = self.polygon
        else:
            self.selector.verts = [(0, 0)]
            self.__reset_selector()

    def __onselect(self, polygon):
        """
        called when new polygon was created
        :param polygon: new polygon
        """
        self.polygon = polygon

    def __reset_button_clicked(self):
        """
        reset-button callback
        """
        self.__reset_selector()

    def __apply_button_clicked(self):
        """
        apply-button callback
        """

        if len(self.polygon) > 2:
            shapely_poly = Polygon(self.polygon)
            if shapely_poly.is_valid:
                self.ui.apply_button.setDisabled(True)
                self.visualization_data.xray_polygon = np.array(self.polygon, dtype=int)
                self.visualization_data.xray_image_height = self.xray_image.shape[0]
                self.visualization_data.xray_image_width = self.xray_image.shape[1]
                # übergebe all_visualization vom vorherigen Fenster
                position_selection_window = PositionSelectionWindow(self.master_window, self.visualization_data,
                                                                    self.next_window, self.all_visualization, self.n)
                # speichere all_visualization vom nächsten Fenster
                self.all_visualization = position_selection_window.all_visualization
                self.master_window.switch_to(position_selection_window)
                self.close()
            else:
                QMessageBox.critical(self, "Fehler", "Die Auswahl darf keine Schnittpunkte besitzen")
        else:
            QMessageBox.critical(self, "Fehler", "Bitte die Form des Ösophagus als Polygon einzeichnen")

    def __reset_selector(self):
        """
        starts the selection of a new polygon
        """
        self.selector._xs, self.selector._ys = [], []
        self.selector._xys = [(0, 0)]
        self.polygon.clear()
        self.selector.clear()
        self.selector._selection_completed = False
        self.selector.set_visible(True)

    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_xray_region_selection_info()
        info_window.show()


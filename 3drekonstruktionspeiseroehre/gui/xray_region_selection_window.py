import logic.image_polygon_detection as image_polygon_detection
import numpy as np
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.position_selection_window import PositionSelectionWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.widgets import PolygonSelector
#from PyQt5 import uic
#from PyQt5.QtWidgets import QAction, QMainWindow, QMessageBox
from PyQt6 import uic
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from shapely.geometry import Polygon
from skimage import io


class XrayRegionSelectionWindow(QMainWindow):
    """Window where the user selects the shape of the esophagus on the x-ray image"""

    next_window = None
    all_visualization = []

    def __init__(self, master_window: MasterWindow, patient_data: PatientData, visit: VisitData, n):
        """
        init XrayRegionSelectionWindow
        :param master_window: the FlexibleWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        :param n: n-th visualization of that visit
        """

        super().__init__()
        self.ui = uic.loadUi("./ui-files/xray_region_selection_window_design.ui", self)
        self.master_window = master_window
        self.patient_data = patient_data
        self.master_window.maximize()
        self.visit = visit
        self.visualization_data = visit.visualization_data_list[n]
        self.n = n
        self.polygon = []

        # Create a figure canvas for displaying the image
        self.figure_canvas = FigureCanvasQTAgg(Figure())
        self.ui.gridLayout.addWidget(self.figure_canvas)
        # Connect button click events to methods
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        # Create a menu button for displaying the Info-Window
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        # Create a plot axis for displaying the image
        self.plot_ax = self.figure_canvas.figure.subplots()
        self.figure_canvas.figure.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.95)
        # Create a polygon selector for user interaction
        self.selector = PolygonSelector(self.plot_ax, self.__onselect, useblit=True, props=dict(color='red'))

        # Load the X-ray image
        self.xray_image = io.imread(self.visualization_data.xray_filename)

        # Display the X-ray image
        self.plot_ax.imshow(self.xray_image)
        self.plot_ax.axis('off')

        # Calculate the initial polygon from the X-ray image
        self.polygon = image_polygon_detection.calculate_xray_polygon(self.xray_image)

        # If the polygon has more than 2 points, set it as the initial selection
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
        # Check if the selected polygon is valid
        if len(self.polygon) > 2:
            shapely_poly = Polygon(self.polygon)
            if shapely_poly.is_valid:
                self.ui.apply_button.setDisabled(True)
                self.visualization_data.xray_polygon = np.array(self.polygon, dtype=int)
                self.visualization_data.xray_image_height = self.xray_image.shape[0]
                self.visualization_data.xray_image_width = self.xray_image.shape[1]
                position_selection_window = PositionSelectionWindow(self.master_window, self.next_window, self.patient_data, self.visit, self.n, self.polygon)
                self.master_window.switch_to(position_selection_window)
                self.close()
            else:
                QMessageBox.critical(self, "Fehler", "Die Auswahl darf keine Schnittpunkte besitzen")
        else:
            QMessageBox.critical(self, "Fehler", "Bitte die Form des Ösophagus als Polygon einzeichnen")

    def __reset_selector(self):
        """
        starts the selection of a new polygon/resets the polygon selector
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


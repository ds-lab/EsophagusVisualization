import logic.image_polygon_detection as image_polygon_detection
import numpy as np
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.visualization_window import VisualizationWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.widgets import PolygonSelector
from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMessageBox
from shapely.geometry import Polygon
from PIL import Image


class EndoscopySelectionWindow(QtWidgets.QMainWindow):
    """Window where the user selects the polyon shape on the endoscopy images"""

    def __init__(self, master_window: MasterWindow, patient_data: PatientData, visit:VisitData):
        """
        Initialize EndoscopySelectionWindow.

        Args:
            master_window (MasterWindow): The MasterWindow in which the next window will be displayed.
            visualization_data (VisualizationData): An instance of VisualizationData that the endoscopy images belong to.
            patient_data (PatientData): An instance of the current PatientData that the VisualizationDate belongs to.
        """
        super().__init__()
        self.ui = uic.loadUi("./ui-files/endoscopy_selection_window_design.ui", self)
        self.master_window = master_window
        self.patient_data = patient_data
        self.visit = visit

        self.current_image_index = 0
        # list of points (not cm)
        self.current_polygon = []
        self.polygon_list = []

        self.figure_canvas = FigureCanvasQTAgg(Figure())
        self.ui.gridLayout.addWidget(self.figure_canvas)
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        self.plot_ax = self.figure_canvas.figure.subplots()
        self.figure_canvas.figure.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.95)

        # Get endoscopy images (same for all visualisation data since only xray differ)
        self.endoscopy_images = [np.array(Image.open(file)) for file in
                                 visit.visualization_data_list[0].endoscopy_files]

        self.__load_image(self.endoscopy_images[0])
        self.__update_button_text()

    def __menu_button_clicked(self):
        """
        Callback for the menu button.

        Shows an InfoWindow with relevant information.
        """
        info_window = InfoWindow()
        info_window.show_endoscopy_selection_info()
        info_window.show()

    def __update_button_text(self):
        """
        Updates the text of the apply button based on the current image index.
        """
        if not self.__is_last_image():
            self.ui.apply_button.setText("Apply selection and load next image")
        else:
            self.ui.apply_button.setText("Apply selection and generate visualization")

    def __is_last_image(self) -> bool:
        """
        Checks if the last image is loaded.

        Returns:
            bool: True if the last image is loaded, False otherwise.
        """
        return self.current_image_index == len(self.endoscopy_images) - 1

    def __load_image(self, image):
        """
        Loads the given image and initializes the polygon selector.

        Args:
            image: The image to load.
        """
        self.plot_ax.clear()
        self.plot_ax.imshow(image)
        self.plot_ax.axis('off')
        self.selector = PolygonSelector(self.plot_ax, self.__onselect, useblit=True, props=dict(color='red'))

        polygon = image_polygon_detection.calculate_endoscopy_polygon(image)

        self.selector.verts = [(0, 0)]
        self.__reset_selector()

        if len(polygon) > 0:
            self.selector.verts = polygon
            self.current_polygon = polygon

    def __onselect(self, polygon):
        """
        Called when a polygon selection is finished.

        Args:
            polygon: The new polygon selection.
        """
        self.current_polygon = polygon

    def __reset_button_clicked(self):
        """
        Callback for the reset button.

        Resets the polygon selection.
        """
        self.__reset_selector()

    def __apply_button_clicked(self):
        """
        Callback for the apply button.

        Applies the current polygon selection and either loads the next image or generates visualization.
        """
        if len(self.current_polygon) > 2:
            shapely_poly = Polygon(self.current_polygon)
            if shapely_poly.is_valid:
                self.polygon_list.append(np.array(self.current_polygon, dtype=int))
                if self.__is_last_image():
                    self.ui.apply_button.setDisabled(True)
                    
                    # Update the polygon for all visualization objects in visit
                    for vis in self.visit.visualization_data_list:
                        vis.endoscopy_polygons = self.polygon_list

                    self.patient_data.add_visit(self.visit.name, self.visit)
                    visualization_window = VisualizationWindow(self.master_window, self.patient_data)
                    self.master_window.switch_to(visualization_window)
                    self.close()
                    
                else:
                    self.current_image_index += 1
                    self.__load_image(self.endoscopy_images[self.current_image_index])
                    self.__update_button_text()
            else:
                QMessageBox.critical(self, "Error", "The selection must not have any intersections.")
        else:
            QMessageBox.critical(self, "Error", "Please draw the cross-section of the esophagus as a polygon.")

    def __reset_selector(self):
        """
        Starts a new polygon selection by resetting the selector.
        """
        self.selector._xs, self.selector._ys = [], []
        self.selector._xys = [(0, 0)]
        self.current_polygon.clear()
        self.selector.clear()
        self.selector._selection_completed = False
        self.selector.set_visible(True)

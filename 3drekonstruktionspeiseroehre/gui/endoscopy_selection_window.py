import numpy as np
from PyQt5.QtWidgets import QMessageBox, QAction
from shapely.geometry import Polygon
from skimage import io
from PyQt5 import QtWidgets, uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.widgets import PolygonSelector
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
from logic.visualization_data import VisualizationData
from logic.patient_data import PatientData
from gui.visualization_window import VisualizationWindow
import logic.image_polygon_detection as image_polygon_detection


class EndoscopySelectionWindow(QtWidgets.QMainWindow):
    """Window where the user selects the profiles on the endoscopy images"""

    def __init__(self, master_window: MasterWindow, visualization_data: VisualizationData, patient_data: PatientData):
        """
        init EndoscopySelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        """
        super().__init__()
        self.ui = uic.loadUi("3drekonstruktionspeiseroehre/ui-files/endoscopy_selection_window_design.ui", self)
        self.master_window = master_window
        self.patient_data = patient_data

        self.visualization_data = visualization_data
        self.current_image_index = 0
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

        self.endoscopy_images = [io.imread(filename) for filename in visualization_data.endoscopy_filenames]

        self.__load_image(self.endoscopy_images[0])
        self.__update_button_text()

    def __menu_button_clicked(self):
        """
        menu button callback
        shows an InfoWindow
        """
        info_window = InfoWindow()
        info_window.show_endoscopy_selection_info()
        info_window.show()

    def __update_button_text(self):
        """
        updates the button text
        """
        if not self.__is_last_image():
            self.ui.apply_button.setText('Auswahl anwenden und nächstes Bild laden')
        else:
            self.ui.apply_button.setText('Auswahl anwenden und Visualisierung generieren')

    def __is_last_image(self):
        """
        checks if the last image is loaded
        :return: True or False
        """
        return self.current_image_index == len(self.endoscopy_images) - 1

    def __load_image(self, image):
        """
        loads the given image
        :param image: the image to load
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
        called when a polygon is finished
        :param polygon: the new polygon
        """
        self.current_polygon = polygon

    def __reset_button_clicked(self):
        """
        callback of reset-button
        """
        self.__reset_selector()

    def __apply_button_clicked(self):
        """
        apply-button callback
        """
        if len(self.current_polygon) > 2:
            shapely_poly = Polygon(self.current_polygon)
            if shapely_poly.is_valid:
                self.polygon_list.append(np.array(self.current_polygon, dtype=int))
                if self.__is_last_image():
                    self.ui.apply_button.setDisabled(True)
                    self.visualization_data.endoscopy_polygons = self.polygon_list
                    self.patient_data.add_visualization(self.visualization_data._xray_filename, self.visualization_data)
                    visualization_window = VisualizationWindow(self.master_window, self.patient_data)
                    self.master_window.switch_to(visualization_window)
                    self.close()
                else:
                    self.current_image_index += 1
                    self.__load_image(self.endoscopy_images[self.current_image_index])
                    self.__update_button_text()
            else:
                QMessageBox.critical(self, "Fehler", "Die Auswahl darf keine Schnittpunkte besitzen")
        else:
            QMessageBox.critical(self, "Fehler", "Bitte den Querschnitt des Ösophagus als Polygon einzeichnen")

    def __reset_selector(self):
        """
        starts a new polygon selection
        """
        self.selector._xs, self.selector._ys = [], []
        self.selector._xys = [(0, 0)]
        self.current_polygon.clear()
        self.selector.clear()
        self.selector._selection_completed = False
        self.selector.set_visible(True)

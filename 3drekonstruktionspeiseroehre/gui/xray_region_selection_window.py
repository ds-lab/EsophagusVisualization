import logic.image_polygon_detection as image_polygon_detection
import numpy as np
import cv2
import os
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.position_selection_window import PositionSelectionWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.widgets import PolygonSelector
from PyQt6 import uic
from PyQt6.QtGui import QAction, QImage, QPainter, QPixmap, QColor
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from shapely.geometry import Polygon, Point
from PIL import Image



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

        # Create a figure canvas for displaying the image
        self.figure_canvas = FigureCanvasQTAgg(Figure())
        self.ui.gridLayout.addWidget(self.figure_canvas)
        # Connect button click events to methods
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        self.ui.nextSelection_button.clicked.connect(self.__next_button_clicked)
        self.ui.deletePoint_button.clicked.connect(self.__delete_button_clicked)
        # Create a menu button for displaying the Info-Window
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        # Create a plot axis for displaying the image
        self.plot_ax = self.figure_canvas.figure.subplots()
        self.figure_canvas.figure.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.95)
        self.polygon_colors = ['red', 'blue', 'green']
        self.current_polygon_index = 0
        self.polygon_selectors = []
        self.polygon_points = {}
        self.checkboxes = [self.ui.oesophagus, self.ui.spine, self.ui.barium]
        self.checkbox_names = {self.ui.oesophagus: 'oesophagus', self.ui.spine: 'spine',
                               self.ui.barium: 'barium'}
        # Load the X-ray image
        image = Image.open(self.visualization_data.xray_file)
        self.xray_image = np.array(image)

        # Display the X-ray image
        self.plot_ax.imshow(self.xray_image)
        self.plot_ax.axis('off')

        # Calculate the initial polygon from the X-ray image
        self.polygonOes = image_polygon_detection.calculate_xray_polygon(self.xray_image)
        self.init_first_polygon()

    def init_first_polygon(self):
        # Always create the initial polygon
        color = self.polygon_colors[0]
        self.selector = PolygonSelector(self.plot_ax, self.__onselect, useblit=True, props=dict(color=color))
        self.polygon_selectors.append(self.selector)

        # If the polygon has more than 2 points, set it as the initial selection
        if len(self.polygonOes) > 2:
            self.selector.verts = self.polygonOes
            self.polygon_points["oesophagus"] = self.selector.verts
        else:
            self.selector.verts = [(0, 0)]
            self.__reset_selector()
        self.figure_canvas.draw_idle()
    def init_polygon_selector(self):
        color = self.polygon_colors[self.current_polygon_index]
        self.selector = PolygonSelector(self.plot_ax, self.__onselect, useblit=True, props=dict(color=color))
        self.polygon_selectors.append(self.selector)
    def __onselect(self, verts):
        checkbox = self.checkboxes[self.current_polygon_index]
        polygon_name = self.checkbox_names[checkbox]
        self.polygon_points[polygon_name] = verts

    def __reset_button_clicked(self):
        """
        reset-button callback
        """
        self.__reset_selector()

    def __reset_selector(self):
        """
        Starts the selection of a new polygon / resets the polygon selector.
        """
        if self.selector:
            # Clear the current polygon points
            self.selector._xys = [(0, 0)]  # Reset internal coordinates
            self.selector._xs, self.selector._ys = [], []  # Clear coordinate lists

            # Clear and reset the selector
            self.selector.clear()
            self.selector._selection_completed = False
            self.selector.set_visible(True)

            # Optionally clear the polygon points in the dictionary
            checkbox = self.checkboxes[self.current_polygon_index]
            polygon_name = self.checkbox_names.get(checkbox, None)
            if polygon_name:
                self.polygon_points[polygon_name] = []

            # Redraw the canvas to reflect changes
            self.figure_canvas.draw_idle()

    def __next_button_clicked(self):
        '''
        Starts the input for a new polygon if you want to save several masks
        '''

        if not self.__validate_current_polygon():
            QMessageBox.critical(self, "Error", "The current polygon is invalid. Please correct it before proceeding.")
            return
        # Move to the next checkbox
        self.current_polygon_index += 1

        if self.current_polygon_index < len(self.checkboxes):
            checkbox = self.checkboxes[self.current_polygon_index]
            if checkbox.isChecked():
                self.init_polygon_selector()
                polygon_name = self.checkbox_names[checkbox]

            else:
                self.__next_button_clicked() # Skip to the next checkbox if this one is not checked
        else:

            self.selector.disconnect_events()
    def __validate_current_polygon(self):
        """
        Validate the current polygon points.
        """
        if self.current_polygon_index < 0:
            return True  # No current polygon to validate

        checkbox = self.checkboxes[self.current_polygon_index]
        polygon_name = self.checkbox_names[checkbox]
        points = self.polygon_points.get(polygon_name, [])

        if len(points) > 2:
            shapely_poly = Polygon(points)
            return shapely_poly.is_valid
        return False

    def __delete_button_clicked(self):
        '''
            Deletes the last point of the current polygon
        '''
        points = self.selector.verts[:-1]
        self.selector._xys = points
        self.selector._xs, self.selector._ys = zip(*points) if points else ([], [])
        self.figure_canvas.draw_idle()

    def __apply_button_clicked(self):
        """
        apply-button callback
        """
        valid = all(self.__validate_polygon(name) for name in self.polygon_points)
        # Check if the selected polygon is valid
        if valid:
            self.ui.apply_button.setDisabled(True)

            # Save the esophagus polygon
            self.visualization_data.xray_polygon = np.array(self.polygon_points["oesophagus"], dtype=int)
            self.visualization_data.xray_image_height = self.xray_image.shape[0]
            self.visualization_data.xray_image_width = self.xray_image.shape[1]

            # Process and save masks based on checkboxes
            self.__process_and_save_masks()

            # Move to the next window
            position_selection_window = PositionSelectionWindow(
                self.master_window, self.next_window, self.patient_data,
                self.visit, self.n, self.polygon_points["oesophagus"]
            )
            self.master_window.switch_to(position_selection_window)
            self.close()
        else:
            QMessageBox.critical(self, "Error", "Please draw all polygons.")
    def __validate_polygon(self, name):
        """
        Validate a specific polygon.
        """
        points = self.polygon_points.get(name, [])
        if len(points) > 2:
            shapely_poly = Polygon(points)
            return shapely_poly.is_valid
        return False

    def __process_and_save_masks(self):
        """
        Process and save mask images based on the selected checkboxes.
        """

        safe_visit_name = self.visit.name.replace(':', '_').replace('[', '_').replace(']', '_')

        base_path = fr"C:\DataAchalasia\{safe_visit_name}\Breischluck"


        if not os.path.exists(base_path):
            os.makedirs(base_path)
        checked_count = sum(checkbox.isChecked() for checkbox in self.checkbox_names.keys())
        if checked_count > 0:
            img_filename = f"{self.visualization_data.xray_minute}.jpg"
            path = os.path.join(base_path, img_filename)
            path = os.path.normpath(path).replace("\\", "/")
            xray_image = self.xray_image.astype(np.uint8)
            cv2.imwrite(path, xray_image)
        for checkbox, polygon_name in self.checkbox_names.items():
            if checkbox.isChecked():
                polygon = self.polygon_points.get(polygon_name)
                if polygon:
                    mask_filename = f"{self.visualization_data.xray_minute}_{polygon_name}_mask.jpg"
                    self.__save_mask(polygon, base_path, mask_filename)


    def __save_mask(self, polygon, base_path, mask_filename):
        """
        Save the mask image for a given polygon.
        """
        colored_image = np.zeros((self.xray_image.shape[0], self.xray_image.shape[1]), dtype=np.uint8)
        cv2.fillPoly(colored_image, [np.array(polygon, dtype=int)], 255)
        mask_path = os.path.join(base_path, mask_filename)
        mask_path = os.path.normpath(mask_path).replace("\\", "/")
        cv2.imwrite(mask_path, colored_image)



    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_xray_region_selection_info()
        info_window.show()
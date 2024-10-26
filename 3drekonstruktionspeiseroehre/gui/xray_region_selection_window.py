import cv2
import os
import subprocess
import nibabel as nib
import numpy as np
import shutil
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
import torch



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

        # Calculate the initial polygon from the X-ray image with the nnUnet
        mask = self.predict_mask_with_nnunet_v2()
        self.mask = (mask > 0.5).astype(np.uint8) * 255
        self.polygonOes = self.mask_to_largest_polygon()
        self.init_first_polygon()

    def predict_mask_with_nnunet_v2(self):
        '''
            Uses the nnUnet for prediction of the oesophagus mask with values between 0 and 1
        '''
        os.environ['nnUNet_raw'] = "C:/ModelAchalasia/nnUNet_raw"
        os.environ['nnUNet_preprocessed'] = "C:/ModelAchalasia/nnUNet_preprocessed"
        os.environ['nnUNet_results'] = "C:/ModelAchalasia/nnUNet_results"

        temp_input_dir = 'C:/ModelAchalasia/nnUNet_raw/Dataset001_Breischluck/imagesTs'
        temp_output_dir = './temp_output_dir'
        os.makedirs(temp_output_dir, exist_ok=True)
        os.makedirs(temp_input_dir, exist_ok=True)

        input_image_path = os.path.join(temp_input_dir, '001_0000.png')
        img = Image.fromarray(self.xray_image).convert("L")
        img_array = np.array(img)
        img_array = img_array.astype(np.uint8)
        img = Image.fromarray(img_array)
        img.save(input_image_path, "PNG", compress_level=0)

        if torch.cuda.is_available():
            command = '''$Env:nnUNet_raw = "C:/ModelAchalasia/nnUNet_raw"; 
                                 $Env:nnUNet_preprocessed = "C:/ModelAchalasia/nnUNet_preprocessed"; 
                                 $Env:nnUNet_results = "C:/ModelAchalasia/nnUNet_results";
                                 nnUNetv2_predict -i C:/ModelAchalasia/nnUNet_raw/Dataset001_Breischluck/imagesTs -o ./temp_output_dir -d 1 -c 2d -tr nnUNetTrainer_100epochs -p nnUNetResEncUNetMPlans 
                              '''
        else:
            command = '''$Env:nnUNet_raw = "C:/ModelAchalasia/nnUNet_raw"; 
                                 $Env:nnUNet_preprocessed = "C:/ModelAchalasia/nnUNet_preprocessed"; 
                                 $Env:nnUNet_results = "C:/ModelAchalasia/nnUNet_results";
                                 nnUNetv2_predict -i C:/ModelAchalasia/nnUNet_raw/Dataset001_Breischluck/imagesTs -o ./temp_output_dir -d 1 -c 2d -tr nnUNetTrainer_100epochs -p nnUNetResEncUNetMPlans -device cpu 
                              '''

        subprocess.run(['powershell', '-Command', command], check=True, text=True)
        output_mask_path = os.path.join(temp_output_dir, '001.png')
        mask = np.array(Image.open(output_mask_path))

        os.remove(input_image_path)
        shutil.rmtree(temp_output_dir)

        return mask

    def mask_to_largest_polygon(self):
        '''
            If more than one contour is predicted, the largest is selected.
        '''
        contours, _ = cv2.findContours(self.mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largest_area = 0
        largest_polygon = None

        for contour in contours:
            if len(contour) >= 3:
                area = cv2.contourArea(contour)
                if area > largest_area:
                    largest_area = area
                    contour = contour.squeeze(1)

                    if not (contour[0] == contour[-1]).all():
                        contour = np.vstack([contour, contour[0]])

                    largest_polygon = Polygon(contour)

        return largest_polygon

    def init_first_polygon(self):
        # Always create the initial polygon
        color = self.polygon_colors[0]
        self.selector = PolygonSelector(self.plot_ax, self.__onselect, useblit=True, props=dict(color=color))
        self.polygon_selectors.append(self.selector)

        # Check if self.polygonOes is a Polygon object or a list of points
        if isinstance(self.polygonOes, Polygon):
            points = np.array(self.polygonOes.exterior.coords)  #extracting points
        else:
            points = self.polygonOes

        # Set the initial selection based on the number of points
        if len(points) > 2:
            self.selector.verts = points
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

        base_path = fr"C:\DataAchalasia\{safe_visit_name}"


        if not os.path.exists(base_path):
            os.makedirs(base_path)
        checked_count = sum(checkbox.isChecked() for checkbox in self.checkbox_names.keys())
        if checked_count > 0:
            img_filename = f"{self.visualization_data.xray_minute}.jpg"
            path = os.path.join(base_path, img_filename)
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
        cv2.imwrite(mask_path, colored_image)



    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_xray_region_selection_info()
        info_window.show()
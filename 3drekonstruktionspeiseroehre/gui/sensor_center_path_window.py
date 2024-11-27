from operator import itemgetter

from gui.endoscopy_selection_window import EndoscopySelectionWindow
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.visualization_window import VisualizationWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QAction
from logic.figure_creator.figure_creator import FigureCreator
import numpy as np
import cv2
import config
from PIL import Image

class SensorCenterPathWindow(QMainWindow):
    """Window where the user selects needed positions for the calculation"""

    def __init__(self, master_window: MasterWindow, next_window, patient_data: PatientData, visit: VisitData, n: int,
                 xray_polygon):
        """
        init PositionSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        """

        super().__init__()
        self.ui = uic.loadUi("./ui-files/sensor_center_path_window_design.ui", self)
        self.master_window = master_window
        self.patient_data = patient_data
        self.visualization_data = visit.visualization_data_list[n]
        self.visit = visit
        self.n = n
        self.xray_polygon = xray_polygon
        self.next_window = next_window

        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)

        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        self.figure_canvas = FigureCanvasQTAgg(Figure())
        self.ui.gridLayout.addWidget(self.figure_canvas)
        self.plot_ax = self.figure_canvas.figure.subplots()
        image = Image.open(self.visualization_data.xray_file)
        self.xray_image = np.array(image)
        self.figure_canvas.figure.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.95)
        self.plot_ax.imshow(self.xray_image)
        self.plot_ax.axis('off')

        self.add_custom_legend()

        # Draw the polygon using the xray_polygon data
        if self.xray_polygon:
            poly = Polygon(self.xray_polygon, closed=True, fill=None, edgecolor='lime', linewidth=1)
            self.plot_ax.add_patch(poly)

        mask = np.zeros((self.visualization_data.xray_image_height, self.visualization_data.xray_image_width))
        # parameter for drawContours: outputArray, inputArray, contourIdx (-1 means all contours),
        # color (1 means white), thickness (thickness -1 means the areas bounded by the contours is filled)
        cv2.drawContours(mask, [np.array(self.visualization_data.xray_polygon)], -1, 1, -1)
        self.visualization_data.xray_mask = mask

        if self.visualization_data.sensor_path is not None:
            # If sensor path was created and/or adapted use that one
            self.cal_sensor_path = self.visualization_data.sensor_path
            print("TEST WHEN ACTIVATED")
        else:
            # Calculate a path through the esophagus along the xray image (sensor path)
            self.cal_sensor_path = FigureCreator.calculate_shortest_path_through_esophagus(self.visualization_data)

        # Calculate center path
        self.cal_widths, self.cal_centers, self.cal_slopes, self.cal_offset_top = FigureCreator.calculate_widths_centers_slope_offset(self.visualization_data, self.cal_sensor_path)
        self.cal_centers = np.array(self.cal_centers)

        # Visualize sensor/center path as colored Line
        self.sens_drawn = Line2D(self.cal_sensor_path[:,1], self.cal_sensor_path[:,0], color='orange')
        self.center_drawn = Line2D(self.cal_centers[:, 1], self.cal_centers[:, 0], color='blue')
        self.plot_ax.add_line(self.center_drawn)
        self.plot_ax.add_line(self.sens_drawn)

        self.center_path = [(yx[1], yx[0]) for yx in self.cal_centers]  # In format [(x,y)]
        self.x_coords, self.y_coords = zip(*self.center_path)
        self.x_coords = np.array(self.x_coords)[::15]
        self.y_coords = np.array(self.y_coords)[::15]

        self.line = Line2D(self.x_coords, self.y_coords, color="red", marker="o", markersize=4)
        self.plot_ax.add_line(self.line)

        # Make visualized center path adaptable for user
        # self.selector = PolygonSelector(self.plot_ax, self.__onselect, useblit=True, props=dict(color='red'))
        # self.selector.verts = self.center_path[::15]

        self.dragging_point = None
        self.figure_canvas.mpl_connect("button_press_event", self.on_press)
        self.figure_canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.figure_canvas.mpl_connect("button_release_event", self.on_release)
        self.figure_canvas.draw()

    def on_press(self, event):
        if event.inaxes != self.plot_ax:
            return
        # Check if the click is near a point of the line
        for i, (x, y) in enumerate(zip(self.line.get_xdata(), self.line.get_ydata())):
            if abs(x - event.xdata) < 4 and abs(y - event.ydata) < 4:
                self.dragging_point = i
                break

    def on_motion(self, event):
        if self.dragging_point is None or event.inaxes != self.plot_ax:
            return
        # Update the position of the dragged point
        xdata, ydata = list(self.line.get_xdata()), list(self.line.get_ydata())
        xdata[self.dragging_point] = event.xdata
        ydata[self.dragging_point] = event.ydata
        self.line.set_data(xdata, ydata)
        self.figure_canvas.draw()

    def on_release(self, event):
        self.dragging_point = None

    def add_custom_legend(self):
        """Add a custom legend to the existing window layout."""
        # Create a container widget for the legend
        legend_widget = QWidget()
        legend_layout = QVBoxLayout()  # Vertical layout for stacking legend items
        legend_widget.setLayout(legend_layout)
        legend_widget.setFixedWidth(150)

        # Helper function to create legend items
        def create_legend_item(color, text):
            item_layout = QHBoxLayout()
            color_box = QFrame()
            color_box.setFixedSize(20, 20)
            color_box.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
            label = QLabel(text)
            item_layout.addWidget(color_box)
            item_layout.addWidget(label)
            item_layout.addStretch()  # Push label to the left
            return item_layout

        # Add legend items
        legend_layout.addLayout(create_legend_item("orange", "Sensor Path"))
        legend_layout.addLayout(create_legend_item("blue", "Original Center Path"))
        legend_layout.addLayout(create_legend_item("red", "Editable Center Path"))

        # Add the legend widget to the existing layout
        self.ui.legendLayout.addWidget(legend_widget, 0, 1)

    def __onselect(self, verts):
        """
        called when new polygon was created
        :param polygon: new polygon
        """
        self.center_path = verts

    def __reset_button_clicked(self):
        """
        reset-button callback
        """
        self.__reset_selector()

    def __reset_selector(self):
        """
        starts the selection of a new polygon/resets the polygon selector
        """
        self.selector._xs, self.selector._ys = [], []
        self.selector._xys = [(0, 0)]
        self.center_path.clear()
        self.selector.clear()
        self.selector._selection_completed = False
        self.selector.set_visible(True)

    def __apply_button_clicked(self):
        """
        apply-button callback
        """
        x_data, y_data = list(self.line.get_xdata()), list(self.line.get_ydata())
        self.center_path = list(zip(x_data, y_data))
        # PROBLEM: when we manually select a center_path the slopes, widths, etc. don't match anymore
        # Save the new center path in the visualization_data
        if len(self.center_path) > 2:
            if len(self.center_path) < len(self.cal_centers):
                self.visualization_data.center_path = FigureCreator.interpolate_path(path=self.center_path, number=len(self.cal_centers))
            elif len(self.center_path) > len(self.cal_centers):
                factor = len(self.center_path) / len(self.cal_centers)
                indices = np.arange(0, len(self.center_path), factor, dtype=int)
                self.visualization_data.center_path = self.center_path[indices]
            else:
                self.visualization_data.center_path = self.center_path
        self.visualization_data.center_path = np.array([(yx[1], yx[0]) for yx in self.visualization_data.center_path], dtype=np.int32)
        #self.cal_widths, _, self.cal_slopes, self.cal_offset_top = FigureCreator.calculate_widths_centers_slope_offset(
        #    self.visualization_data, self.visualization_data.center_path)

        self.visualization_data.widths = self.cal_widths
        self.visualization_data.slopes = self.cal_slopes
        self.visualization_data.offset = self.cal_offset_top
        self.visualization_data.sensor_path = np.array(self.cal_sensor_path, dtype=np.int32)

        esophagus_full_length_px = FigureCreator.calculate_esophagus_length_px(self.visualization_data.sensor_path, 0,
                                                                               self.visualization_data.esophagus_exit_pos)
        esophagus_full_length_cm = FigureCreator.calculate_esophagus_full_length_cm(self.visualization_data.sensor_path,
                                                                                    esophagus_full_length_px,
                                                                                    self.visualization_data)
        self.visualization_data.esophagus_len = esophagus_full_length_cm
        # v * mean(timeframe) ; v/mean(timeframe)
        # pro time frame min max mean vom Druck
        # summe über alle Metriken (gemittelt)
        # maximaler Ausschlag

        self.cm_to_px_ratio = esophagus_full_length_cm / esophagus_full_length_px

        """
        volume = self.volume_checker()
        if volume:
            reply = QMessageBox.warning(self, 'Warning', f"The estimated volume is outside the check boundary: {volume} ({config.volumen_lower_boundary}, {config.volumen_upper_boundary}).\nThis might be caused by a mapping/calculation error.\nDo you really want to proceed?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return  # Exit the method if the user chooses not to proceed
        """

        length = self.length_checker()
        if length:
            reply = QMessageBox.warning(self, 'Warning',
                                        f"The estimated length of the Esophagus is outside the check boundary: {length} ({config.max_eso_length}, {config.min_eso_length}).\nThis might be caused by a mapping/calculation error.\nDo you really want to proceed?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return  # Exit the method if the user chooses not to proceed

        # If there are more visualizations in this visit continue with the next xray selection
        if self.next_window:
            self.master_window.switch_to(self.next_window)
        # Handle Endoscopy annotation
        elif len(self.visualization_data.endoscopy_files) > 0:
            endoscopy_selection_window = EndoscopySelectionWindow(self.master_window,
                                                                  self.patient_data, self.visit)
            self.master_window.switch_to(endoscopy_selection_window)
            self.close()
        # Else show the visualization
        else:
            # Add new visit to patient data
            self.patient_data.add_visit(self.visit.name, self.visit)
            visualization_window = VisualizationWindow(self.master_window, self.patient_data)
            self.master_window.switch_to(visualization_window)
            self.close()

    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_sensor_center_path_info()
        info_window.show()

    def volume_checker(self):
        # NOT USED RIGHT NOW
        widths = np.array(self.visualization_data.widths)
        volumen_ready = (((widths * self.cm_to_px_ratio) / 2) ** 2) * np.pi
        volumen = np.sum(volumen_ready)
        if config.volumen_upper_boundary < volumen or volumen < config.volumen_lower_boundary:
            return volumen
        return None

    def length_checker(self):
        exact_length = FigureCreator.calculate_esophagus_exact_length(self.visualization_data.center_path, self.cm_to_px_ratio)
        if exact_length > config.max_eso_length or exact_length < config.min_eso_length:
            return exact_length
        return None
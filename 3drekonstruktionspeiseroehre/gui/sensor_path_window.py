from operator import itemgetter

from gui.endoscopy_selection_window import EndoscopySelectionWindow
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.sensor_center_path_window import SensorCenterPathWindow
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
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtGui import QAction
from logic.figure_creator.figure_creator import FigureCreator
import numpy as np
import cv2
import config
from PIL import Image


class SensorPathWindow(QMainWindow):
    """Window where the user selects needed positions for the calculation"""

    def __init__(self, master_window: MasterWindow, next_window, patient_data: PatientData, visit: VisitData, n: int,
                 xray_polygon):
        """
        init PositionSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        """

        super().__init__()
        self.ui = uic.loadUi("./ui-files/sensor_path_window_design.ui", self)
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

        # Draw the polygon using the xray_polygon data
        if self.xray_polygon:
            poly = Polygon(self.xray_polygon, closed=True, fill=None, edgecolor='lime', linewidth=1)
            self.plot_ax.add_patch(poly)

        mask = np.zeros((self.visualization_data.xray_image_height, self.visualization_data.xray_image_width))
        # parameter for drawContours: outputArray, inputArray, contourIdx (-1 means all contours),
        # color (1 means white), thickness (thickness -1 means the areas bounded by the contours is filled)
        cv2.drawContours(mask, [np.array(self.visualization_data.xray_polygon)], -1, 1, -1)
        self.visualization_data.xray_mask = mask

        # Calculate a path through the esophagus along the xray image (sensor path)
        self.cal_sensor_path = FigureCreator.calculate_shortest_path_through_esophagus(self.visualization_data)

        # Visualize sensor/center path as colored Line
        self.sens_drawn = Line2D(self.cal_sensor_path[:, 1], self.cal_sensor_path[:, 0], color='blue')
        self.plot_ax.add_line(self.sens_drawn)

        self.sensor_path = [(yx[1], yx[0]) for yx in self.cal_sensor_path] # In format [(x,y)]
        self.x_coords, self.y_coords = zip(*self.sensor_path)
        self.x_coords = np.array(self.x_coords)[::15]
        self.y_coords = np.array(self.y_coords)[::15]

        self.line = Line2D(self.x_coords, self.y_coords, color="red", marker="o", markersize=4)
        self.plot_ax.add_line(self.line)

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

    def __onselect(self, verts):
        """
        called when new polygon was created
        :param polygon: new polygon
        """
        self.sensor_path = verts

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
        self.sensor_path.clear()
        self.selector.clear()
        self.selector._selection_completed = False
        self.selector.set_visible(True)

    def __apply_button_clicked(self):
        """
        apply-button callback
        """
        x_data, y_data = list(self.line.get_xdata()), list(self.line.get_ydata())
        self.sensor_path = list(zip(x_data, y_data))
        # PROBLEM: when we manually select a center_path the slopes, widths, etc. don't match anymore
        # Save the new center path in the visualization_data
        if len(self.sensor_path) > 2:
            if len(self.sensor_path) < len(self.cal_sensor_path):
                self.visualization_data.sensor_path = FigureCreator.interpolate_path(path=self.sensor_path,
                                                                                            number=len(
                                                                                                self.cal_sensor_path))
            elif len(self.sensor_path) > len(self.cal_sensor_path):
                factor = len(self.sensor_path) / len(self.cal_sensor_path)
                indices = np.arange(0, len(self.sensor_path), factor, dtype=int)
                self.visualization_data.sensor_path = self.sensor_path[indices]
            else:
                self.visualization_data.sensor_path = self.sensor_path
        self.visualization_data.sensor_path = np.array([(yx[1], yx[0]) for yx in self.visualization_data.sensor_path],
                                                       dtype=np.int32)

        # Go to center_path visualization
        sensor_center_path_window = SensorCenterPathWindow(self.master_window, self.next_window,
                                                           self.patient_data, self.visit, self.n,
                                                           self.xray_polygon)
        self.master_window.switch_to(sensor_center_path_window)
        self.close()

    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_sensor_path_info()
        info_window.show()


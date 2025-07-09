from matplotlib.lines import Line2D
from gui.master_window import MasterWindow
from gui.base_workflow_window import BaseWorkflowWindow
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QRadioButton, QCheckBox
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from gui.rectangle_selector import CustomRectangleSelector
from PyQt6 import uic
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtGui import QAction
from gui.draggable_horizontal_line import DraggableHorizontalLine, DraggableLineManager
from gui.info_window import InfoWindow
from gui.xray_window_managment import ManageXrayWindows
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import config
from scipy.interpolate import RectBivariateSpline
import numpy as np
import cv2


class DCISelectionWindow(BaseWorkflowWindow):
    """Window where the user selects the rectangle for the EPI calculation and the LES and UES positions"""

    next_window = None

    def __init__(
        self, master_window: MasterWindow, patient_data: PatientData, visit: VisitData
    ):
        """
        init DciSelectionWindow
        :param master_window: the FlexibleWindow in which the next window will be displayed
        :param patient_data: the patient data
        :param visit: the visit data
        """

        super().__init__(master_window, patient_data, visit, None)
        self.ui = uic.loadUi("./ui-files/dci_selection_window_design.ui", self)
        self.master_window.maximize()

        # Store visit reference for access in methods
        self.visit = visit
        self.patient_data = patient_data
        self.visualization_data = visit.visualization_data_list[0]

        # Ensure apply button is enabled after navigation
        if hasattr(self.ui, "apply_button"):
            self.ui.apply_button.setEnabled(True)

        self.rectangle = None
        self.pressure_matrix_high_res = None

        self.figure_canvas = None
        self.connection_ids = []

        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Select the region for the Esophageal Pressure Index")
        self.lower_ues, self.lower_les, self.upper_les, self.selector = (
            None,
            None,
            None,
            None,
        )
        self.relation_x_y, self.goal_relation = None, None

        sensor_names = [
            "P" + str(len(config.coords_sensors) - i)
            for i in range(len(config.coords_sensors))
        ]
        self.ui.first_combobox.addItems(sensor_names)
        self.ui.second_combobox.addItems(sensor_names)

        # Access the radio buttons
        self.radioButton20mmHg = self.findChild(QRadioButton, "radioButton20mmHg")
        self.radioButton0mmHg = self.findChild(QRadioButton, "radioButton0mmHg")

        # Access checkbox for selector
        self.selector_checkbox = self.findChild(QCheckBox, "checkBoxDecouple")

        # set checkbox to checked
        self.selector_checkbox.setChecked(True)
        self.selectorIsCoupled = True

        # Preselect the 20 mmHg radio button
        self.radioButton20mmHg.setChecked(True)
        self.radioButton0mmHg.setChecked(False)
        self.is_20mmHg_selected = True

        # Connect signals to slots if needed
        self.radioButton20mmHg.toggled.connect(self.__on_radio_button_toggled)
        self.radioButton0mmHg.toggled.connect(self.__on_radio_button_toggled)
        self.selector_checkbox.toggled.connect(self.__on_checkbox_toggled)

        # Connect button click events to methods
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        # Create a menu button for displaying the Info-Window
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        # Setup navigation buttons after UI is loaded
        self._setup_navigation_buttons()

        self.goal_relation = 16 / 9
        self.__plot_data()

    def __on_checkbox_toggled(self):
        """
        Callback function that is called when the user toggles the checkbox
        """
        if self.selector_checkbox.isChecked():
            self.selectorIsCoupled = True
            self.__couple_selector()
        else:
            self.selectorIsCoupled = False

    def __on_radio_button_toggled(self):
        """
        Callback function that is called when the user toggles the radio buttons
        """
        if self.radioButton20mmHg.isChecked():
            self.is_20mmHg_selected = True
        elif self.radioButton0mmHg.isChecked():
            self.is_20mmHg_selected = False
        self.__update_DCI_value(
            int(self.selector.extents[0]),
            int(self.selector.extents[1]),
            int(self.selector.extents[2]),
            int(self.selector.extents[3]),
        )

    def __update_DCI_value(self, x1, x2, y1, y2):
        """
        Update the DCI value based on the selected rectangle
        :param x1: the x-coordinate of the lower left corner of the rectangle
        :param x2: the x-coordinate of the upper right corner of the rectangle
        :param y1: the y-coordinate of the lower left corner of the rectangle
        :param y2: the y-coordinate of the upper right corner of the rectangle
        """
        # Extract the selected data
        selected_data = self.pressure_matrix_high_res[y1:y2, x1:x2]

        height_in_cm = (
            selected_data.shape[0]
            / self.pressure_matrix_high_res.shape[0]
            * np.sort(config.coords_sensors)[-1]
        )
        time_in_s = (
            selected_data.shape[1]
            / self.pressure_matrix_high_res.shape[1]
            * (
                self.visualization_data.pressure_matrix.shape[1]
                / config.csv_values_per_second
            )
        )

        dci_value = self.calculateDCI(selected_data, height_in_cm, time_in_s)
        les_height = self.get_les_height()
        esophagus_length = self.get_esophagus_length()
        self.figure_canvas.draw()
        self.ui.DCI.setText(f"{dci_value} mmHg·s·cm")
        self.ui.heightLabelLES.setText(f"{les_height} cm")
        self.ui.heightLabelEsophagus.setText(f"{esophagus_length} cm")

    def __onselect(self, eclick, erelease):
        """
        Callback function that is called when the user selects a rectangle in the plot
        :param eclick: the press event
        :param erelease: the release event
        """
        # eclick and erelease are the press and release events
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        self.__update_DCI_value(x1, x2, y1, y2)

    def get_les_height(self):
        """
        Calculate the height of the Lower Esophageal Sphincter (LES) based on the upper and lower LES.
        :return: the height of the LES in cm
        """
        return np.round(
            (self.lower_les.get_y_position() - self.upper_les.get_y_position())
            * np.sort(config.coords_sensors)[-1]
            / self.pressure_matrix_high_res.shape[0],
            2,
        )

    def get_esophagus_length(self):
        """
        Calculate the length of the tubular esophagus based on the upper les and lower ues.
        :return: the length of the tubular esophagus in cm
        """
        return np.round(
            (self.upper_les.get_y_position() - self.lower_ues.get_y_position())
            * np.sort(config.coords_sensors)[-1]
            / self.pressure_matrix_high_res.shape[0],
            2,
        )

    def __couple_selector(self):
        """
        Couple the rectangle selector with the LES and UES lines
        """
        self.selectorIsCoupled = True
        self.selector.extents = (
            self.selector.extents[0],
            self.selector.extents[1],
            self.lower_ues.get_y_position(),
            self.upper_les.get_y_position(),
        )
        self.selector.update()
        self.__update_DCI_value(
            int(self.selector.extents[0]),
            int(self.selector.extents[1]),
            int(self.selector.extents[2]),
            int(self.selector.extents[3]),
        )

    def on_lines_dragged(self):
        """
        Callback function that is called when the user drags the lines of the LES and UES (updates the DCI value, les height, and length of tubular esophagus)
        """
        # Get the current positions of the upper_les and lower_ues lines
        upper_les_y = self.upper_les.get_y_position()
        lower_ues_y = self.lower_ues.get_y_position()
        lower_les_y = self.lower_les.get_y_position()

        if (
            upper_les_y
            <= lower_ues_y
            + 1
            * self.pressure_matrix_high_res.shape[0]
            / np.sort(config.coords_sensors)[-1]
        ):  # length of tubular esophagus must be at least 1 cm
            self.upper_les.set_y_position(self.upper_les_backup)
            self.lower_ues.set_y_position(self.lower_ues_backup)
            return
        elif (
            upper_les_y
            >= lower_les_y
            - 0.5
            * self.pressure_matrix_high_res.shape[0]
            / np.sort(config.coords_sensors)[-1]
        ):  # les must have a minimum height of 0.5 cm
            self.upper_les.set_y_position(self.upper_les_backup)
            self.lower_les.set_y_position(self.lower_les_backup)
            return
        elif (
            lower_ues_y
            >= lower_les_y
            - 0.5
            * self.pressure_matrix_high_res.shape[0]
            / np.sort(config.coords_sensors)[-1]
        ):  # should never happen since upper_les is always above lower_les
            self.lower_ues.set_y_position(self.lower_ues_backup)
            self.lower_les.set_y_position(self.lower_les_backup)
            return

        if (
            self.lower_ues != self.lower_ues_backup
            or self.upper_les != self.upper_les_backup
        ) and self.selectorIsCoupled:  # update the DCI value if rectangle selector is changed
            self.__couple_selector()

        # Update the labels
        les_height = self.get_les_height()
        esophagus_length = self.get_esophagus_length()
        self.ui.heightLabelLES.setText(f"{les_height} cm")
        self.ui.heightLabelEsophagus.setText(f"{esophagus_length} cm")
        self.lower_les_backup = lower_les_y
        self.upper_les_backup = upper_les_y
        self.lower_ues_backup = lower_ues_y
        first_sensor_pos = self.find_first_sensor_below_ues()
        self.ui.first_combobox.setCurrentIndex(first_sensor_pos)
        self.visualization_data.first_sensor_index = first_sensor_pos
        second_sensor_pos = self.find_middle_sensor_in_les()
        self.ui.second_combobox.setCurrentIndex(second_sensor_pos)
        self.visualization_data.second_sensor_index = second_sensor_pos

    def connect_events(self):
        self.connection_ids.append(
            self.fig.canvas.mpl_connect(
                "motion_notify_event", self.line_manager.on_hover
            )
        )
        self.connection_ids.append(
            self.fig.canvas.mpl_connect(
                "button_press_event", self.line_manager.on_press
            )
        )
        self.connection_ids.append(
            self.fig.canvas.mpl_connect(
                "button_release_event", self.line_manager.on_release
            )
        )
        self.connection_ids.append(
            self.fig.canvas.mpl_connect(
                "motion_notify_event", self.line_manager.on_motion
            )
        )

    def disconnect_events(self):
        for cid in self.connection_ids:
            self.fig.canvas.mpl_disconnect(cid)
        self.connection_ids.clear()

    def __initialize_plot_analysis(self):
        """
        Initialize the plot analysis by creating the rectangle selector, the upper LES, lower LES, and lower UES lines, and the DCI value label
        """
        # Create a polygon selector for user interaction
        self.selector = CustomRectangleSelector(
            self.ax,
            self.__onselect,
            useblit=True,
            props=dict(
                facecolor=(1, 0, 0, 0), edgecolor="white", linewidth=1.5, linestyle="-"
            ),
            interactive=True,
            ignore_event_outside=True,
            use_data_coordinates=True,
        )

        if self.lower_ues is not None:
            self.lower_ues.line.remove()
        if self.upper_les is not None:
            self.upper_les.line.remove()
        if self.lower_les is not None:
            self.lower_les.line.remove()
        upper_les = self.find_boundary(region="LES_upper")
        lower_ues = self.find_boundary(region="UES_lower")
        lower_les = self.find_boundary(region="LES_lower")

        left_end, right_end = self.find_biggest_connected_region(lower_ues, upper_les)

        self.selector.extents = (left_end, right_end, lower_ues, upper_les)
        self.line_manager = DraggableLineManager(self.fig.canvas)
        self.lower_les = DraggableHorizontalLine(
            self.ax.axhline(y=lower_les, color="r", linewidth=1.5, picker=2),
            label="LES (L)",
            color="red",
            callback=self.on_lines_dragged,
        )
        self.lower_ues = DraggableHorizontalLine(
            self.ax.axhline(y=lower_ues, color="r", linewidth=1.5, picker=2),
            label="UES",
            color="blue",
            callback=self.on_lines_dragged,
        )
        self.upper_les = DraggableHorizontalLine(
            self.ax.axhline(y=upper_les, color="r", linewidth=1.5, picker=2),
            label="LES (U)",
            color="black",
            callback=self.on_lines_dragged,
        )
        self.line_manager.add_line(self.lower_les)
        self.line_manager.add_line(self.lower_ues)
        self.line_manager.add_line(self.upper_les)
        legend_handles = [
            Line2D([0], [0], color=line.color, lw=2, linestyle="-")
            for line in self.line_manager.lines
        ]
        legend_labels = [line.label for line in self.line_manager.lines]
        self.ax.legend(
            legend_handles,
            legend_labels,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.1),
            ncol=len(self.line_manager.lines),
        )
        self.connect_events()
        self.__update_DCI_value(left_end, right_end, lower_ues, upper_les)
        first_sensor_pos = self.find_first_sensor_below_ues()
        second_sensor_pos = self.find_middle_sensor_in_les()
        self.ui.second_combobox.setCurrentIndex(second_sensor_pos)
        self.ui.first_combobox.setCurrentIndex(first_sensor_pos)
        self.visualization_data.first_sensor_index = first_sensor_pos
        self.visualization_data.second_sensor_index = second_sensor_pos
        self.lower_les_backup = lower_les
        self.upper_les_backup = upper_les
        self.lower_ues_backup = lower_ues

    def remove_rectangle_selector(self):
        if self.selector:
            self.selector.set_active(False)  # Deactivate the selector
            self.selector.disconnect_events()  # Disconnect event handlers
            if hasattr(self.selector, "artists"):
                for artist in self.selector.artists:
                    artist.remove()  # Remove all artists (rectangle, handles, etc.)
            self.selector = None  # Remove the reference to the selector
            self.fig.canvas.draw_idle()  # Redraw the canvas to reflect the changes

    def __reset_button_clicked(self):
        """
        reset-button callback
        """
        self.remove_rectangle_selector()
        self.disconnect_events()
        self.__initialize_plot_analysis()

    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_dci_selection_info()
        info_window.show()

    def __generate_estimated_pressure_matrix(
        self, first_sensor, last_sensor, min_gap, number_of_measurements, coords_sensors
    ):
        """
        Generate an estimated pressure matrix by interpolating the pressure values between the sensors
        :param first_sensor: the position of the first sensor
        :param last_sensor: the position of the last sensor
        :param min_gap: the minimum gap between the sensors
        :param number_of_measurements: the number of measurements
        :param coords_sensors: the coordinates of the sensors
        :return: the estimated pressure matrix
        """
        estimated_pressure_matrix = np.zeros(
            ((last_sensor - first_sensor) // min_gap + 1, number_of_measurements)
        )
        for i in range(number_of_measurements):
            sensor_counter = 0
            for position in range(first_sensor, last_sensor + 1, min_gap):
                if position in coords_sensors:
                    estimated_pressure_matrix[
                        (position - first_sensor) // min_gap, i
                    ] = self.visualization_data.pressure_matrix[sensor_counter, i]
                    sensor_counter += 1
                else:
                    value_before = self.visualization_data.pressure_matrix[
                        sensor_counter - 1, i
                    ]
                    value_after = self.visualization_data.pressure_matrix[
                        sensor_counter, i
                    ]
                    estimated_pressure_matrix[
                        (position - first_sensor) // min_gap, i
                    ] = (
                        (position - coords_sensors[sensor_counter - 1]) * value_after
                        + (coords_sensors[sensor_counter] - position) * value_before
                    ) / (
                        coords_sensors[sensor_counter]
                        - coords_sensors[sensor_counter - 1]
                    )
        return estimated_pressure_matrix

    def __interpolate_pressure_matrix(self, estimated_pressure_matrix):
        """
        Interpolate the pressure matrix to a higher resolution
        :param estimated_pressure_matrix: the estimated pressure matrix
        :return: the interpolated pressure matrix in higher resolution
        """
        y = np.arange(estimated_pressure_matrix.shape[0])
        x = np.arange(estimated_pressure_matrix.shape[1])

        # Create the spline interpolator
        spline = RectBivariateSpline(
            y, x, estimated_pressure_matrix
        )  # Bicubic interpolation

        # Define higher resolution grid
        xnew = np.linspace(
            0,
            estimated_pressure_matrix.shape[1] - 1,
            estimated_pressure_matrix.shape[1] * 10,
        )
        ynew = np.linspace(
            0,
            estimated_pressure_matrix.shape[0] - 1,
            int(
                np.floor(
                    estimated_pressure_matrix.shape[0]
                    * 10
                    * self.relation_x_y
                    / self.goal_relation
                )
            ),
        )
        return spline(ynew, xnew)

    def __plot_data(self):
        """
        Create the visualization plot of the pressure matrix and initialize the plot analysis (rectangle selector, upper LES, lower LES, lower UES, etc.)
        """
        number_of_measurements = len(self.visualization_data.pressure_matrix[1])

        # Define the colors and positions for the color map
        colors = [
            (16 / 255, 1 / 255, 255 / 255),
            (5 / 255, 252 / 255, 252 / 255),
            (19 / 255, 254 / 255, 3 / 255),
            (252 / 255, 237 / 255, 3 / 255),
            (255 / 255, 0 / 255, 0 / 255),
            (91 / 255, 5 / 255, 132 / 255),
        ]
        positions = [0, 0.123552143573761, 0.274131298065186, 0.5, 0.702702701091766, 1]

        # Create the color map
        cmap = LinearSegmentedColormap.from_list(
            "custom_cmap", list(zip(positions, colors))
        )

        # approximate values between sensors in equal distances
        coords_sensors = np.sort(
            config.coords_sensors
        )  # sort the sensor positions if not already sorted
        min_gap = np.gcd.reduce(
            np.diff(coords_sensors)
        )  # assumption, that there is only one sensor at each position
        first_sensor = coords_sensors[0]  # start at the first sensor (min value)
        last_sensor = coords_sensors[-1]  # max value

        estimated_pressure_matrix = self.__generate_estimated_pressure_matrix(
            first_sensor, last_sensor, min_gap, number_of_measurements, coords_sensors
        )

        self.relation_x_y = (
            estimated_pressure_matrix.shape[1] / estimated_pressure_matrix.shape[0]
        )
        pressure_matrix_high_res = self.__interpolate_pressure_matrix(
            estimated_pressure_matrix
        )
        self.pressure_matrix_high_res = pressure_matrix_high_res

        im = self.ax.imshow(
            pressure_matrix_high_res,
            cmap=cmap,
            interpolation="nearest",
            vmin=config.cmin,
            vmax=config.cmax,
        )

        # Calculate the time for each measurement
        time = (
            np.arange(0, estimated_pressure_matrix.shape[1])
            / config.csv_values_per_second
        )

        # Set the tick labels
        x_ticks = np.linspace(
            0,
            pressure_matrix_high_res.shape[1],
            len(time) // int(np.ceil(10 * self.relation_x_y / self.goal_relation)) + 1,
        )
        y_ticks = np.linspace(
            0,
            pressure_matrix_high_res.shape[0],
            estimated_pressure_matrix.shape[0] // 10 + 1,
        )
        self.ax.set_xticks(x_ticks)
        self.ax.set_yticks(y_ticks)
        self.ax.set_xticklabels(
            np.round(
                time[:: int(np.ceil(10 * self.relation_x_y / self.goal_relation))], 1
            )
        )  # Display only every 10th time point, rounded to 1 decimal place
        self.ax.set_yticklabels(
            np.arange(0, estimated_pressure_matrix.shape[0] + 1, 10)
        )

        self.fig.colorbar(im, ax=self.ax, label="Pressure (mmHg·s·cm)")
        self.ax.set_ylabel("Height along esophagus (cm)")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_xlim(0, pressure_matrix_high_res.shape[1])
        self.ax.set_ylim(pressure_matrix_high_res.shape[0], 0)

        self.figure_canvas = FigureCanvasQTAgg(figure=self.fig)
        self.ui.gridLayout.addWidget(self.figure_canvas)

        plt.contour(
            self.pressure_matrix_high_res > 30,
            levels=[0.5],
            colors="k",
            linestyles="solid",
            linewidths=0.3,
        )  # threshold for the contour plot is 30 mmHg

        # Plot small dots at the coordinates of the sensors
        min_coord = min(config.coords_sensors)
        max_coord = max(config.coords_sensors)
        for i, coord in enumerate(config.coords_sensors):
            x = self.pressure_matrix_high_res.shape[1] - 10
            # Normalize coord to the range of the pressure_matrix_high_res height
            y = (
                (coord - min_coord)
                / (max_coord - min_coord)
                * (self.pressure_matrix_high_res.shape[0] - 1)
            )
            y = int(np.ceil(y))
            self.ax.plot(
                x, y, "ro", markersize=4
            )  # 'ro' means red color, circle marker
            self.ax.annotate(
                f"P{len(config.coords_sensors) - i}",
                (x, y),
                textcoords="offset points",
                xytext=(5, -4),
                ha="left",
            )
        self.figure_canvas.draw()
        self.__initialize_plot_analysis()

    def __apply_button_clicked(self):
        """
        apply-button callback
        """
        for i in range(len(self.visit.visualization_data_list)):
            self.visit.visualization_data_list[i].sphincter_length_cm = (
                self.get_les_height()
            )
        if (
            self.ui.first_combobox.currentIndex()
            != self.ui.second_combobox.currentIndex()
        ):
            if (
                self.ui.first_combobox.currentIndex()
                > self.ui.second_combobox.currentIndex()
            ):
                for i in range(len(self.visit.visualization_data_list)):
                    self.visit.visualization_data_list[i].first_sensor_index = (
                        self.ui.first_combobox.currentIndex()
                    )
                    self.visit.visualization_data_list[i].second_sensor_index = (
                        self.ui.second_combobox.currentIndex()
                    )
            else:
                for i in range(len(self.visit.visualization_data_list)):
                    self.visit.visualization_data_list[i].first_sensor_index = (
                        self.ui.second_combobox.currentIndex()
                    )
                    self.visit.visualization_data_list[i].second_sensor_index = (
                        self.ui.first_combobox.currentIndex()
                    )
        else:
            QMessageBox.critical(self, "Error", "Please select two different sensors.")
        for i in range(len(self.visit.visualization_data_list)):
            self.visit.visualization_data_list[i].esophageal_pressurization_index = (
                float(self.ui.DCI.text().split()[0])
            )
        ManageXrayWindows(self.master_window, self.visit, self.patient_data)

    def calculateDCI(self, pressure_matrix, height, time):
        """
        calculates the DCI value of the selected rectangle
        :param pressure_matrix: the pressure matrix of the selected rectangle
        :param height: the height of the selected rectangle
        :param time: the time span of the selected rectangle
        :return: the DCI value
        """
        # Create a mask of all values above 20 mmHg
        mask = pressure_matrix > 20

        mean_pressure = 0
        if self.is_20mmHg_selected:
            if len(pressure_matrix[mask]) != 0:
                # Calculate the mean of these values
                mean_pressure = np.mean(np.maximum(pressure_matrix - 20, 0))
        else:
            if len(pressure_matrix) != 0:
                # Calculate the mean of these values
                mean_pressure = np.mean(pressure_matrix)
        return np.round(mean_pressure * height * time, 2)

    def find_largest_stripe(self, binary_matrix, region_start, region_end):
        """
        Finds the largest connected stripe in the given binary matrix region.
        """
        region = binary_matrix[region_start:region_end]
        contours, _ = cv2.findContours(
            region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None, None
        best_contour = max(contours, key=cv2.contourArea)
        _, y, _, h = cv2.boundingRect(best_contour)
        return y + region_start, h  # Adjust for offset

    def find_sobel_edge(self, binary_matrix, region_start, region_end, edge_type):
        """
        Detects the strongest gradient edge using Sobel filtering.
        """
        sobel_y = cv2.Sobel(binary_matrix, cv2.CV_64F, dx=0, dy=1, ksize=3)
        if edge_type == "upper":
            return region_start + np.argmax(
                sobel_y[region_start:region_end].sum(axis=1)
            )
        else:  # "lower"
            return region_start + np.argmin(
                sobel_y[region_start:region_end].sum(axis=1)
            )

    def find_boundary(self, threshold=30, min_percentage=0.3, region="UES_lower"):
        """
        General function to detect boundaries of UES and LES stripes.
        """
        height = self.pressure_matrix_high_res.shape[0]
        binary_matrix = (self.pressure_matrix_high_res > threshold).astype(
            np.uint8
        ) * 255

        if region == "UES_lower":
            region_start, region_end, edge_type, default = (
                0,
                height // 2,
                "lower",
                int(0.05 * height),
            )
        elif region == "LES_upper":
            region_start, region_end, edge_type, default = (
                height // 2,
                height,
                "upper",
                int(0.75 * height),
            )
        elif region == "LES_lower":
            region_start, region_end, edge_type, default = (
                height // 2,
                height,
                "lower",
                int(0.95 * height),
            )
        else:
            raise ValueError("Invalid region specified.")

        y, h = self.find_largest_stripe(binary_matrix, region_start, region_end)
        if y is None:
            return default

        sobel_edge_y = self.find_sobel_edge(
            binary_matrix, region_start, region_end, edge_type
        )

        if edge_type == "upper":
            for row in range(y, y + h):
                if (
                    np.sum(self.pressure_matrix_high_res[row] > threshold)
                    / self.pressure_matrix_high_res.shape[1]
                    >= min_percentage
                ):
                    largest_stripe_start = row
                    break
            else:
                largest_stripe_start = y
            return (
                sobel_edge_y if y <= sobel_edge_y <= (y + h) else largest_stripe_start
            )

        else:  # "lower"
            for row in range(y + h - 1, y - 1, -1):
                if (
                    np.sum(self.pressure_matrix_high_res[row] > threshold)
                    / self.pressure_matrix_high_res.shape[1]
                    >= min_percentage
                ):
                    largest_stripe_end = row
                    break
            else:
                largest_stripe_end = y + h
            return sobel_edge_y if y <= sobel_edge_y <= (y + h) else largest_stripe_end

    def find_biggest_connected_region(self, lower_ues, upper_les, threshold=30):
        """
        Find the biggest connected region of high pressure between UES and LES using contour detection.

        :param lower_ues: The y-coordinate of the lower end of the UES.
        :param upper_les: The y-coordinate of the upper end of the LES.
        :param threshold: The pressure threshold to count values above.
        :return: A tuple (left_end_x, right_end_x) representing the x-coordinates of the left and right ends of the biggest connected region above the threshold.
        """
        roi = np.array(self.pressure_matrix_high_res[lower_ues:upper_les])
        binary_mask = (roi > threshold).astype(np.uint8) * 255
        contours, _ = cv2.findContours(
            binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            # Default to estimated position if no connected regions found
            left_end_x = self.find_leftmost_x_coordinate_above_threshold(
                self.pressure_matrix_high_res, lower_ues, threshold
            )
            right_end_x = left_end_x + self.pressure_matrix_high_res.shape[1] * 10 / (
                len(self.visualization_data.pressure_matrix[1])
                / config.csv_values_per_second
            )
            return int(left_end_x), int(right_end_x)

        # Find the largest connected contour by area
        largest_contour = max(contours, key=cv2.contourArea)

        # Get bounding box (x, y, width, height)
        x, _, w, _ = cv2.boundingRect(largest_contour)
        left_end_x = x
        right_end_x = x + w

        # Ensure at least 15 % of points in boundary columns exceed threshold
        def check_threshold_percentage(column_index):
            if 0 <= column_index < roi.shape[1]:
                column_values = roi[:, column_index]
                return (np.sum(column_values > threshold) / len(column_values)) >= 0.15
            return False

        while left_end_x < right_end_x and not check_threshold_percentage(left_end_x):
            left_end_x += 1

        while right_end_x > left_end_x and not check_threshold_percentage(right_end_x):
            right_end_x -= 1

        if left_end_x >= right_end_x:
            left_end_x = self.find_leftmost_x_coordinate_above_threshold(
                self.pressure_matrix_high_res, lower_ues, threshold
            )
            right_end_x = left_end_x + self.pressure_matrix_high_res.shape[1] * 10 / (
                len(self.visualization_data.pressure_matrix[1])
                / config.csv_values_per_second
            )
            return int(left_end_x), int(right_end_x)

        return int(left_end_x), int(right_end_x)

    def find_middle_sensor_in_les(self):
        """
        Finds the sensor closest to the middle of the Lower Esophageal Sphincter (LES).
        :return: the index of the closest sensor to the middle of the LES.
        """
        les_start = self.lower_les.get_y_position() / int(
            np.ceil(10 * self.relation_x_y / self.goal_relation)
        )
        les_end = self.upper_les.get_y_position() / int(
            np.ceil(10 * self.relation_x_y / self.goal_relation)
        )
        middle_position = (les_start + les_end) / 2

        closest_sensor = min(
            config.coords_sensors, key=lambda sensor: abs(sensor - middle_position)
        )
        return config.coords_sensors.index(closest_sensor)

    def find_first_sensor_below_ues(self):
        """
        Finds the first sensor below the lower end of the Upper Esophageal Sphincter (UES).
        :return: the sensor position of the first sensor below the lower end of the UES.
        """
        lower_ues_position = self.lower_ues.get_y_position() / int(
            np.ceil(10 * self.relation_x_y / self.goal_relation)
        )
        first_sensor_above_ues = next(
            sensor for sensor in config.coords_sensors if sensor > lower_ues_position
        )
        return config.coords_sensors.index(first_sensor_above_ues)

    def find_leftmost_x_coordinate_above_threshold(
        self, pressure_matrix, lower_ues_y, threshold=30
    ):
        """
        Finds the leftmost x-coordinate of the connected region above the lower UES that has the most values in the upper part of the plot.

        :param pressure_matrix: The pressure matrix.
        :param lower_ues_y: The y-coordinate of the lower UES.
        :param threshold: The pressure threshold (default is 30 mmHg).
        :return: The x-coordinate of the leftmost point in the best connected region.
        """
        binary_mask = (pressure_matrix > threshold).astype(np.uint8) * 255
        contours, _ = cv2.findContours(
            binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return 0

        best_region = None
        max_upper_values = 0

        for contour in contours:
            # Get bounding box of the contour
            x, y, w, h = cv2.boundingRect(contour)
            if y < lower_ues_y:
                upper_values_count = np.sum(contour[:, :, 1] < (lower_ues_y / 2))

                if upper_values_count > max_upper_values:
                    max_upper_values = upper_values_count
                    best_region = contour
        if best_region is not None:
            leftmost_x = np.min(best_region[:, :, 0])
            return leftmost_x

        return 0  # Return 0 if no valid region is found

    def _has_unsaved_changes(self) -> bool:
        """
        Check if there are unsaved changes in the DCI selection window
        """
        # For now, we consider changes made if the user has interacted with the selectors
        # This could be enhanced to track specific changes
        return hasattr(self, "selector") and self.selector is not None

    def _before_going_back(self):
        """
        Cleanup operations before going back
        """
        # Disconnect events and cleanup
        if hasattr(self, "connection_ids"):
            self.disconnect_events()

        # Clear any temporary data if needed
        pass

    def _on_window_activated(self):
        """
        Called when window is shown/activated - re-enable apply button
        """
        super()._on_window_activated()
        # Ensure apply button is always enabled when returning to this window
        if hasattr(self.ui, "apply_button"):
            self.ui.apply_button.setEnabled(True)

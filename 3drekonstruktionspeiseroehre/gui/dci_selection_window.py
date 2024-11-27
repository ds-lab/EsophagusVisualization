from gui.master_window import MasterWindow
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
from scipy import interpolate
import numpy as np
from scipy.ndimage import label

class DCISelectionWindow(QMainWindow):
    """Window where the user selects the rectangle for the DCI (EPI) calculation and the LES and UES positions"""

    next_window = None

    def __init__(self, master_window: MasterWindow, patient_data: PatientData, visit: VisitData):
        """
        init DciSelectionWindow
        :param master_window: the FlexibleWindow in which the next window will be displayed
        :param patient_data: the patient data
        :param visit: the visit data
        """

        super().__init__()
        self.ui = uic.loadUi("./ui-files/dci_selection_window_design.ui", self)
        self.master_window = master_window
        self.patient_data = patient_data
        self.master_window.maximize()
        self.visit = visit
        self.visualization_data = visit.visualization_data_list[0]
        
        self.rectangle = None
        self.pressure_matrix_high_res = None

        # Create a figure canvas for displaying the plot
        self.figure_canvas = None

        # Create a new figure and subplot
        self.fig, self.ax = plt.subplots()
        self.ax.set_title('Select the region for Esophageal Pressure Index')
        self.lower_ues, self.lower_les, self.upper_les, self.selector = None, None, None, None
        self.relation_x_y, self.goal_relation = None, None 

        sensor_names = ["P" + str(len(config.coords_sensors) - i) for i in range(len(config.coords_sensors))]
        self.ui.first_combobox.addItems(sensor_names)
        self.ui.second_combobox.addItems(sensor_names)

        # Access the radio buttons
        self.radioButton20mmHg = self.findChild(QRadioButton, 'radioButton20mmHg')
        self.radioButton0mmHg = self.findChild(QRadioButton, 'radioButton0mmHg')

        # Access checkbox for selector
        self.selector_checkbox = self.findChild(QCheckBox, 'checkBoxDecouple')

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
        self.__update_DCI_value(int(self.selector.extents[0]), int(self.selector.extents[1]), int(self.selector.extents[2]), int(self.selector.extents[3]))

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

        height_in_cm = selected_data.shape[0] / self.pressure_matrix_high_res.shape[0] * np.sort(config.coords_sensors)[-1]
        time_in_s = selected_data.shape[1] / self.pressure_matrix_high_res.shape[1] * (self.visualization_data.pressure_matrix.shape[1] / config.csv_values_per_second)

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
        return np.round((self.lower_les.get_y_position() - self.upper_les.get_y_position()) * np.sort(config.coords_sensors)[-1] / self.pressure_matrix_high_res.shape[0], 2)
    
    def get_esophagus_length(self):
        """
        Calculate the length of the tubular esophagus based on the upper les and lower ues.
        :return: the length of the tubular esophagus in cm
        """
        return np.round((self.upper_les.get_y_position() - self.lower_ues.get_y_position()) * np.sort(config.coords_sensors)[-1] / self.pressure_matrix_high_res.shape[0], 2)
        
    def __couple_selector(self):
        """
        Couple the rectangle selector with the LES and UES lines
        """
        self.selectorIsCoupled = True
        self.selector.extents = (self.selector.extents[0], self.selector.extents[1], self.lower_ues.get_y_position(), self.upper_les.get_y_position())
        self.selector.update()
        self.__update_DCI_value(int(self.selector.extents[0]), int(self.selector.extents[1]), int(self.selector.extents[2]), int(self.selector.extents[3]))

    def on_lines_dragged(self):
        """
        Callback function that is called when the user drags the lines of the LES and UES (updates the DCI value, les height, and length of tubular esophagus)
        """
        # Get the current positions of the upper_les and lower_ues lines
        upper_les_y = self.upper_les.get_y_position()
        lower_ues_y = self.lower_ues.get_y_position()
        lower_les_y = self.lower_les.get_y_position()

        if upper_les_y <= lower_ues_y + 1 * self.pressure_matrix_high_res.shape[0] / np.sort(config.coords_sensors)[-1]: # length of tubular esophagus must be at least 1 cm
            self.upper_les.set_y_position(self.upper_les_backup)
            self.lower_ues.set_y_position(self.lower_ues_backup)
            return
        elif upper_les_y >= lower_les_y - 0.5 * self.pressure_matrix_high_res.shape[0] / np.sort(config.coords_sensors)[-1]: # les must have a minimum height of 0.5 cm
            self.upper_les.set_y_position(self.upper_les_backup)
            self.lower_les.set_y_position(self.lower_les_backup)
            return
        elif lower_ues_y >= lower_les_y - 0.5 * self.pressure_matrix_high_res.shape[0] / np.sort(config.coords_sensors)[-1]: # should never happen since upper_les is always above lower_les
            self.lower_ues.set_y_position(self.lower_ues_backup)
            self.lower_les.set_y_position(self.lower_les_backup) 
            return

        if (self.lower_ues != self.lower_ues_backup or self.upper_les != self.upper_les_backup) and self.selectorIsCoupled: # update the DCI value if rectangle selector is changed
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

    def __initialize_plot_analysis(self):
        """
        Initialize the plot analysis by creating the rectangle selector, the upper LES, lower LES, and lower UES lines, and the DCI value label
        """
        # Create a polygon selector for user interaction
        self.selector = CustomRectangleSelector(self.ax, self.__onselect, useblit=True, props=dict(facecolor=(1, 0, 0, 0), edgecolor='red', linewidth=1.5, linestyle='-'), interactive=True, ignore_event_outside=True, use_data_coordinates=True)

        if self.lower_ues is not None:
            self.lower_ues.text.remove()
            self.lower_ues.line.remove()
        if self.upper_les is not None:
            self.upper_les.text.remove()
            self.upper_les.line.remove()
        if self.lower_les is not None:
            self.lower_les.text.remove()
            self.lower_les.line.remove()
        upper_les = self.find_upper_end_of_les()
        lower_ues = self.find_lower_end_of_ues()
        lower_les = self.find_lower_end_of_les()

        left_end, right_end = self.find_biggest_connected_region(lower_ues, upper_les)
        
        self.selector.extents = (left_end, right_end, lower_ues, upper_les)
        self.line_manager = DraggableLineManager(self.fig.canvas)
        self.lower_les = DraggableHorizontalLine(self.ax.axhline(y=lower_les, color='r', linewidth=1.5, picker=2), label='LES (L)', callback=self.on_lines_dragged)
        self.lower_ues = DraggableHorizontalLine(self.ax.axhline(y=lower_ues, color='r', linewidth=1.5, picker=2), label='UES', callback=self.on_lines_dragged)
        self.upper_les = DraggableHorizontalLine(self.ax.axhline(y=upper_les, color='r', linewidth=1.5, picker=2), label='LES (U)', callback=self.on_lines_dragged)
        self.line_manager.add_line(self.lower_les)
        self.line_manager.add_line(self.lower_ues)
        self.line_manager.add_line(self.upper_les)
        self.fig.canvas.mpl_connect('motion_notify_event', self.line_manager.on_hover)
        self.fig.canvas.mpl_connect('button_press_event', self.line_manager.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.line_manager.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.line_manager.on_motion)
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
            if hasattr(self.selector, 'artists'):
                for artist in self.selector.artists:
                    artist.remove()  # Remove all artists (rectangle, handles, etc.)
            self.selector = None  # Remove the reference to the selector
            self.fig.canvas.draw_idle()  # Redraw the canvas to reflect the changes

    def __reset_button_clicked(self):
        """
        reset-button callback
        """
        self.remove_rectangle_selector()  # Remove the rectangle selector
        self.__initialize_plot_analysis()

    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_dci_selection_info()
        info_window.show()

    def __plot_data(self):
        """
        Create the visualization plot of the pressure matrix and initialize the plot analysis (rectangle selector, upper LES, lower LES, lower UES, etc.)
        """
        number_of_measurements = len(self.visualization_data.pressure_matrix[1])

        # Define the colors and positions for the color map
        colors = [(16/255, 1/255, 255/255), (5/255, 252/255, 252/255), (19/255, 254/255, 3/255), 
                (252/255, 237/255, 3/255), (255/255, 0/255, 0/255), (91/255, 5/255, 132/255)]
        positions = [0, 0.123552143573761, 0.274131298065186, 0.5, 0.702702701091766, 1]

        # Create the color map
        cmap = LinearSegmentedColormap.from_list('custom_cmap', list(zip(positions, colors)))

        # approximate values between sensors in equal distances
        coords_sensors = np.sort(config.coords_sensors) # sort the sensor positions if not already sorted
        min_gap = np.gcd.reduce(np.diff(coords_sensors)) # assumption, that there is only one sensor at each position
        first_sensor = coords_sensors[0] # start at the first sensor (min value)
        last_sensor = coords_sensors[-1] # max value
        estimated_pressure_matrix = np.zeros(((last_sensor - first_sensor) // min_gap + 1, number_of_measurements))
        for i in range(number_of_measurements):
            position = coords_sensors[0]
            sensor_counter = 0
            while position <= last_sensor:
                if position in coords_sensors:
                    estimated_pressure_matrix[(position - first_sensor) // min_gap, i] = self.visualization_data.pressure_matrix[sensor_counter, i]
                    sensor_counter += 1
                else:
                    # need position of the sensors before and after the current position
                    value_before = self.visualization_data.pressure_matrix[sensor_counter - 1, i]
                    value_after = self.visualization_data.pressure_matrix[sensor_counter, i]
                    estimated_pressure_matrix[(position - first_sensor) // min_gap, i] = ((position - coords_sensors[sensor_counter - 1]) * value_after + (coords_sensors[sensor_counter] - position) * value_before) / (coords_sensors[sensor_counter] - coords_sensors[sensor_counter - 1])
                position += min_gap

        x = np.arange(estimated_pressure_matrix.shape[1])
        y = np.arange(estimated_pressure_matrix.shape[0])
        f = interpolate.interp2d(x, y, estimated_pressure_matrix, kind='cubic')

        self.relation_x_y = estimated_pressure_matrix.shape[1] / estimated_pressure_matrix.shape[0]
        self.goal_relation = 16 / 9

        # Define the higher resolution grid
        xnew = np.linspace(0, estimated_pressure_matrix.shape[1], estimated_pressure_matrix.shape[1]*10)
        ynew = np.linspace(0, estimated_pressure_matrix.shape[0], int(np.floor(estimated_pressure_matrix.shape[0]*10 * self.relation_x_y / self.goal_relation)))
        pressure_matrix_high_res = f(xnew, ynew)
        self.pressure_matrix_high_res = pressure_matrix_high_res

        im = self.ax.imshow(pressure_matrix_high_res, cmap=cmap, interpolation='nearest', vmin=config.cmin, vmax=config.cmax)

        # Calculate the time for each measurement
        time = np.arange(0, estimated_pressure_matrix.shape[1]) / config.csv_values_per_second

        # Set the tick labels
        x_ticks = np.linspace(0, pressure_matrix_high_res.shape[1], len(time)//int(np.ceil(10 * self.relation_x_y / self.goal_relation)) + 1)
        y_ticks = np.linspace(0, pressure_matrix_high_res.shape[0], estimated_pressure_matrix.shape[0]//10+1)
        self.ax.set_xticks(x_ticks)
        self.ax.set_yticks(y_ticks)
        self.ax.set_xticklabels(np.round(time[::int(np.ceil(10 * self.relation_x_y / self.goal_relation))], 1))  # Display only every 10th time point, rounded to 1 decimal place
        self.ax.set_yticklabels(np.arange(0, estimated_pressure_matrix.shape[0]+1, 10))

        self.fig.colorbar(im, ax=self.ax, label='Pressure')
        self.ax.set_ylabel('Height along esophagus (cm)')
        self.ax.set_xlabel('Time (s)')
        self.ax.set_xlim(0, pressure_matrix_high_res.shape[1])
        self.ax.set_ylim(pressure_matrix_high_res.shape[0], 0)

        self.figure_canvas = FigureCanvasQTAgg(figure=self.fig)
        self.ui.gridLayout.addWidget(self.figure_canvas)

        plt.contour(self.pressure_matrix_high_res > 30, levels=[0.5], colors='k', linestyles='solid', linewidths=0.3) # threshold for the contour plot is 30 mmHg

        # Plot small dots at the coordinates of the sensors
        min_coord = min(config.coords_sensors)
        max_coord = max(config.coords_sensors)
        for i, coord in enumerate(config.coords_sensors):
            x = self.pressure_matrix_high_res.shape[1] - 10
            # Normalize coord to the range of the pressure_matrix_high_res height
            y = (coord - min_coord) / (max_coord - min_coord) * (self.pressure_matrix_high_res.shape[0] - 1)
            y = int(np.ceil(y))
            self.ax.plot(x, y, 'ro', markersize=4)  # 'ro' means red color, circle marker
            self.ax.annotate(f'P{len(config.coords_sensors) - i}', (x, y), textcoords="offset points", xytext=(5, -4), ha='left')
        self.figure_canvas.draw()
        self.__initialize_plot_analysis()


    def __apply_button_clicked(self):
        """
        apply-button callback
        """
        for i in range(len(self.visit.visualization_data_list)):
            self.visit.visualization_data_list[i].sphincter_length_cm = self.get_les_height()
        if self.ui.first_combobox.currentIndex() != self.ui.second_combobox.currentIndex():
            if self.ui.first_combobox.currentIndex() > self.ui.second_combobox.currentIndex():
                for i in range(len(self.visit.visualization_data_list)):
                    self.visit.visualization_data_list[i].first_sensor_index = self.ui.first_combobox.currentIndex()
                    self.visit.visualization_data_list[i].second_sensor_index = self.ui.second_combobox.currentIndex()
            else:
                for i in range(len(self.visit.visualization_data_list)):
                    self.visit.visualization_data_list[i].first_sensor_index = self.ui.second_combobox.currentIndex()
                    self.visit.visualization_data_list[i].second_sensor_index = self.ui.first_combobox.currentIndex()
        else:
            QMessageBox.critical(self, "Error", "Please select two different sensors.")
        for i in range(len(self.visit.visualization_data_list)):
            self.visit.visualization_data_list[i].esophageal_pressurization_index = float(self.ui.DCI.text().split()[0])
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
    
    def find_lower_end_of_ues(self):
        """
        Detect the lower end of the Upper Esophageal Sphincter (UES).
        
        The UES is identified as a horizontal stripe in the upper part of the plot with higher pressure (>30 mmHg) than the regions above and below it. The UES must be in the upper half of the plot.
        
        :return: The y-coordinate of the lower end of the UES
        """
        upper_half_boundary = len(self.pressure_matrix_high_res) // 2
        stripe_size = max(1, len(self.pressure_matrix_high_res) // 100)
        max_diff = -float('inf')
        lower_end_y = None

        for y in range(stripe_size, upper_half_boundary, stripe_size // 2):
            current_stripe = self.pressure_matrix_high_res[y:y + stripe_size]
            previous_stripe = self.pressure_matrix_high_res[y - stripe_size:y]

            current_average = sum(sum(row) for row in current_stripe) / (len(current_stripe) * len(current_stripe[0]))
            previous_average = sum(sum(row) for row in previous_stripe) / (len(previous_stripe) * len(previous_stripe[0]))

            diff = previous_average - current_average

            if diff > 0 and diff > max_diff:
                max_diff = diff
                lower_end_y = y + stripe_size

        return lower_end_y if lower_end_y is not None else int(0.05 * len(self.pressure_matrix_high_res))
    
    def find_upper_end_of_les(self, threshold=30):
        """
        Detect the upper end of the Lower Esophageal Sphincter (LES).
        
        The LES is identified as a horizontal stripe in the lower part of the plot with a high number of points (>30 mmHg) than the regions above and below it. The LES must be in the lower half of the plot.
        
        :param threshold: The pressure threshold indicating the LES
        :return: The y-coordinate of the upper end of the LES
        """
        lower_half_start = len(self.pressure_matrix_high_res) // 2
        stripe_size = max(1, len(self.pressure_matrix_high_res) // 100)
        upper_end_y = None
        max_diff = -float('inf')

        for y in range(lower_half_start + stripe_size, len(self.pressure_matrix_high_res), stripe_size // 2):
            current_stripe = self.pressure_matrix_high_res[y:y + stripe_size]
            previous_stripe = self.pressure_matrix_high_res[y - stripe_size:y]

            current_count = sum(1 for row in current_stripe for value in row if value > threshold)
            previous_count = sum(1 for row in previous_stripe for value in row if value > threshold)

            diff = current_count - previous_count

            if diff > 0 and diff > max_diff:
                max_diff = diff
                upper_end_y = y

        return upper_end_y if upper_end_y is not None else int(0.75 * len(self.pressure_matrix_high_res))
    
    def find_lower_end_of_les(self, threshold=30):
        """
        Detect the lower end of the Lower Esophageal Sphincter (LES).
        
        The LES is identified as a horizontal stripe in the lower part of the plot with higher pressure (>30 mmHg) than the regions above and below it. The LES must be in the lower half of the plot.
        
        :param threshold: The pressure threshold indicating the LES
        :return: The y-coordinate of the lower end of the LES
        """
        lower_half_start = len(self.pressure_matrix_high_res) // 2
        stripe_size = max(1, len(self.pressure_matrix_high_res) // 100)
        lower_end_y = None
        max_diff = -float('inf')

        for y in range(lower_half_start + stripe_size, len(self.pressure_matrix_high_res), stripe_size // 2):
            current_stripe = self.pressure_matrix_high_res[y:y + stripe_size]
            previous_stripe = self.pressure_matrix_high_res[y - stripe_size:y]

            current_count = sum(1 for row in current_stripe for value in row if value > threshold)
            previous_count = sum(1 for row in previous_stripe for value in row if value > threshold)

            diff = previous_count - current_count

            if diff > 0 and diff > max_diff:
                max_diff = diff
                lower_end_y = y + stripe_size

        return lower_end_y if lower_end_y is not None else int(0.95 * len(self.pressure_matrix_high_res))

    def find_biggest_connected_region(self, lower_ues, upper_les, threshold=30):
        """
        :param lower_ues: The y-coordinate of the lower end of the UES
        :param upper_les: The y-coordinate of the upper end of the LES
        :param threshold: The pressure threshold to count values above
        :return: A tuple (left_end_x, right_end_x) representing the x-coordinates of the left and right ends of the biggest connected region above a certain threshold
        """
        # Extract the region of interest
        roi = np.array(self.pressure_matrix_high_res[lower_ues:upper_les])

        # Create a binary mask where values above the threshold are 1, and others are 0
        binary_mask = roi > threshold

        # Label connected regions
        labeled_array, num_features = label(binary_mask)

        # Find the largest connected region
        max_region_size = 0
        max_region_label = 0
        for region_label in range(1, num_features + 1):
            region_size = np.sum(labeled_array == region_label)
            if region_size > max_region_size:
                max_region_size = region_size
                max_region_label = region_label

        # Find the left and right ends of the largest connected region
        if max_region_label == 0:
            left_end_x = self.find_leftmost_x_coordinate_above_threshold(self.pressure_matrix_high_res, lower_ues, threshold)
            right_end_x = left_end_x + self.pressure_matrix_high_res.shape[1] * 10 / (len(self.visualization_data.pressure_matrix[1]) / config.csv_values_per_second)
            return int(left_end_x), int(right_end_x)

        max_region_coords = np.column_stack(np.where(labeled_array == max_region_label))
        left_end_x = np.min(max_region_coords[:, 1])
        right_end_x = np.max(max_region_coords[:, 1])

        # Check if at least 5% of the points in the left and right end columns are above the threshold
        def check_threshold_percentage(column_index):
            column_values = roi[:, column_index]
            above_threshold_count = np.sum(column_values > threshold)
            total_count = len(column_values)
            return (above_threshold_count / total_count) >= 0.15

        while left_end_x < right_end_x and not check_threshold_percentage(left_end_x):
            left_end_x += 1

        while right_end_x > left_end_x and not check_threshold_percentage(right_end_x):
            right_end_x -= 1

        if left_end_x >= right_end_x:
            left_end_x = self.find_leftmost_x_coordinate_above_threshold(self.pressure_matrix_high_res, lower_ues, threshold)
            right_end_x = left_end_x + self.pressure_matrix_high_res.shape[1] * 10 / (len(self.visualization_data.pressure_matrix[1]) / config.csv_values_per_second)
            return int(left_end_x), int(right_end_x)

        return int(left_end_x), int(right_end_x)
    
    def find_middle_sensor_in_les(self):
        """
        Finds the sensor closest to the middle of the Lower Esophageal Sphincter (LES).
        :return: the index of the closest sensor to the middle of the LES.
        """
        les_start = self.lower_les.get_y_position() / int(np.ceil(10 * self.relation_x_y / self.goal_relation))
        les_end = self.upper_les.get_y_position() / int(np.ceil(10 * self.relation_x_y / self.goal_relation))
        middle_position = (les_start + les_end) / 2

        closest_sensor = min(config.coords_sensors, key=lambda sensor: abs(sensor - middle_position))
        return config.coords_sensors.index(closest_sensor)
    
    def find_first_sensor_below_ues(self):
        """
        Finds the first sensor below the lower end of the Upper Esophageal Sphincter (UES).
        :return: the sensor position of the first sensor below the lower end of the UES.
        """
        lower_ues_position = self.lower_ues.get_y_position() / int(np.ceil(10 * self.relation_x_y / self.goal_relation))
        first_sensor_above_ues = next(sensor for sensor in config.coords_sensors if sensor > lower_ues_position)
        return config.coords_sensors.index(first_sensor_above_ues)
    
    def find_leftmost_x_coordinate_above_threshold(self, pressure_matrix, lower_ues_y, threshold=30):
        """
        Finds the x-coordinate of the connected region above the lower UES that is above the threshold and has the most values in the upper parts of the plot.
        :param pressure_matrix: The pressure matrix.
        :param lower_ues_y: The y-coordinate of the lower UES.
        :param threshold: The pressure threshold (default is 30 mmHg).
        :return: The x-coordinate of the leftmost point in the connected region above the threshold with the most values in the upper parts.
        """
        # Create a binary matrix where values above the threshold are 1 and others are 0
        binary_matrix = pressure_matrix > threshold

        # Label connected regions in the binary matrix
        labeled_matrix, num_features = label(binary_matrix)

        # Initialize variables to keep track of the best region
        best_region_coords = None
        max_upper_values = 0

        # Iterate through the labeled regions to find the best region above the lower UES
        for region_label in range(1, num_features + 1):
            region_coords = np.argwhere(labeled_matrix == region_label)
            if np.any(region_coords[:, 0] < lower_ues_y):
                # Count the number of values in the upper parts of the plot
                upper_values_count = np.sum(region_coords[:, 0] < lower_ues_y / 2)
                if upper_values_count > max_upper_values:
                    max_upper_values = upper_values_count
                    best_region_coords = region_coords

        if best_region_coords is not None:
            # Find the leftmost x-coordinate in the best region
            leftmost_x = np.min(best_region_coords[:, 1])
            return leftmost_x

        return 0  # Return 0 if no region is found
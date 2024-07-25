from gui.master_window import MasterWindow
from PyQt6.QtWidgets import QMainWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from gui.rectangle_selector import CustomRectangleSelector
from PyQt6 import uic
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtGui import QAction
from gui.draggable_horizontal_line import DraggableHorizontalLine
from gui.info_window import InfoWindow
from gui.xray_window_managment import ManageXrayWindows
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import config
from scipy import interpolate
import numpy as np
from scipy.ndimage import gaussian_filter
from itertools import groupby

class DCISelectionWindow(QMainWindow):
    """Window where the user selects the rectangle for the DCI calculation"""

    next_window = None

    def __init__(self, master_window: MasterWindow, patient_data: PatientData, visit: VisitData):
        """
        init DciSelectionWindow
        :param master_window: the FlexibleWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        :param n: n-th visualization of that visit
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
        self.dci_text = self.ax.text(0.5, 1.05, r"Esophageal Pressurization Index: 0.0 mmHg$\cdot$s$\cdot$cm", transform=self.ax.transAxes, ha='center')

        self.lower_ues = None
        self.lower_les = None
        self.upper_les = None
        
        # Connect button click events to methods
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        # Create a menu button for displaying the Info-Window
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        self.__plot_data()

    def __update_DCI_value(self, x1, x2, y1, y2):
        # Extract the selected data
        selected_data = self.pressure_matrix_high_res[y1:y2, x1:x2]

        height_in_cm = selected_data.shape[0] / self.pressure_matrix_high_res.shape[0] * np.sort(config.coords_sensors)[-1]
        time_in_s = selected_data.shape[1] / self.pressure_matrix_high_res.shape[1] * (self.visualization_data.pressure_matrix.shape[1] / config.csv_values_per_second)

        dci_value = self.calculateDCI(selected_data, height_in_cm, time_in_s)
        if self.dci_text is not None:
            self.dci_text.remove()
        self.dci_text = self.ax.text(0.5, 1.05, f"Esophageal Pressurization Index: {dci_value} mmHg$\cdot$s$\cdot$cm", transform=self.ax.transAxes, ha='center')
        self.figure_canvas.draw()


    def __onselect(self, eclick, erelease):
        # eclick and erelease are the press and release events
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        self.__update_DCI_value(x1, x2, y1, y2)
        

    def __initialize_plot_analysis(self):
        # Create a polygon selector for user interaction
        self.selector = CustomRectangleSelector(self.ax, self.__onselect, useblit=True, props=dict(facecolor=(1, 0, 0, 0), edgecolor='red', linewidth=2, linestyle='-'), interactive=True, ignore_event_outside=True, use_data_coordinates=True)

        upper_les = self.find_upper_les()
        print(f"upper les: {upper_les}")
        lower_ues = self.find_lower_ues(upper_les)
        print(f"lower ues: {lower_ues}")
        len_y, len_x = self.pressure_matrix_high_res.shape
        self.selector.extents = (len_x * 0.25, len_x * 0.75, lower_ues, upper_les) # TODO: improve the initial rectangle

        self.lower_les = DraggableHorizontalLine(self.ax.axhline(y=self.find_les_lower_end(upper_les), color='r', linewidth=2, picker=5)) # 'picker=5' makes the line selectable
        self.lower_ues = DraggableHorizontalLine(self.ax.axhline(y=lower_ues, color='r', linewidth=2, picker=5)) # 'picker=5' makes the line selectable
        self.upper_les = DraggableHorizontalLine(self.ax.axhline(y=upper_les, color='r', linewidth=2, picker=5)) # 'picker=5' makes the line selectable
        self.__update_DCI_value(int(len_x * 0.25), int(len_x * 0.75), int(len_y * 0.25), int(len_y * 0.75))
        # self.__simulate_click(1, 1)

    def __reset_button_clicked(self):
        """
        reset-button callback
        """
        self.__initialize_plot_analysis()

    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_dci_selection_info()
        info_window.show()

    def __plot_data(self):
        number_of_measurements = len(self.visualization_data.pressure_matrix[1])

        # Define the colors and positions for the color map
        colors = [(16/255, 1/255, 255/255), (5/255, 252/255, 252/255), (19/255, 254/255, 3/255), 
                (252/255, 237/255, 3/255), (255/255, 0/255, 0/255), (91/255, 5/255, 132/255)] # replace with values from config.py
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

        relation_x_y = estimated_pressure_matrix.shape[1] / estimated_pressure_matrix.shape[0]
        goal_relation = 16 / 9

        # Define the higher resolution grid
        xnew = np.linspace(0, estimated_pressure_matrix.shape[1], estimated_pressure_matrix.shape[1]*10)
        ynew = np.linspace(0, estimated_pressure_matrix.shape[0], int(np.floor(estimated_pressure_matrix.shape[0]*10 * relation_x_y / goal_relation)))
        pressure_matrix_high_res = f(xnew, ynew)
        self.pressure_matrix_high_res = pressure_matrix_high_res

        im = self.ax.imshow(pressure_matrix_high_res, cmap=cmap, interpolation='nearest', vmin=config.cmin, vmax=config.cmax)

        # Calculate the time for each measurement
        time = np.arange(0, estimated_pressure_matrix.shape[1]) / config.csv_values_per_second

        # Set the tick labels
        x_ticks = np.linspace(0, pressure_matrix_high_res.shape[1], len(time)//int(np.ceil(10 * relation_x_y / goal_relation)) + 1)
        y_ticks = np.linspace(0, pressure_matrix_high_res.shape[0], estimated_pressure_matrix.shape[0]//10+1)
        self.ax.set_xticks(x_ticks)
        self.ax.set_yticks(y_ticks)
        self.ax.set_xticklabels(np.round(time[::int(np.ceil(10 * relation_x_y / goal_relation))], 1))  # Display only every 10th time point, rounded to 1 decimal place
        self.ax.set_yticklabels(np.arange(0, estimated_pressure_matrix.shape[0]+1, 10))

        self.fig.colorbar(im, ax=self.ax, label='Pressure')
        self.ax.set_ylabel('Height along esophagus (cm)')
        self.ax.set_xlabel('Time (s)')

        self.figure_canvas = FigureCanvasQTAgg(figure=self.fig)
        self.ui.gridLayout.addWidget(self.figure_canvas)

        plt.contour(self.pressure_matrix_high_res > 30, levels=[0.5], colors='k', linestyles='solid', linewidths=0.3) # threshold for the contour plot is 30 mmHg

        self.figure_canvas.draw()
        self.__initialize_plot_analysis()
        les_center = self.find_upper_les()
        print(f"les center: {les_center}")
        print(self.pressure_matrix_high_res.shape)


    def __apply_button_clicked(self):
        """
        apply-button callback
        """
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
        if len(pressure_matrix[mask]) != 0:
            # Calculate the mean of these values
            mean_pressure = np.mean(np.maximum(pressure_matrix - 20, 0)) # TODO: check if calculation is correct
        """print(f"Height: {height} cm")
        print(f"Time: {time} s")
        print(f"Mean pressure with np.mean(np.maximum(pressure_matrix - 20, 0)): {mean_pressure} mmHg")
        print(f"Mean pressure with np.mean(np.maximum(pressure_matrix[mask] - 20, 0)): {np.mean(np.maximum(pressure_matrix[mask] - 20, 0))} mmHg")
        print(f"Mean pressure with np.mean(pressure_matrix) - 20: {np.mean(pressure_matrix) - 20} mmHg")
        print(f"Mean pressure with np.mean(pressure_matrix[mask]) - 20: {np.mean(pressure_matrix[mask]) - 20} mmHg")
        print(f"Mean pressure with np.divide(np.sum(pressure_matrix[mask]), pressure_matrix.size): {np.divide(np.sum(pressure_matrix[mask]), pressure_matrix.size)} mmHg")"""
        return np.round(mean_pressure * height * time, 2)
    
    def find_upper_les(self):
        # Step 2: Preprocess
        smoothed_matrix = gaussian_filter(self.pressure_matrix_high_res, sigma=1)  # Apply Gaussian blur

        # Step 3: Detect High-Pressure Region
        avg_pressure = np.mean(smoothed_matrix, axis=1)  # Average pressure along y-axis
        threshold = np.mean(avg_pressure) + 1.5 * np.std(avg_pressure)  # Example threshold
        high_pressure_regions = np.where(avg_pressure > threshold)[0]

        # Assuming LES is the largest continuous high-pressure region
        les_position = max((list(g) for _, g in groupby(high_pressure_regions)), key=len)
        les_center = np.mean(les_position)

        return les_center
    
    def find_les_lower_end(self, les_upper_limit, target_pressure=30, tolerance=2):
        """
        Find the lower end of the LES based on a target pressure level.
        
        :param les_upper_limit: The y-coordinate of the upper limit of the LES
        :param target_pressure: The target pressure value to find below the LES (default 30 mmHg)
        :param tolerance: The tolerance level for the target pressure (default 2 mmHg)
        :return: The y-coordinate of the lower end of the LES
        """
        lower_end = None
        for y in range(int(les_upper_limit) + 1, len(self.pressure_matrix_high_res), 5):
            row_pressure = np.mean(self.pressure_matrix_high_res[y])
            if target_pressure - tolerance <= row_pressure <= target_pressure + tolerance:
                lower_end = y
                break  # Stop at the first row that meets the criteria
        
        return lower_end
    
    def find_lower_ues(self, upper_les, target_pressure_ues=30, gap_pressure_ues=25):
        """
        Find the lower end of the UES starting from the top of the diagram, ensuring it's not connected to the LES
        by requiring that more than 20 rows have values below a certain threshold to confirm discontinuity.
        
        :param upper_les: The y-coordinate of the upper end of the LES
        :param target_pressure_ues: The pressure value indicating significant portions
        :param gap_pressure_ues: The pressure threshold for identifying gaps
        :return: The y-coordinate of the lower end of the UES
        """
        for y in range(len(self.pressure_matrix_high_res) - 1, -1, -10):  # Start from the top of the diagram
            row = self.pressure_matrix_high_res[y]
            high_pressure_count = sum(p > target_pressure_ues for p in row)
            if high_pressure_count / len(row) > 0.2:  # Example criterion: >20% of points are above target pressure
                # Check for discontinuity between this row and LES
                discontinuity_found = False
                low_pressure_row_count = 0  # Counter for consecutive rows meeting the low-pressure criteria
                for check_y in range(y + 1, int(upper_les)):
                    check_row = self.pressure_matrix_high_res[check_y]
                    if sum(p <= gap_pressure_ues for p in check_row) / len(check_row) > 0.5:  # Majority of pressures are below target
                        low_pressure_row_count += 1
                        if low_pressure_row_count >= 20:  # Check if at least 20 rows meet the criteria
                            discontinuity_found = True
                            break
                    else:
                        low_pressure_row_count = 0  # Reset counter if a row does not meet the criteria
                if discontinuity_found:
                    return y  # This row is considered the lower end of the UES if discontinuity is confirmed
        return 0  # Return None if no suitable region is found

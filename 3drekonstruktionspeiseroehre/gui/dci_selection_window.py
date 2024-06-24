from gui.master_window import MasterWindow
from PyQt6.QtWidgets import QMainWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from matplotlib.widgets import RectangleSelector
from PyQt6 import uic
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtGui import QAction
from gui.info_window import InfoWindow
from gui.endoscopy_selection_window import EndoscopySelectionWindow
from gui.visualization_window import VisualizationWindow
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import config
from scipy import interpolate

class DCISelectionWindow(QMainWindow):
    """Window where the user selects the rectangle for the DCI calculation"""

    next_window = None

    def __init__(self, master_window: MasterWindow, patient_data: PatientData, visit: VisitData, n):
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
        self.visualization_data = visit.visualization_data_list[n]
        self.n = n
        self.rectangle = None
        self.pressure_matrix_high_res = None

        # Create a figure canvas for displaying the plot
        self.figure_canvas = None

        # Create a new figure and subplot
        self.fig, self.ax = plt.subplots()
        self.dci_text = self.ax.text(0.5, 1.05, r"DCI: 0.0 mmHg$\cdot$s$\cdot$cm", transform=self.ax.transAxes, ha='center')
        
        # Connect button click events to methods
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        # Create a menu button for displaying the Info-Window
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        self.__plot_data()

    def __onselect(self, eclick, erelease):
        # eclick and erelease are the press and release events
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)

        # Extract the selected data
        selected_data = self.pressure_matrix_high_res[y1:y2, x1:x2]

        height_in_cm = selected_data.shape[0] / self.pressure_matrix_high_res.shape[0] * np.sort(config.coords_sensors)[-1]
        time_in_s = selected_data.shape[1] / self.pressure_matrix_high_res.shape[1] * (self.visualization_data.pressure_matrix.shape[1] / config.csv_values_per_second)

        dci_value = self.calculateDCI(selected_data, height_in_cm, time_in_s)
        print(dci_value)
        # Update the DCI text
        if self.dci_text is not None:
            self.dci_text.remove()
        self.dci_text = self.ax.text(0.5, 1.05, f"DCI: {dci_value} mmHg$\cdot$s$\cdot$cm", transform=self.ax.transAxes, ha='center')
        self.figure_canvas.draw()

    def __reset_button_clicked(self):
        """
        reset-button callback
        """
        self.__reset_selector()

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

        # Create a polygon selector for user interaction
        self.selector = RectangleSelector(self.ax, self.__onselect, useblit=True, props=dict(facecolor=(1, 0, 0, 0), edgecolor='red', linewidth=2, linestyle='-'), interactive=True)

        self.figure_canvas.draw()


    def __apply_button_clicked(self):
        """
        apply-button callback
        """
        # TODO: refactor; until now, only what stood in position_selection_window.py was copied
        # TODO: maybe store DCI in database
        if len(self.visualization_data.endoscopy_files) > 0:
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

    def __reset_selector(self):
        """
        starts the selection of a new rectangle/resets the rectangle selector
        """
        self.selector.clear()
        self.selector.set_active(True)

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
            mean_pressure = np.mean(pressure_matrix[mask]) - 20 # TODO: check if -20 is correct
        return np.round(mean_pressure * height * time, 2)

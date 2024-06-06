from gui.master_window import MasterWindow
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from matplotlib.widgets import RectangleSelector
from PyQt6 import uic
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtGui import QAction
from matplotlib.figure import Figure
from gui.info_window import InfoWindow
from gui.endoscopy_selection_window import EndoscopySelectionWindow
from gui.visualization_window import VisualizationWindow
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from matplotlib.colors import LinearSegmentedColormap
import config

# for RectangleSelector: https://matplotlib.org/3.1.1/gallery/widgets/rectangle_selector.html

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
        print(self.visualization_data.pressure_matrix)
        print(self.visualization_data.pressure_matrix.shape)
        # self.visualization_data.pressure_matrix stores arrays of pressure values of each sensor; index 0 is sensor P22 (top), index 1 is sensor P1 (bottom)
        # can we use calculate_surfacecolor_list?

        # Create a figure canvas for displaying the plot
        self.figure_canvas = None
        
        # Connect button click events to methods
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        # Create a menu button for displaying the Info-Window
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        self.__plot_data()


    def __onselect(self, eventpress, eventrelease):
        # TODO: do sth useful with the selected rectangle
        'eventpress and eventrelease are the press and release events'
        x1, y1 = eventpress.xdata, eventpress.ydata
        x2, y2 = eventrelease.xdata, eventrelease.ydata
        print(f"Selection started at ({x1}, {y1}) and ended at ({x2}, {y2})")

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
        number_of_sensors = len(self.visualization_data.pressure_matrix[0])

        # Define the colors and positions for the color map
        colors = [(16/255, 1/255, 255/255), (5/255, 252/255, 252/255), (19/255, 254/255, 3/255), 
                (252/255, 237/255, 3/255), (255/255, 0/255, 0/255), (91/255, 5/255, 132/255)] # replace with values from config.py
        positions = [0, 0.123552143573761, 0.274131298065186, 0.5, 0.702702701091766, 1]

        # Create the color map
        cmap = LinearSegmentedColormap.from_list('custom_cmap', list(zip(positions, colors)))
 
        # Create a new figure and subplot
        fig, ax = plt.subplots()

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
                    # print(f"value_before: {value_before}, value_after: {value_after}, value_estimated: {estimated_pressure_matrix[(position - first_sensor) // min_gap, i]}")
                    # (position - coords_sensors[sensor_counter]) / (coords_sensors[sensor_counter + 1] - coords_sensors[sensor_counter]) * (value_after - value_before) + value_before
                    #np.mean([self.visualization_data.pressure_matrix[coords_sensors.index(sensor), i] for sensor in coords_sensors if sensor < position and sensor > position + min_gap])
                #print(f"position: {position}, sensor_counter: {sensor_counter}, value: {estimated_pressure_matrix[(position - first_sensor) // min_gap, i]}")
                position += min_gap

        im = ax.imshow(estimated_pressure_matrix, cmap=cmap, interpolation='nearest', vmin=config.cmin, vmax=config.cmax)
        fig.colorbar(im, ax=ax, label='Pressure')

        self.figure_canvas = FigureCanvasQTAgg(figure=fig)
        self.ui.gridLayout.addWidget(self.figure_canvas)

        # Create a polygon selector for user interaction
        self.selector = RectangleSelector(ax, self.__onselect, useblit=True, props=dict(facecolor=(1, 0, 0, 0), edgecolor='red', linewidth=2, linestyle='-'), interactive=True)

        self.figure_canvas.draw()

    """def __plot_data(self):
        # time_data = np.linspace(0, 10, 100)  # replace with your actual data
        # height_data = np.sin(time_data)  # replace with your actual data

        # self.plot_ax.plot(time_data, height_data)
        # self.figure_canvas.draw()

        # Assuming self.visualization_data.pressure_matrix is a 2D array
        data = self.visualization_data.pressure_matrix

        # Create a grid of the same size as the data
        grid_x, grid_y = np.mgrid[0:data.shape[0]:1, 0:data.shape[1]:1]

        # Create a finer grid
        fine_grid_x, fine_grid_y = np.mgrid[0:data.shape[0]:0.01, 0:data.shape[1]:0.01]

        # Interpolate the data onto the finer grid
        fine_data = griddata((grid_x.ravel(), grid_y.ravel()), data.ravel(), (fine_grid_x, fine_grid_y), method='cubic')

        # Create a new figure and subplot
        fig, ax = plt.subplots()

        # Define the colors and positions for the color map
        colors = [(16/255, 1/255, 255/255), (5/255, 252/255, 252/255), (19/255, 254/255, 3/255), 
                (252/255, 237/255, 3/255), (255/255, 0/255, 0/255), (91/255, 5/255, 132/255)] # replace with values from config.py
        positions = [0, 0.123552143573761, 0.274131298065186, 0.5, 0.702702701091766, 1]

        # Create the color map
        cmap = LinearSegmentedColormap.from_list('custom_cmap', list(zip(positions, colors)))

        # Plot the interpolated data
        im = ax.imshow(fine_data, cmap=cmap, interpolation='nearest', vmin=config.cmin, vmax=config.cmax)
        fig.colorbar(im, ax=ax, label='Pressure')

        # Create a canvas and add the plot to it
        canvas = FigureCanvasQTAgg(fig)

        # Create a new QWidget and set it as the central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a layout and add the canvas to it
        layout = QVBoxLayout(central_widget)
        layout.addWidget(canvas)"""



    def __apply_button_clicked(self):
        """
        apply-button callback
        """
        # TODO: refactor; until now, only what stood in position_selection_window.py was copied
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

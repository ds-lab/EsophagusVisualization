from gui.master_window import MasterWindow
from PyQt6.QtWidgets import QMainWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from matplotlib.widgets import RectangleSelector
from PyQt6 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt6.QtGui import QAction
from matplotlib.figure import Figure
from gui.info_window import InfoWindow
from gui.endoscopy_selection_window import EndoscopySelectionWindow
from gui.visualization_window import VisualizationWindow
import numpy as np

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
        print(self.visualization_data.pressure_matrix)
        print(self.visualization_data.pressure_matrix.shape)
        # self.visualization_data.pressure_matrix stores arrays of pressure values of each sensor; index 0 is sensor P22 (top), index 1 is sensor P1 (bottom)
        # can we use calculate_surfacecolor_list?

        # Create a figure canvas for displaying the image
        self.figure_canvas = FigureCanvasQTAgg(Figure())
        self.ui.gridLayout.addWidget(self.figure_canvas)
        # Connect button click events to methods
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        # Create a menu button for displaying the Info-Window
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        # Create a plot axis for displaying the image
        self.plot_ax = self.figure_canvas.figure.subplots()
        self.figure_canvas.figure.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.95)
        # Create a polygon selector for user interaction
        self.selector = RectangleSelector(self.plot_ax, self.__onselect, useblit=True, props=dict(facecolor=(1, 0, 0, 0), edgecolor='red', linewidth=2, linestyle='-'), interactive=True)
        self.__plot_data()


    def __onselect(self, polygon):
        """
        called when new polygon was created
        :param polygon: new polygon
        """
        self.polygon = polygon

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
        time_data = np.linspace(0, 10, 100)  # replace with your actual data
        height_data = np.sin(time_data)  # replace with your actual data

        self.plot_ax.plot(time_data, height_data)
        self.figure_canvas.draw()

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

from gui.endoscopy_selection_window import EndoscopySelectionWindow
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.visualization_window import VisualizationWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from logic.visualization_data import VisualizationData
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.pyplot import Circle
from PyQt5 import uic
from PyQt5.QtWidgets import QAction, QMainWindow, QMessageBox
from skimage import io


class PositionSelectionWindow(QMainWindow):
    """Window where the user selects needed positions for the calculation"""

    def __init__(self, master_window: MasterWindow, next_window, patient_data: PatientData, visit: VisitData, n: int):
        """
        init PositionSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        """

        super().__init__()
        self.ui = uic.loadUi("./ui-files/position_selection_window_design.ui", self)
        self.master_window = master_window
        self.patient_data = patient_data
        self.visualization_data = visit.visualization_data_list[n]
        self.visit = visit
        self.n = n
        self.next_window = next_window
        sensor_names = ["P" + str(22 - i) for i in range(22)]
        self.ui.first_combobox.addItems(sensor_names)
        self.ui.second_combobox.addItems(sensor_names)
        self.ui.second_combobox.setCurrentIndex(21)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        self.ui.first_sensor_button.clicked.connect(self.__first_sensor_button_clicked)
        self.ui.second_sensor_button.clicked.connect(self.__second_sensor_button_clicked)
        self.ui.sphinkter_button.clicked.connect(self.__sphincter_button_clicked)
        self.ui.eso_exit_button.clicked.connect(self.__eso_exit_button_clicked)
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        if len(self.visualization_data.endoscopy_filenames) > 0:
            self.ui.endoscopy_button.clicked.connect(self.__endoscopy_button_clicked)
        else:
            self.ui.endoscopy_groupbox.setHidden(True)

        self.figure_canvas = FigureCanvasQTAgg(Figure())
        self.ui.gridLayout.addWidget(self.figure_canvas)

        self.xray_image = io.imread(self.visualization_data.xray_filename)
        self.plot_ax = self.figure_canvas.figure.subplots()
        self.figure_canvas.figure.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.95)
        self.plot_ax.imshow(self.xray_image)
        self.plot_ax.axis('off')
        self.figure_canvas.mpl_connect("button_press_event", self.__on_left_click)

        self.active_paint_index = None  # None=none, 0=first sensor, 1=second sensor, 2=endoscopy, 3=sphincter
        self.first_sensor_pos = None
        self.second_sensor_pos = None
        self.second_sensor_pos_2 = None
        self.endoscopy_pos = None
        self.sphincter_upper_pos = None
        self.esophagus_exit_pos = None

    def __on_left_click(self, event):
        """
        handles left-click on image
        :param event:
        """
        # TODO: second und sphincter Punkte mit x und y übergeben und ax line nehmen 
        if event.xdata and event.ydata and self.active_paint_index is not None:
            self.plot_ax.clear()
            self.plot_ax.imshow(self.xray_image)
            self.plot_ax.axis('off')
            if self.active_paint_index == 0:
                self.first_sensor_pos = event.ydata
            elif self.active_paint_index == 1:
                self.second_sensor_pos = event.ydata
            elif self.active_paint_index == 2:
                self.endoscopy_pos = (event.xdata, event.ydata)
            elif self.active_paint_index == 3:
                self.sphincter_upper_pos = (event.xdata, event.ydata)
            elif self.active_paint_index == 4:
                self.esophagus_exit_pos = (event.xdata, event.ydata)

            if self.first_sensor_pos:
                self.plot_ax.axhline(self.first_sensor_pos, color='green')
            if self.second_sensor_pos:
                self.plot_ax.axhline(self.second_sensor_pos, color='blue')
            if self.endoscopy_pos:
                point = Circle(self.endoscopy_pos, 4.0, color='red')
                self.plot_ax.add_patch(point)
            if self.sphincter_upper_pos:
                point = Circle(self.sphincter_upper_pos, 4.0, color='yellow')
                self.plot_ax.add_patch(point)
            if self.esophagus_exit_pos:
                point = Circle(self.esophagus_exit_pos, 4.0, color='pink')
                self.plot_ax.add_patch(point)
            self.figure_canvas.figure.canvas.draw()

    def __apply_button_clicked(self):
        """
        apply-button callback
        """
        #
        if self.__are_necessary_positions_set():
            if self.ui.first_combobox.currentIndex() != self.ui.second_combobox.currentIndex():
                if self.__is_sensor_order_correct():
                    if not self.__is_any_position_outside_polygon():
                        self.ui.apply_button.setDisabled(True)
                        offset = min([point[1] for point in self.visualization_data.xray_polygon])
                        if self.ui.first_combobox.currentIndex() > self.ui.second_combobox.currentIndex():
                            self.visualization_data.first_sensor_pos = int(self.first_sensor_pos - offset)
                            self.visualization_data.first_sensor_index = self.ui.first_combobox.currentIndex()
                            self.visualization_data.second_sensor_pos = int(self.second_sensor_pos - offset)
                            self.visualization_data.second_sensor_index = self.ui.second_combobox.currentIndex()
                        else:
                            self.visualization_data.first_sensor_pos = int(self.second_sensor_pos - offset)
                            self.visualization_data.first_sensor_index = self.ui.second_combobox.currentIndex()
                            self.visualization_data.second_sensor_pos = int(self.first_sensor_pos - offset)
                            self.visualization_data.second_sensor_index = self.ui.first_combobox.currentIndex()
                        self.visualization_data.sphincter_upper_pos = (
                            int(self.sphincter_upper_pos[0]), int(self.sphincter_upper_pos[1] - offset))
                        self.visualization_data.esophagus_exit_pos = (
                            int(self.esophagus_exit_pos[0]), int(self.esophagus_exit_pos[1] - offset))
                        self.visualization_data.sphincter_length_cm = self.ui.sphinkter_spinbox.value()

                        # If there are more visualizations in this visit continue with the next xray selection
                        if self.next_window:
                            self.master_window.switch_to(self.next_window)
                        # Handle Endoscopy annotation
                        elif len(self.visualization_data.endoscopy_filenames) > 0:
                            # ToDo: richtige y-position für endoscopy_pos finden
                            self.visualization_data.endoscopy_start_pos = \
                                (int(self.endoscopy_pos[0]), int(self.endoscopy_pos[1] - offset))
                            endoscopy_selection_window = EndoscopySelectionWindow(self.master_window,
                                                                                  self.patient_data, self.visit)
                            self.master_window.switch_to(endoscopy_selection_window)
                            self.close()
                        # Else show the visualization
                        else:
                            # Add new visualization to patient_data
                            self.patient_data.add_visit(self.visit.name, self.visit)
                            visualization_window = VisualizationWindow(self.master_window, self.patient_data)
                            self.master_window.switch_to(visualization_window)
                            self.close()
                    else:
                        QMessageBox.critical(self, "Fehler", "Die Positionen müssen sich innerhalb des zuvor " +
                                             "markierten Umrisses des Ösophagus befinden")
                else:
                    QMessageBox.critical(self, "Fehler", "Positionen der Sensoren scheinen vertauscht zu sein")
            else:
                QMessageBox.critical(self, "Fehler", "Bitte wählen Sie zwei unterschiedliche Sensoren aus")
        else:
            QMessageBox.critical(self, "Fehler", "Bitte tragen Sie alle benötigten Positionen in die Graphik ein")

    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_position_selection_info()
        info_window.show()

    def __first_sensor_button_clicked(self):
        self.active_paint_index = 0

    def __second_sensor_button_clicked(self):
        self.active_paint_index = 1

    def __endoscopy_button_clicked(self):
        self.active_paint_index = 2

    def __sphincter_button_clicked(self):
        self.active_paint_index = 3

    def __eso_exit_button_clicked(self):
        self.active_paint_index = 4

    def __are_necessary_positions_set(self):
        """
        checks if all necessary positions are set
        :return: True or False
        """
        return self.first_sensor_pos and self.second_sensor_pos and self.sphincter_upper_pos and self.esophagus_exit_pos \
            and (self.endoscopy_pos or len(self.visualization_data.endoscopy_filenames) == 0)

    def __is_sensor_order_correct(self):
        """
        checks for correct sensor order
        :return: True or False
        """
        return (self.ui.first_combobox.currentIndex() > self.ui.second_combobox.currentIndex()
                and self.first_sensor_pos > self.second_sensor_pos) \
            or (self.ui.first_combobox.currentIndex() < self.ui.second_combobox.currentIndex()
                and self.first_sensor_pos < self.second_sensor_pos)

    def __is_any_position_outside_polygon(self):
        """
        checks if a position was marked outside the shape of the esophagus
        :return: True or False
        """
        poly_y_min = min([point[1] for point in self.visualization_data.xray_polygon])
        poly_y_max = max([point[1] for point in self.visualization_data.xray_polygon])
        # ToDo: Check für endoscopy_pos anpassen
        return self.first_sensor_pos < poly_y_min or self.first_sensor_pos > poly_y_max \
            or self.second_sensor_pos < poly_y_min or self.second_sensor_pos > poly_y_max \
            or (len(self.visualization_data.endoscopy_filenames) > 0 and (self.endoscopy_pos[1] < poly_y_min
                                                                          or self.endoscopy_pos[1] > poly_y_max))

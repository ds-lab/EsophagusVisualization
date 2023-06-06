from PyQt5 import uic
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QAction
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from skimage import io
from gui.endoscopy_selection_window import EndoscopySelectionWindow
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
from logic.visualization_data import VisualizationData
from gui.visualization_window import VisualizationWindow


class PositionSelectionWindow(QMainWindow):
    """Window where the user selects needed positions for the calculation"""

    def __init__(self, master_window: MasterWindow, visualization, next_window, all_visualization):
        """
        init PositionSelectionWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        """

        super().__init__()
        self.ui = uic.loadUi("ui-files/position_selection_window_design.ui", self)
        self.master_window = master_window
        self.visualization_data = visualization
        self.all_visualization = all_visualization
        self.next_window = next_window
        sensor_names = ["P" + str(22 - i) for i in range(22)]
        self.ui.first_combobox.addItems(sensor_names)
        self.ui.second_combobox.addItems(sensor_names)
        self.ui.second_combobox.setCurrentIndex(21)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        self.ui.first_sensor_button.clicked.connect(self.__first_sensor_button_clicked)
        self.ui.second_sensor_button.clicked.connect(self.__second_sensor_button_clicked)
        self.ui.sphinkter_button.clicked.connect(self.__sphincter_button_clicked)
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
        self.endoscopy_pos = None
        self.sphincter_upper_pos = None

    def __on_left_click(self, event):
        """
        handles left-click on image
        :param event:
        """
        if event.xdata and event.ydata and self.active_paint_index is not None:
            self.plot_ax.clear()
            self.plot_ax.imshow(self.xray_image)
            self.plot_ax.axis('off')
            if self.active_paint_index == 0:
                self.first_sensor_pos = event.ydata
            elif self.active_paint_index == 1:
                self.second_sensor_pos = event.ydata
            elif self.active_paint_index == 2:
                self.endoscopy_pos = event.ydata
            elif self.active_paint_index == 3:
                self.sphincter_upper_pos = event.ydata
            if self.first_sensor_pos:
                self.plot_ax.axhline(self.first_sensor_pos, color='green')
            if self.second_sensor_pos:
                self.plot_ax.axhline(self.second_sensor_pos, color='blue')
            if self.endoscopy_pos:
                self.plot_ax.axhline(self.endoscopy_pos, color='red')
            if self.sphincter_upper_pos:
                self.plot_ax.axhline(self.sphincter_upper_pos, color='yellow')
            self.figure_canvas.figure.canvas.draw()

    def __apply_button_clicked(self):
        """
        apply-button callback
        """
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
                        self.visualization_data.sphincter_upper_pos = int(self.sphincter_upper_pos - offset)
                        self.visualization_data.sphincter_length_cm = self.ui.sphinkter_spinbox.value()
                        if len(self.visualization_data.endoscopy_filenames) > 0:
                            self.visualization_data.endoscopy_start_pos = int(self.endoscopy_pos - offset)
                            endoscopy_selection_window = EndoscopySelectionWindow(self.master_window,
                                                                                  self.visualization_data)
                            self.master_window.switch_to(endoscopy_selection_window)
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

        # füge alle visualization Data der Bilder zu all_visualization hinzu
        self.all_visualization.append(self.visualization_data)

        # falls es nächste Fenster gibt, gehe zu nächstem Fenster
        if self.next_window:
            self.master_window.switch_to(self.next_window)
        # wenn nicht, dann erzeuge Visualisierung
        else:
            self.__create_visualization()


    def __create_visualization(self):
        """
        apply-button callback
        """
        all_visualization = self.all_visualization
        visualization_window = VisualizationWindow(self.master_window, all_visualization)
        self.master_window.switch_to(visualization_window)
        self.close()

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

    def __are_necessary_positions_set(self):
        """
        checks if all necessary positions are set
        :return: True or False
        """
        return self.first_sensor_pos and self.second_sensor_pos and self.sphincter_upper_pos \
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
        return self.first_sensor_pos < poly_y_min or self.first_sensor_pos > poly_y_max \
            or self.second_sensor_pos < poly_y_min or self.second_sensor_pos > poly_y_max \
            or self.sphincter_upper_pos < poly_y_min or self.sphincter_upper_pos > poly_y_max \
            or (len(self.visualization_data.endoscopy_filenames) > 0 and (self.endoscopy_pos < poly_y_min
                or self.endoscopy_pos > poly_y_max))


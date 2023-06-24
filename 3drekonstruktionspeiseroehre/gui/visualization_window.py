import multiprocessing
import pickle
import shutil
from multiprocessing.pool import ThreadPool

import cv2
from PyQt5.QtWidgets import QProgressDialog, QMainWindow, QAction, QFileDialog
from PyQt5.QtCore import QUrl
from PyQt5 import uic
from dash_server import DashServer
from logic.figure_creator.figure_creation_thread import FigureCreationThread
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
from logic.figure_creator.figure_creator_with_endoscopy import FigureCreatorWithEndoscopy
from logic.figure_creator.figure_creator_without_endoscopy import FigureCreatorWithoutEndoscopy
from logic.visualization_data import VisualizationData
import numpy as np


class VisualizationWindow(QMainWindow):
    """The window that shows the visualization"""

    def __init__(self, master_window: MasterWindow, all_visualization, n):
        """
        init VisualizationWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        """
        super().__init__()
        self.ui = uic.loadUi("/Users/Alicia/PycharmProjects/3drekonstruktionspeiseroehre_flex/3drekonstruktionspeiseroehre/ui-files/visualization_window_design.ui", self)
        self.master_window = master_window
        # Maximize window to show the whole 3d reconstruction (necessary if visualization_data is imported)
        self.master_window.maximize()
        self.all_visualization = all_visualization
        self.n = n
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        menu_button_2 = QAction("Download für Import", self)
        menu_button_2.triggered.connect(self.__download_object_file)
        self.ui.menubar.addAction(menu_button_2)
        menu_button_3 = QAction("Download für Darstellung", self)
        menu_button_3.triggered.connect(self.__download_html_file)
        self.ui.menubar.addAction(menu_button_3)
        # set native menu bar flag as false to see MenuBar on Mac
        self.ui.menubar.setNativeMenuBar(False)

        self.dash_server = None
        self.progress_dialog = QProgressDialog("Visualisierung wird erstellt", None, 0, 100, None)
        self.progress_dialog.setWindowTitle("Fortschritt")
        self.progress_dialog.show()
        self.__start_visualization()

    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_visualization_info()
        info_window.show()

    def closeEvent(self, event):
        """
        closing-event callback
        :param event:
        """
        if self.dash_server:
            self.dash_server.stop()
        self.ui.webView.close()

    def __set_progress(self, val):
        """
        progress bar callback
        :param val: new progress value
        """
        if self.progress_dialog:
            self.progress_dialog.setValue(val)

    def __start_visualization(self):
        """
        callback of the figure creation thread
        :param figure_creator: FigureCreator
        """

        pool = ThreadPool(len(self.all_visualization))
        pool_output = pool.map(run, self.all_visualization)

        for i in range(len(self.all_visualization)):
            self.all_visualization[i].figure_creator = pool_output[i]

        self.dash_server = DashServer(self.all_visualization)
        url = QUrl()
        url.setScheme("http")
        url.setHost("127.0.0.1")
        url.setPort(self.dash_server.get_port())
        self.ui.webView.load(url)

    def __download_object_file(self):
        """
        Download button callback
        """
        # Prompt the user to choose a destination path
        destination_file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Pickle Files (*.pickle)")

        # Save the visualization_data object as a pickle file
        with open(destination_file_path, 'wb') as file:
            pickle.dump(self.all_visualization[self.n], file)

    def __download_html_file(self):
        """
        Download button callback
        """
        # Prompt the user to choose a destination path
        destination_file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "HTML Files (*.html)")
        # Get Figure
        figure = self.all_visualization[self.n].figure_creator.get_figure()
        # Write the figure to a html file
        figure.write_html(destination_file_path)


def run(visualization_data):
    """
        to be run as thread
        starts figure creation
        """
    mask = np.zeros((visualization_data.xray_image_height, visualization_data.xray_image_width))
    cv2.drawContours(mask, [np.array(visualization_data.xray_polygon)], -1, 1, -1)
    visualization_data.xray_mask = mask

    if visualization_data.endoscopy_polygons is not None:
        figure_creator = FigureCreatorWithEndoscopy(visualization_data)
    else:
        figure_creator = FigureCreatorWithoutEndoscopy(visualization_data)

    return figure_creator

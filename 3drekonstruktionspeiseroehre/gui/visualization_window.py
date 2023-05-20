import pickle
import shutil
from PyQt5.QtWidgets import QProgressDialog, QMainWindow, QAction, QFileDialog
from PyQt5.QtCore import QUrl
from PyQt5 import uic
from dash_server import DashServer
from logic.figure_creator.figure_creation_thread import FigureCreationThread
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
from logic.visualization_data import VisualizationData


class VisualizationWindow(QMainWindow):
    """The window that shows the visualization"""

    def __init__(self, master_window: MasterWindow, visualization_data: VisualizationData):
        """
        init VisualizationWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        """
        super().__init__()
        self.ui = uic.loadUi("3drekonstruktionspeiseroehre/ui-files/visualization_window_design.ui", self)
        self.master_window = master_window
        self.visualization_data = visualization_data
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        menu_button_2 = QAction("Download", self)
        menu_button_2.triggered.connect(self.__download_file)
        self.ui.menubar.addAction(menu_button_2)

        self.dash_server = None
        self.progress_dialog = QProgressDialog("Visualisierung wird erstellt", None, 0, 100, None)
        self.progress_dialog.setWindowTitle("Fortschritt")
        self.progress_dialog.show()
        self.thread = FigureCreationThread(self.visualization_data)
        self.thread.progress_value.connect(self.__set_progress)
        self.thread.return_value.connect(self.__start_visualization)
        self.thread.start()

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

    def __start_visualization(self, figure_creator):
        """
        callback of the figure creation thread
        :param figure_creator: FigureCreator
        """
        self.visualization_data.figure_creator = figure_creator
        self.dash_server = DashServer(self.visualization_data)
        url = QUrl()
        url.setScheme("http")
        url.setHost("127.0.0.1")
        url.setPort(self.dash_server.get_port())
        self.ui.webView.load(url)

    def __download_file(self):
        """
        Download button callback
        """
        # Prompt the user to choose a destination path
        destination_file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Pickle Files (*.pickle)")
    
        # Save the visualization_data object as a pickle file
        with open(destination_file_path, 'wb') as file:
            pickle.dump(self.visualization_data, file)
        


import pickle
import zipfile
import os
from PyQt5.QtWidgets import QProgressDialog, QMainWindow, QAction, QFileDialog, QGridLayout, QWidget, QMessageBox, QVBoxLayout, QLabel, QSizePolicy,QPushButton, QStyle
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont
from PyQt5 import uic
from dash_server import DashServer
from logic.figure_creator.figure_creation_thread import FigureCreationThread
from gui.master_window import MasterWindow
from gui.info_window import InfoWindow
import gui.file_selection_window 
from logic.patient_data import PatientData
from gui.drag_and_drop import *


class VisualizationWindow(QMainWindow):
    """The window that shows the visualization"""

    def __init__(self, master_window: MasterWindow, patient_data: PatientData):
        """
        init VisualizationWindow
        :param master_window: the MasterWindow in which the next window will be displayed
        :param visualization_data: VisualizationData
        """
        super().__init__()
        self.ui = uic.loadUi("3drekonstruktionspeiseroehre/ui-files/visualization_window_design.ui", self)
        self.master_window = master_window
        # Maximize window to show the whole 3d reconstruction (necessary if visualization_data is imported)
        self.master_window.maximize()
        self.patient_data = patient_data
        self.visualization_data_dict = self.patient_data.visualization_data_dict

        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        menu_button_2 = QAction("Download für Import", self)
        menu_button_2.triggered.connect(self.__download_object_files)
        self.ui.menubar.addAction(menu_button_2)
        menu_button_3 = QAction("Download für Darstellung", self)
        menu_button_3.triggered.connect(self.__download_html_file)
        self.ui.menubar.addAction(menu_button_3)
        menu_button_4 = QAction("Weitere Rekonstruktion einfügen", self)
        menu_button_4.triggered.connect(self.__extend_patient_data)
        menu_button_4.setToolTip("Zurück zur Datei-Auswahl (bisherige Rekonstruktionen bleiben bestehen)")
        self.ui.menubar.addAction(menu_button_4)
        menu_button_5 = QAction("Reset", self)
        menu_button_5.triggered.connect(self.__reset_patient_data)
        menu_button_5.setToolTip("Zurück zur Datei-Auswahl (bisherige Rekonstruktionen werden entfernt)")
        self.ui.menubar.addAction(menu_button_5)

        # Create a grid layout for visualizations
        self.visualization_layout = DragWidget(orientation=Qt.Orientation.Horizontal)


        self.dash_servers = []  # List to store DashServer instances for cleanup
        self.web_views = []  # List to store QWebView instances for cleanup

        self.progress_dialog = QProgressDialog("Visualisierung wird erstellt", None, 0, 100, None)
        self.progress_dialog.setWindowTitle("Fortschritt")
        self.progress_dialog.show()

        # Thread per visualzation data object
        self.thread = [None] * len(self.patient_data.visualization_data_dict)
        for i, (name, visualization_data) in enumerate(self.patient_data.visualization_data_dict.items()):
            self.thread[i] = FigureCreationThread(visualization_data)
            self.thread[i].progress_value.connect(self.__set_progress)
            self.thread[i].return_value.connect(
                lambda figure_creator, viz_data=visualization_data, viz_name=name: self.__start_visualization(figure_creator, viz_data, viz_name)
            )
            self.thread[i].start()

        self.setCentralWidget(self.visualization_layout)


    def __menu_button_clicked(self):
        """
        info-button callback
        """
        info_window = InfoWindow()
        info_window.show_visualization_info()
        info_window.show()

    def closeEvent(self, event):
        """
        Closing-event callback
        :param event:
        """
        for dash_server in self.dash_servers:
            dash_server.stop()

        for web_view in self.web_views:
            web_view.close()

        event.accept()
        

    def __set_progress(self, val):
        """
        progress bar callback
        :param val: new progress value
        """
        if self.progress_dialog:
            self.progress_dialog.setValue(val)

    def __start_visualization(self, figure_creator, visualization_data, visualization_name):
        """
        callback of the figure creation thread
        :param figure_creator: FigureCreator
        :param visualization_data: VisualizationData
        :param visualization_name: Name of the visualization
        """
        visualization_data.figure_creator = figure_creator
        dash_server = DashServer(visualization_data)
        url = QUrl()
        url.setScheme("http")
        url.setHost("127.0.0.1")
        url.setPort(dash_server.get_port())

        # Create a new QVBoxLayout for each visualization
        vbox = QVBoxLayout()
        # Create DragItem to make vboxes drag and droppable
        item = DragItem()

        # Add the label with the visualization name to the vbox
        if "." in visualization_name:
            visualization_name = visualization_name.split(".")[0]
        label = QLabel(visualization_name)
        label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        label.setFont(QFont('Arial', 14))
        vbox.addWidget(label)

        # Create a button with a trash can icon to remove the visualization
        button = QPushButton()
        button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarCloseButton')))
        button.setFixedSize(20, 20)
        button.clicked.connect(lambda _, viz_name=visualization_name, item=item: self.__delete_visualization(viz_name, item)) # Connect the button's clicked signal to the delete visualization method
        vbox.addWidget(button)


        # Create a new QWebEngineView for each visualization
        web_view = QWebEngineView()
        web_view.load(url)
        vbox.addWidget(web_view)

        # Set vbox as the DragItem's layout and add it to the visualization layout
        item.setLayout(vbox)
        self.visualization_layout.add_item(item)
        

        # Save the DashServer and QWebEngineView instances for cleanup later
        self.dash_servers.append(dash_server)
        self.web_views.append(web_view)
    

    def __download_object_files(self):
        """
        Download button callback to save multiple VisualizationData objects as pickle files
        """
        # Prompt the user to choose a destination directory
        destination_directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        # Windows uses backslashes 
        destination_directory = destination_directory.replace('/', '\\')

        if destination_directory:
            # Iterate over each VisualizationData object in the visualization_data_dict
            for name, visualization_data in self.patient_data.visualization_data_dict.items():
                # Generate a file name for each pickle file
                file_name = f"{name.split('.')[0]}.achalasie"
                # Construct the file path by joining the destination directory and the file name
                file_path = os.path.join(str(destination_directory), file_name)

                # Save the VisualizationData object as a pickle file
                with open(file_path, 'wb') as file:
                    pickle.dump(visualization_data, file)

            # Inform the user that the export is complete
            QMessageBox.information(
                self, "Export erfolgreich",
                f"Die Dateien wurden erfolgreich exportiert in {destination_directory}."
            )


    def __download_html_file(self):
        """
        Download button callback
        """
        # Prompt the user to choose a destination path for the zip file
        destination_file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "ZIP Files (*.zip)")
        
        if destination_file_path:
            with zipfile.ZipFile(destination_file_path, 'w') as zip_file:
                # Iterate over each visualization and export its HTML
                for i, dash_server in enumerate(self.dash_servers):
                    figure = dash_server.figure
                    # Generate a unique file name for each HTML file
                    html_file_name = f"figure_{i}.html"
                    # Write the figure to an HTML file
                    figure.write_html(html_file_name)
                    # Add the HTML file to the zip
                    zip_file.write(html_file_name)
                    # Remove the temporary HTML file
                    os.remove(html_file_name)

        # Inform the user that the export is complete
        QMessageBox.information(self, "Export Complete", "HTML Dateien wurden erfolgreich als zip Datei exportiert.")


    def __extend_patient_data(self):
        file_selection_window = gui.file_selection_window.FileSelectionWindow(self.master_window, self.patient_data)
        self.master_window.switch_to(file_selection_window)
        for dash_server in self.dash_servers:
            dash_server.stop()
        for web_view in self.web_views:
            web_view.close()


    def __reset_patient_data(self):
        self.patient_data.visualization_data_dict = {}
        file_selection_window = gui.file_selection_window.FileSelectionWindow(self.master_window, self.patient_data)
        self.master_window.switch_to(file_selection_window)
        for dash_server in self.dash_servers:
            dash_server.stop()
        for web_view in self.web_views:
            web_view.close()
        

    def __delete_visualization(self, visualization_name, viz_item):
        # Remove the item from the layout
        self.visualization_layout.removeItem(viz_item)

        # Find the corresponding web_view and dash_server instances
        web_view = viz_item.layout().itemAt(2).widget()  # Assuming the web_view is at index 2 in the QHBoxLayout
        dash_server = next((server for server in self.dash_servers if server.get_port() == web_view.url().port()), None)

        if dash_server:
            dash_server.stop()  # Stop the DashServer

        self.web_views.remove(web_view)  # Remove the QWebEngineView from the list
        self.dash_servers.remove(dash_server)

        # Clean up the layout
        for i in reversed(range(viz_item.layout().count())):
            viz_item.layout().itemAt(i).widget().setParent(None)
        
        # Clean patient_data
        self.patient_data.remove_visualization(visualization_name)


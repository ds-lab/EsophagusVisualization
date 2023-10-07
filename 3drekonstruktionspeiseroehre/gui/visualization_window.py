import csv
import os
import pickle
import zipfile
import numpy as np

import gui.file_selection_window
from dash_server import DashServer
from gui.drag_and_drop import *
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from logic.figure_creator.figure_creation_thread import FigureCreationThread
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from PyQt5 import uic
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (QAction, QFileDialog, QLabel, QMainWindow,
                             QMessageBox, QProgressDialog, QPushButton,
                             QSizePolicy, QStyle, QVBoxLayout)


class VisualizationWindow(QMainWindow):
    """The window that shows the visualization"""

    def __init__(self, master_window: MasterWindow, patient_data: PatientData):
        """
        Initialize VisualizationWindow

        Args:
            master_window (MasterWindow): The MasterWindow in which the next window will be displayed
            patient_data (PatientData): PatientData object
        """
        super().__init__()
        self.ui = uic.loadUi("./ui-files/visualization_window_design.ui", self)
        self.master_window = master_window
        # Maximize window to show the whole 3d reconstruction (necessary if visualization_data is imported)
        self.master_window.maximize()
        self.patient_data = patient_data
        self.visits = self.patient_data.visit_data_dict

        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        menu_button_2 = QAction("Download für Import", self)
        menu_button_2.triggered.connect(self.__download_object_files)
        self.ui.menubar.addAction(menu_button_2)
        menu_button_3 = QAction("Download für Darstellung", self)
        menu_button_3.triggered.connect(self.__download_html_file)
        self.ui.menubar.addAction(menu_button_3)
        menu_button_6 = QAction("CSV Metriken Download", self)
        menu_button_6.triggered.connect(self.__download_csv_file)
        self.ui.menubar.addAction(menu_button_6)
        menu_button_4 = QAction("Weitere Rekonstruktion einfügen", self)
        menu_button_4.triggered.connect(self.__extend_patient_data)
        self.ui.menubar.addAction(menu_button_4)
        menu_button_5 = QAction("Reset", self)
        menu_button_5.triggered.connect(self.__reset_patient_data)
        self.ui.menubar.addAction(menu_button_5)

        # Create a DragWidget to layout the visualizations
        self.visualization_layout = DragWidget(orientation=Qt.Orientation.Horizontal)

        self.dash_servers = []  # List to store DashServer instances for cleanup
        self.web_views = []  # List to store QWebView instances for cleanup
        # set native menu bar flag as false to see MenuBar on Mac
        self.ui.menubar.setNativeMenuBar(False)

        self.progress_dialog = QProgressDialog("Visualisierung wird erstellt", None, 0, 100, None)
        self.progress_dialog.setWindowTitle("Fortschritt")
        self.progress_dialog.show()

        # Thread per visualzation data object
        self.thread = [None] * len(self.visits)
        for i, (name, visit_data) in enumerate(self.visits.items()):
            self.thread[i] = FigureCreationThread(visit_data)
            self.thread[i].progress_value.connect(self.__set_progress)
            self.thread[i].return_value.connect(
                lambda visit: self.__start_visualization(visit)
            )
            self.thread[i].start()

        self.setCentralWidget(self.visualization_layout)

    def __menu_button_clicked(self):
        """
        Callback for the info-button
        """
        info_window = InfoWindow()
        info_window.show_visualization_info()
        info_window.show()

    def closeEvent(self, event):
        """
        Callback for the closing event
        """
        for dash_server in self.dash_servers:
            dash_server.stop()

        for web_view in self.web_views:
            web_view.close()

        event.accept()

    def __set_progress(self, val):
        """
        Callback for the progress bar

        Args:
            val (int): New progress value
        """
        if self.progress_dialog:
            self.progress_dialog.setValue(val)

    def __start_visualization(self, visit: VisitData):
        """
        Callback of the figure creation thread

        Args:
            visit (VisitData): VisitData object
        """
        dash_server = DashServer(visit)
        url = QUrl()
        url.setScheme("http")
        url.setHost("127.0.0.1")
        url.setPort(dash_server.get_port())

        # Create a new QVBoxLayout for each visualization
        vbox = QVBoxLayout()
        # Create DragItem to make vboxes drag and droppable
        item = DragItem()

        # Add the label with the visualization name to the vbox
        if "." in visit.name:
            visit_name = visit.name.split(".")[0]
        else:
            visit_name = visit.name
        label = QLabel(visit_name)
        label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        label.setFont(QFont('Arial', 14))
        vbox.addWidget(label)

        # Create a button with a trash can icon that triggers the removal of the visualization
        button = QPushButton()
        button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarCloseButton')))
        button.setFixedSize(20, 20)
        button.clicked.connect(lambda _, visit_name=visit_name, item=item: self.__delete_visualization(visit_name,
                                                                                                       item))  # Connect the button's clicked signal to the delete visualization method
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
        Callback for the download button to save multiple VisualizationData objects as pickle files
        """

        # Prompt the user to choose a destination directory
        destination_directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        # Windows uses backslashes 
        destination_directory = destination_directory.replace('/', '\\')

        if destination_directory:
            # Iterate over each VisualizationData object in the visit_data_dict
            for name, visit_data in self.patient_data.visit_data_dict.items():
                # Generate a file name for each pickle file
                file_name = f"{name.split('.')[0]}.achalasie"
                # Construct the file path by joining the destination directory and the file name
                file_path = os.path.join(str(destination_directory), file_name)

                # Save the VisualizationData object as a pickle file (*.achalasie)
                with open(file_path, 'wb') as file:
                    pickle.dump(visit_data, file)

            # Inform the user that the export is complete
            QMessageBox.information(
                self, "Export erfolgreich",
                f"Die Dateien wurden erfolgreich exportiert in {destination_directory}."
            )

    def __download_html_file(self):
        """
        Callback for the download button to store visible graphs as .html files with their current coloring
        """
        # Prompt the user to choose a destination path for the zip file
        destination_file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "ZIP Files (*.zip)")

        if destination_file_path:
            with zipfile.ZipFile(destination_file_path, 'w') as zip_file:
                # Iterate over each visualization and export its HTML
                for i, dash_server in enumerate(self.dash_servers):
                    figure = dash_server.current_figure
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

    def __download_csv_file(self):

        # Prompt the user to choose a destination path for the csv file
        destination_file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")

        if destination_file_path:
            with open(destination_file_path, "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Id", "Breischluckbild", "Tubular Index (Mean)", "Sphinkter Index (Mean)", "Volume Tubular",
                                 "Volume Sphinkter", "Pressure Tubular (Max)", "Pressure Sphinkter (Max)", "Index Tublar (Max)",
                                 "Index Sphinkter (Max)", "Index Tublar (Min)", "Index Sphinkter (Min)", "Esophagus Length (cm)"])


                for i, (name, visit_data) in enumerate(self.visits.items()):

                    if "." in name:
                        visit_name = name.split(".")[0]
                    else:
                        visit_name = name

                    for j in range(len(visit_data.visualization_data_list)):
                        xray_name = visit_data.visualization_data_list[j].xray_filename.split("/")[-1].split(".")[0]
                        tubular_metric = visit_data.visualization_data_list[j].figure_creator.get_metrics()[0]
                        sphinkter_metric = visit_data.visualization_data_list[j].figure_creator.get_metrics()[1]
                        volume_tubular = visit_data.visualization_data_list[j].figure_creator.get_metrics()[2]
                        volume_sphinkter = visit_data.visualization_data_list[j].figure_creator.get_metrics()[3]
                        max_pressure_tubular = visit_data.visualization_data_list[j].figure_creator.get_metrics()[4]
                        max_pressure_sphinkter = visit_data.visualization_data_list[j].figure_creator.get_metrics()[5]
                        max_metric_tubular = visit_data.visualization_data_list[j].figure_creator.get_metrics()[6]
                        max_metric_sphinkter = visit_data.visualization_data_list[j].figure_creator.get_metrics()[7]
                        min_metric_tubular = visit_data.visualization_data_list[j].figure_creator.get_metrics()[8]
                        min_metric_sphinkter = visit_data.visualization_data_list[j].figure_creator.get_metrics()[9]
                        esophagus_length = visit_data.visualization_data_list[j].figure_creator.get_esophagus_full_length_cm()

                    writer.writerow([visit_name, xray_name, round(np.mean(tubular_metric), 2),
                                     round(np.mean(sphinkter_metric), 2), round(volume_tubular, 2),
                                     round(volume_sphinkter, 2), round(max_pressure_tubular, 2),
                                     round(max_pressure_sphinkter, 2), round(max_metric_tubular, 2),
                                     round(max_metric_sphinkter, 2), round(min_metric_tubular, 2),
                                     round(min_metric_sphinkter, 2),
                                     round(esophagus_length, 2)])

                # Inform the user that the export is complete
        QMessageBox.information(self, "Export Complete",
                                "csv Datei wurde erfolgreich exportiert.")

    def __extend_patient_data(self):
        """
        Callback for extending patient data
        """
        # Open File selection window
        file_selection_window = gui.file_selection_window.FileSelectionWindow(self.master_window, self.patient_data)
        self.master_window.switch_to(file_selection_window)

        # Stop all threads
        for dash_server in self.dash_servers:
            dash_server.stop()
        for web_view in self.web_views:
            web_view.close()

    def __reset_patient_data(self):
        """
        Callback for resetting patient data
        """
        # Empty the patient data object
        self.patient_data.visit_data_dict = {}

        # Open file selection window
        file_selection_window = gui.file_selection_window.FileSelectionWindow(self.master_window, self.patient_data)
        self.master_window.switch_to(file_selection_window)

        # Stop all threads
        for dash_server in self.dash_servers:
            dash_server.stop()
        for web_view in self.web_views:
            web_view.close()

    def __delete_visualization(self, visit_name, visit_item):
        """
        Callback for deleting a visualization

        Args:
            visit_name (str): Name of the visit to delete
            visit_item (DragItem): GUI item of the visit to delete
        """

        # Remove the item from the layout
        self.visualization_layout.removeItem(visit_item)

        # Find the corresponding web_view and dash_server instances
        web_view = visit_item.layout().itemAt(2).widget()  # Assuming the web_view is at index 2 in the QHBoxLayout
        dash_server = next((server for server in self.dash_servers if server.get_port() == web_view.url().port()), None)

        if dash_server:
            dash_server.stop()  # Stop the DashServer
            self.dash_servers.remove(dash_server)

        self.web_views.remove(web_view)  # Remove the QWebEngineView from the list

        # Clean up the layout
        for i in reversed(range(visit_item.layout().count())):
            visit_item.layout().itemAt(i).widget().setParent(None)

        # Clean patient_data
        self.patient_data.remove_visit(visit_name)

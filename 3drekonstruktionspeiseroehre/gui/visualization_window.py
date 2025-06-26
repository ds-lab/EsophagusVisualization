import csv
import os
import pickle
import re

import numpy as np

from dash_server import DashServer
from gui.drag_and_drop import *
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.show_message import ShowMessage
import gui.data_window
from logic.figure_creator.figure_creation_thread import FigureCreationThread
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from logic.database import database
from logic.services.reconstruction_service import ReconstructionService

from PyQt6 import uic
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (QFileDialog, QLabel, QMainWindow,       # QAction
                             QMessageBox, QProgressDialog, QPushButton,
                             QSizePolicy, QStyle, QVBoxLayout)
import pyvista as pv


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
        self.setAcceptDrops(True)
        self.ui = uic.loadUi("./ui-files/visualization_window_design.ui", self)
        self.master_window = master_window
        # Maximize window to show the whole 3d reconstruction (necessary if visualization_data is imported)
        self.master_window.maximize()
        self.patient_data = patient_data
        self.visits = self.patient_data.visit_data_dict

        self.db = database.get_db()
        self.reconstruction_service = ReconstructionService(self.db)

        # Create Menu-Buttons
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        # Saving the Reconstruction as a file is not used, because it should be saved in the DB
        #menu_button_2 = QAction("Save Reconstruction as file", self)
        #menu_button_2.triggered.connect(self.__download_object_files)
        #self.ui.menubar.addAction(menu_button_2)
        menu_button_3 = QAction("Download for Display", self)
        menu_button_3.triggered.connect(self.__download_html_file)
        self.ui.menubar.addAction(menu_button_3)
        menu_button_6 = QAction("CSV Metrics Download", self)
        menu_button_6.triggered.connect(self.__download_csv_file)
        self.ui.menubar.addAction(menu_button_6)
        menu_button_7 = QAction("Download for 3d-Printing", self)
        menu_button_7.triggered.connect(self.__download_stl_file)
        self.ui.menubar.addAction(menu_button_7)
        menu_button_8 = QAction("Save in Reconstruction in DB", self)
        menu_button_8.triggered.connect(self.__save_reconstruction_in_db)
        self.ui.menubar.addAction(menu_button_8)
        menu_button_4 = QAction("Add Reconstruction(s)", self)
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

        self.progress_dialog = QProgressDialog("Creating Visualisation", None, 0, 100, None)
        self.progress_dialog.setWindowTitle("Processing...")
        self.progress_dialog.show()

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
        #label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        label.setFont(QFont('Arial', 14))
        vbox.addWidget(label)

        # Create a button with a trash can icon that triggers the removal of the visualization
        button = QPushButton()
        #button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarCloseButton')))
        button.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_TitleBarCloseButton')))
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
                print(f"visit_data: {visit_data}")
                # Generate a file name for each pickle file
                file_name = f"{name.split('.')[0]}.achalasie"
                # Construct the file path by joining the destination directory and the file name
                file_path = os.path.join(str(destination_directory), file_name)

                # Save the VisualizationData object as a pickle file (*.achalasie)
                with open(file_path, 'wb') as file:
                    pickle.dump(visit_data, file)

            # Inform the user that the export is complete
            QMessageBox.information(
                self, "Export Successful",
                f"The files were successfully exported to {destination_directory}."
            )

    def __save_reconstruction_in_db(self):
        try:
            savings = False
            for name, visit_data in self.patient_data.visit_data_dict.items():
                match = re.search(r'Visit_ID_(\d+)', name)
                visit = match.group(1)
                reconstruction_bytes = pickle.dumps(visit_data)
                reconstruction = self.reconstruction_service.get_reconstruction_for_visit(visit)
                if not reconstruction or reconstruction and ShowMessage.to_update_for_visit_named("3d reconstruction(s)", name):
                    reconstruction_dict = {'visit_id': visit,
                                           'reconstruction_file': reconstruction_bytes}
                    if reconstruction:
                        self.reconstruction_service.update_reconstruction(reconstruction.reconstruction_id, reconstruction_dict)
                        if self.reconstruction_service.get_reconstruction_for_visit(visit):
                            savings = True

                        # Inform the user about the saving
                        if savings:
                            QMessageBox.information(
                                self, "Saving done",
                                f"Reconstruction(s) for the visit {name} has/have been saved in the database."
                            )
                        else:
                            QMessageBox.information(
                                self, "Saving failed",
                                f"The saving of the reconstruction(s) for the visit {name} to the database failed."
                            )
                    else:
                        self.reconstruction_service.create_reconstruction(reconstruction_dict)
                        if self.reconstruction_service.get_reconstruction_for_visit(visit):
                            savings = True

                        # Inform the user about the saving
                        if savings:
                            QMessageBox.information(
                                self, "Saving done",
                                f"Reconstruction(s) for the visit {name} has/have been saved in the database."
                            )
                        else:
                            QMessageBox.information(
                                self, "Saving failed",
                                f"The saving of the reconstruction(s) for the visit {name} to the database failed."
                            )
        except Exception as e:
            QMessageBox.information(
                self, "Saving failed",
                f"The saving of the reconstruction(s) for the visit {name}  to the database failed."
            )

    def __download_html_file(self):
        """
        Callback for the download button to store visible graphs as .html files with their current coloring
        """
         # Prompt the user to choose a destination directory
        destination_directory = QFileDialog.getExistingDirectory(self, "Select Directory")

        try:
            export_successful = False
            # Iterate over each visualization and export its HTML
            for i, dash_server in enumerate(self.dash_servers):
                figure = dash_server.current_figure
                # Generate a unique file name for each HTML file
                html_file_name = f"figure_{dash_server.visit.name}.html"
                # Construct the file path by joining the destination directory and the file name
                file_path = os.path.join(str(destination_directory), html_file_name)
                # Write the figure to an HTML file
                figure.write_html(file_path)
            # Check if the file was actually created
            if os.path.exists(file_path):
                export_successful = True
            else:
                print(f"Failed to create file: {file_path}")

            # Inform the user that the export is complete
            if export_successful:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"The files have been successfully exported to {destination_directory}.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "No files were exported. There might be an issue with the data or permissions.",
                )

        # Inform user that the export failed
        except Exception as e:
            print(f"An error occurred during export: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during the export process: {str(e)}",
            )

    def __download_stl_file(self):
        """
        Callback for the download button to store graphs as .stl for 3d printing
        """

        # Prompt the user to choose a destination directory
        destination_directory = QFileDialog.getExistingDirectory(
            self, "Select Directory"
        )

        if not destination_directory:
            print("User cancelled the directory selection")
            return  # Exit the method if no directory was selected

        # Use os.path.normpath to normalize the path for the current operating system
        destination_directory = os.path.normpath(destination_directory)
        # # Windows uses backslashes
        # destination_directory = destination_directory.replace("/", "\\")

        try:
            export_successful = False
            # loop through all visits.items (these are figures which are displayed in different threads)
            for i, (name, visit_data) in enumerate(self.visits.items()):
                visit_name = name.split(".")[0] if "." in name else name

                # loop though all X_ray pictures/"Breischluckbilder" of a particular visit_data
                for j in range(len(visit_data.visualization_data_list)):
                    # extract the name
                    xray_name = visit_data.visualization_data_list[j].xray_minute
                    # get the data to create the .stl-object
                    figure_x = visit_data.visualization_data_list[j].figure_x
                    figure_y = visit_data.visualization_data_list[j].figure_y
                    figure_z = visit_data.visualization_data_list[j].figure_z

                    # create file_name and file_path for each object
                    file_name = visit_name + "_" + str(xray_name) + ".stl"
                    # Construct the file path by joining the destination directory and the file name
                    file_path = os.path.join(str(destination_directory), file_name)

                    # convert the data of the figure into the correct format
                    points = np.array([figure_x.flatten(), figure_y.flatten(), figure_z.flatten()])
                    points = points.transpose(1, 0)

                    # create the 3d-object
                    points = pv.wrap(points)
                    surface = points.reconstruct_surface()

                    # Save Object for 3d printing
                    pv.save_meshio(file_path, surface)

            # Check if the file was actually created
            if os.path.exists(file_path):
                export_successful = True
            else:
                print(f"Failed to create file: {file_path}")

            # Inform the user that the export is complete
            if export_successful:
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"The files have been successfully exported to {destination_directory}.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "No files were exported. There might be an issue with the data or permissions.",
                )

        # Inform user that the export failed
        except Exception as e:
            print(f"An error occurred during export: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during the export process: {str(e)}",
            )

    def __download_csv_file(self):
        """
        Callback for the download button to store a csv-file of the metrics of all loaded visualizations
        """
        self.__download_overall_csv_file()
        self.__download_timeframe_csv_file()

    def __download_overall_csv_file(self):
        """
        Callback for the download button to store a overall csv-file of the metrics of all loaded visualizations
        """
        # Prompt the user to choose a destination path for the csv file
        title = f"overall_metrics_"
        destination_file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV Overall-Metrics File", title, "CSV Files (*.csv)")

        if not destination_file_path:
            print("User cancelled the directory selection")
            return  # Exit the method if no directory was selected

        try:
            export_successful = False
            with open(destination_file_path, "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(
                    ["Id-Visit","Id-Picture",
                     "Volume Tubular", "Volume Sphincter", "Esophagus Length (cm)",
                     "Mean over all (Volume * max(tubular pressure from frame))",
                     "Mean over all (Volume * min(tubular pressure from frame))",
                     "Mean over all (Volume * mean(tubular pressure from frame))",
                     "Mean over all (Volume / max(sphincter pressure from frame))",
                     "Mean over all (Volume / min(sphincter pressure from frame))",
                     "Mean over all (Volume / mean(sphincter pressure from frame))",
                     "Tubular Pressure Max", "Tubular Pressure Min", "Tubular Pressure Mean",
                     "Sphincter Pressure Max", "Sphincter Pressure Min", "Sphincter Pressure Mean", "Esophageal Pressurization Index"
                     ])

                # loop through all visits.items (these are figures which are displayed in different threads)
                for i, (name, visit_data) in enumerate(self.visits.items()):
                    if "." in name:
                        visit_name = name.split(".")[0]
                    else:
                        visit_name = name
                    # loop though all X_ray pictures/"Breischluckbilder" of a particular visit_data
                    for j in range(len(visit_data.visualization_data_list)):
                        id_minute = visit_data.visualization_data_list[j].xray_minute
                        metrics = visit_data.visualization_data_list[j].figure_creator.get_metrics()
                        tubular_metric_mean = metrics['metric_tubular_overall']['mean']
                        tubular_metric_min = metrics['metric_tubular_overall']['min']
                        tubular_metric_max = metrics['metric_tubular_overall']['max']
                        sphincter_metric_mean = metrics['metric_sphincter_overall']['mean']
                        sphincter_metric_min = metrics['metric_sphincter_overall']['min']
                        sphincter_metric_max = metrics['metric_sphincter_overall']['max']
                        tubular_pressure_mean = metrics['pressure_tubular_overall']['mean']
                        tubular_pressure_min = metrics['pressure_tubular_overall']['min']
                        tubular_pressure_max = metrics['pressure_tubular_overall']['max']
                        sphincter_pressure_mean = metrics['pressure_sphincter_overall']['mean']
                        sphincter_pressure_min = metrics['pressure_sphincter_overall']['min']
                        sphincter_pressure_max = metrics['pressure_sphincter_overall']['max']
                        volume_tubular = metrics['volume_sum_tubular']
                        volume_sphincter = metrics['volume_sum_sphincter']
                        esophagus_length = visit_data.visualization_data_list[j].figure_creator.get_esophagus_full_length_cm()
                        esophageal_pressurization_index = metrics['esophageal_pressurization_index']

                        # Write metrics data to CSV file
                        writer.writerow([visit_name.encode("utf-8"), id_minute,
                                         round(volume_tubular, 4), round(volume_sphincter, 4), round(esophagus_length, 4),
                                         round(tubular_metric_max, 4), round(tubular_metric_min, 4), round(tubular_metric_mean, 4),
                                         round(sphincter_metric_max, 4), round(sphincter_metric_min, 4), round(sphincter_metric_mean, 4),
                                         round(tubular_pressure_max, 4), round(tubular_pressure_min, 4), round(tubular_pressure_mean, 4),
                                         round(sphincter_pressure_max, 4), round(sphincter_pressure_min, 4), round(sphincter_pressure_mean, 4), round(esophageal_pressurization_index, 4)])

            # Check if the file was actually created
            if os.path.exists(destination_file_path):
                export_successful = True
            else:
                print(f"Failed to create file: {destination_file_path}")

            if export_successful:
                # Inform the user that the export is complete
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"The files have been successfully exported to {destination_file_path}.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "No files were exported. There might be an issue with the data or permissions.",
                )
        except Exception as e:
            # Inform user that the export failed
            print(f"An error occurred during export: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during the export process: {str(e)}",
            )

    def __download_timeframe_csv_file(self):
        """
        Callback for the download button to store a timeframe dependent csv-file of the metrics of all loaded visualizations
        """
        title = f"timeframe_metrics_"
        destination_file_path_metriks, _ = QFileDialog.getSaveFileName(self, "Save CSV Timeframe-Metrics File", title, "CSV Files (*.csv)")

        if not destination_file_path_metriks:
            print("User cancelled the directory selection")
            return  # Exit the method if no directory was selected

        try:
            export_successful = False
            with open(destination_file_path_metriks, "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(
                    ["Id-Visit", "Id-Picture", "Frame", "Length Tubular", "Length Sphincter", "Volume Tubular", "Volume Sphincter", "Max tubular pressure in frame", "Min tubular pressure in frame", "Mean tubular pressure in frame",
                     "Volume * max(tubular pressure from frame)", "Volume * min(tubular pressure from frame)", "Volume * mean(tubular pressure from frame)",
                     "Max sphincter pressure in frame", "Min sphincter pressure in frame", "Mean sphincter pressure in frame",
                     "Volume / max(sphincter pressure from frame)", "Volume / min(sphincter pressure from frame)", "Volume / mean(sphincter pressure from frame)"])

                # loop through all visits.items (these are figures which are displayed in different threads)
                for i, (name, visit_data) in enumerate(self.visits.items()):

                    if "." in name:
                        visit_name = name.split(".")[0]
                    else:
                        visit_name = name

                    # loop though all X_ray pictures/"Breischluckbilder" of a particular visit_data
                    for j in range(len(visit_data.visualization_data_list)):
                        metrics = visit_data.visualization_data_list[j].figure_creator.get_metrics()
                        id_minute = visit_data.visualization_data_list[j].xray_minute
                        for frame in range(len(metrics['metric_tubular']['max'])):
                            max_pressure_tubular_per_frame = metrics['pressure_tubular_per_frame']['max'][frame]
                            min_pressure_tubular_per_frame = metrics['pressure_tubular_per_frame']['min'][frame]
                            mean_pressure_tubular_per_frame = metrics['pressure_tubular_per_frame']['mean'][frame]
                            max_pressure_sphincter_per_frame = metrics['pressure_sphincter_per_frame']['max'][frame]
                            min_pressure_sphincter_per_frame = metrics['pressure_sphincter_per_frame']['min'][frame]
                            mean_pressure_sphincter_per_frame = metrics['pressure_sphincter_per_frame']['mean'][frame]
                            metric_max_tubular = metrics['metric_tubular']['max'][frame]
                            metric_min_tubular = metrics['metric_tubular']['min'][frame]
                            metric_mean_tubular = metrics['metric_tubular']['mean'][frame]
                            metric_max_sphincter = metrics['metric_sphincter']['max'][frame]
                            metric_min_sphincter = metrics['metric_sphincter']['min'][frame]
                            metric_mean_sphincter = metrics['metric_sphincter']['mean'][frame]
                            volume_tubular = metrics['volume_sum_tubular']
                            volume_sphincter = metrics['volume_sum_sphincter']
                            len_tubular = metrics['len_tubular']
                            len_sphincter = metrics['len_sphincter']

                            # Write metrics data to CSV file
                            writer.writerow([visit_name.encode("utf-8"), id_minute, frame, round(len_tubular, 4), round(len_sphincter, 4), round(volume_tubular, 4), round(volume_sphincter, 4),
                                             round(max_pressure_tubular_per_frame, 4),round(min_pressure_tubular_per_frame, 4),round(mean_pressure_tubular_per_frame, 4),
                                             round(metric_max_tubular, 4), round(metric_min_tubular, 4), round(metric_mean_tubular, 4),
                                             round(max_pressure_sphincter_per_frame, 4),round(min_pressure_sphincter_per_frame, 4),round(mean_pressure_sphincter_per_frame, 4),
                                             round(metric_max_sphincter, 4), round(metric_min_sphincter, 4), round(metric_mean_sphincter, 4)])
            # Check if the file was actually created
            if os.path.exists(destination_file_path_metriks):
                export_successful = True
            else:
                print(f"Failed to create file: {destination_file_path_metriks}")


            if export_successful:
                # Inform the user that the export is complete
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"The files have been successfully exported to {destination_file_path_metriks}.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    "No files were exported. There might be an issue with the data or permissions.",
                )

        except Exception as e:
            # Inform user that the export failed
            print(f"An error occurred during export: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred during the export process: {str(e)}",
            )


    def __extend_patient_data(self):
        """
        Callback for extending patient data
        """
        # Open the Data Window to enable selection of new data
        data_window = gui.data_window.DataWindow(self.master_window, self.patient_data)
        self.master_window.switch_to(data_window)

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

        # Open the Data Window to enable selection of new data
        data_window = gui.data_window.DataWindow(self.master_window, self.patient_data)
        self.master_window.switch_to(data_window)

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

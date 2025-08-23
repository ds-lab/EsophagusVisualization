import csv
import os
import pickle
import re

import numpy as np
import pandas as pd

from dash_server import DashServer
from gui.base_workflow_window import BaseWorkflowWindow
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
from utils.path_utils import resource_path
from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtWidgets import QFileDialog, QLabel, QMessageBox, QProgressDialog, QPushButton, QSizePolicy, QStyle, QVBoxLayout
import pyvista as pv


class VisualizationWindow(BaseWorkflowWindow):
    """The window that shows the visualization"""

    def __init__(self, master_window: MasterWindow, patient_data: PatientData):
        """
        Initialize VisualizationWindow

        Args:
            master_window (MasterWindow): The MasterWindow in which the next window will be displayed
            patient_data (PatientData): PatientData object
        """
        # Call parent constructor with available data
        super().__init__(master_window, patient_data, None, None)

        self.setAcceptDrops(True)
        self.ui = uic.loadUi(resource_path("ui-files/visualization_window_design.ui"), self)

        # Setup navigation buttons after UI is loaded
        self._setup_navigation_buttons()

        # Maximize window to show the whole 3d reconstruction (necessary if visualization_data is imported)
        self.master_window.maximize()
        self.visits = self.patient_data.visit_data_dict

        self.db = database.get_db()
        self.reconstruction_service = ReconstructionService(self.db)

        # Create Menu-Buttons
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)
        # Saving the Reconstruction as a file is not used, because it should be saved in the DB
        # menu_button_2 = QAction("Save Reconstruction as file", self)
        # menu_button_2.triggered.connect(self.__download_object_files)
        # self.ui.menubar.addAction(menu_button_2)
        menu_button_3 = QAction("Download for Display", self)
        menu_button_3.triggered.connect(self.__download_html_file)
        self.ui.menubar.addAction(menu_button_3)
        menu_button_6 = QAction("CSV Metrics Download", self)
        menu_button_6.triggered.connect(self.__download_csv_file)
        self.ui.menubar.addAction(menu_button_6)
        menu_button_7 = QAction("Download for 3d-Printing", self)
        menu_button_7.triggered.connect(self.__download_stl_file)
        self.ui.menubar.addAction(menu_button_7)
        # Add VTKHDF export for ML with pressure and anatomical attributes
        menu_button_vtkhdf = QAction("Download VTKHDF for ML", self)
        menu_button_vtkhdf.triggered.connect(self.__download_vtkhdf_file)
        self.ui.menubar.addAction(menu_button_vtkhdf)
        menu_button_8 = QAction("Save in Reconstruction in DB", self)
        menu_button_8.triggered.connect(self.__save_reconstruction_in_db)
        self.ui.menubar.addAction(menu_button_8)
        # Adjust segmentation entry point
        menu_button_adjust = QAction("Adjust current Reconstruction(s)", self)
        menu_button_adjust.triggered.connect(self.__adjust_current_segmentation)
        self.ui.menubar.addAction(menu_button_adjust)
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
            self.thread[i].return_value.connect(lambda visit: self.__start_visualization(visit))
            self.thread[i].error_occurred.connect(self.__handle_error)
            self.thread[i].start()

        self.setCentralWidget(self.visualization_layout)

        # Ensure the progress dialog stays in front of the main window
        self.progress_dialog = QProgressDialog("Creating Visualization", None, 0, 100, self)
        self.progress_dialog.setWindowTitle("Processing...")
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.progress_dialog.show()
        try:
            self.progress_dialog.raise_()
            self.progress_dialog.activateWindow()
        except Exception:
            pass
        # Center the progress dialog after it is shown (ensure final size is known)
        try:
            QTimer.singleShot(0, self.__center_progress_dialog)
        except Exception:
            pass

    def __center_progress_dialog(self):
        try:
            if hasattr(self, "progress_dialog") and self.progress_dialog:
                self.progress_dialog.adjustSize()
                parent_rect = self.frameGeometry()
                dlg_rect = self.progress_dialog.frameGeometry()
                dlg_rect.moveCenter(parent_rect.center())
                self.progress_dialog.move(dlg_rect.topLeft())
        except Exception:
            pass

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
        # Stop all figure creation threads
        if hasattr(self, "thread") and self.thread:
            for thread in self.thread:
                if thread and thread.isRunning():
                    thread.terminate()
                    thread.wait()  # Wait for thread to finish

        # Close progress dialog if it exists
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # Stop all dash servers (ensure shutdown)
        for dash_server in getattr(self, "dask_servers", []) or []:
            # typo safeguard, do nothing
            pass
        for dash_server in getattr(self, "dash_servers", []) or []:
            try:
                dash_server.stop()
            except Exception:
                # Ignore errors when stopping servers that might already be stopped
                pass

        # Close all web views
        for web_view in getattr(self, "web_views", []) or []:
            try:
                web_view.close()
            except Exception:
                # Ignore errors when closing views that might already be closed
                pass

        event.accept()

    def __set_progress(self, val):
        """
        Callback for the progress bar

        Args:
            val (int): New progress value
        """
        if self.progress_dialog:
            self.progress_dialog.setValue(val)

    def __handle_error(self, error_message):
        """
        Handle errors from figure creation threads

        Args:
            error_message (str): The error message
        """
        # Close progress dialog
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # Show error message to user
        QMessageBox.critical(
            self,
            "Visualization Error",
            f"An error occurred while creating the visualization:\n\n{error_message}\n\n" "Please go back and check your segmentation data.",
        )

        # Go back to the previous window
        self._handle_back_button()

    def __start_visualization(self, visit: VisitData):
        """
        Callback of the figure creation thread

        Args:
            visit (VisitData): VisitData object
        """
        dash_server = DashServer(visit)
        # Use explicit URL string including trailing slash
        url = QUrl(f"http://127.0.0.1:{dash_server.get_port()}/")

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
        # label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        label.setFont(QFont("Arial", 14))
        vbox.addWidget(label)

        # Create a button with a trash can icon that triggers the removal of the visualization
        button = QPushButton()
        # button.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_TitleBarCloseButton')))
        button.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, "SP_TitleBarCloseButton")))
        button.setFixedSize(20, 20)
        button.clicked.connect(
            lambda _, visit_name=visit_name, item=item: self.__delete_visualization(visit_name, item)
        )  # Connect the button's clicked signal to the delete visualization method
        vbox.addWidget(button)

        # Create a new QWebEngineView for each visualization
        web_view = QWebEngineView()
        # Use an isolated, in-memory web profile per view to avoid stale cache/service-worker issues under Windows
        profile = QWebEngineProfile(f"dash_view_{dash_server.get_port()}", web_view)
        try:
            # Prefer ephemeral in-memory cache/cookies
            profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
            profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        except Exception:
            pass
        web_view.setPage(QWebEnginePage(profile, web_view))
        # Load with a short delay and retry on failure (helps on Windows where
        # the server might not yet accept connections at first attempt)
        self.__load_webview_with_retries(web_view, url, max_attempts=20, delay_ms=250)
        vbox.addWidget(web_view)

        # Set vbox as the DragItem's layout and add it to the visualization layout
        item.setLayout(vbox)
        self.visualization_layout.add_item(item)

        # Save the DashServer and QWebEngineView instances for cleanup later
        self.dash_servers.append(dash_server)
        self.web_views.append(web_view)

    def __load_webview_with_retries(self, web_view: QWebEngineView, url: QUrl, max_attempts: int = 15, delay_ms: int = 200):
        """
        Ensure the given QWebEngineView loads the URL reliably by retrying a few
        times with a small delay. This mitigates race conditions between server
        startup and the first navigation attempt (observed under Windows).
        """

        web_view.setProperty("retry_count", 0)

        def _on_finished(ok, w=web_view, u=url):
            if ok:
                try:
                    w.loadFinished.disconnect()
                except Exception:
                    pass
                return
            retries = w.property("retry_count") or 0
            if retries < max_attempts:
                w.setProperty("retry_count", retries + 1)
                QTimer.singleShot(delay_ms, lambda w=w, u=u: w.load(u))
            else:
                try:
                    w.loadFinished.disconnect()
                except Exception:
                    pass

        web_view.loadFinished.connect(_on_finished)
        QTimer.singleShot(delay_ms, lambda w=web_view, u=url: w.load(u))

    def __download_object_files(self):
        """
        Callback for the download button to save multiple VisualizationData objects as pickle files
        """

        # Prompt the user to choose a destination directory
        destination_directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        # Windows uses backslashes
        destination_directory = destination_directory.replace("/", "\\")

        if destination_directory:
            # Iterate over each VisualizationData object in the visit_data_dict
            for name, visit_data in self.patient_data.visit_data_dict.items():
                print(f"visit_data: {visit_data}")
                # Generate a file name for each pickle file
                file_name = f"{name.split('.')[0]}.achalasie"
                # Construct the file path by joining the destination directory and the file name
                file_path = os.path.join(str(destination_directory), file_name)

                # Save the VisualizationData object as a pickle file (*.achalasie)
                with open(file_path, "wb") as file:
                    pickle.dump(visit_data, file)

            # Inform the user that the export is complete
            QMessageBox.information(self, "Export Successful", f"The files were successfully exported to {destination_directory}.")

    def __save_reconstruction_in_db(self):
        try:
            savings = False
            for name, visit_data in self.patient_data.visit_data_dict.items():
                match = re.search(r"Visit_ID_(\d+)", name)
                visit = match.group(1)
                reconstruction_bytes = pickle.dumps(visit_data)
                reconstruction = self.reconstruction_service.get_reconstruction_for_visit(visit)
                if not reconstruction or reconstruction and ShowMessage.to_update_for_visit_named("3d reconstruction(s)", name):
                    reconstruction_dict = {"visit_id": visit, "reconstruction_file": reconstruction_bytes}
                    if reconstruction:
                        self.reconstruction_service.update_reconstruction(reconstruction.reconstruction_id, reconstruction_dict)
                        if self.reconstruction_service.get_reconstruction_for_visit(visit):
                            savings = True

                        # Inform the user about the saving
                        if savings:
                            QMessageBox.information(self, "Saving done", f"Reconstruction(s) for the visit {name} has/have been saved in the database.")
                        else:
                            QMessageBox.information(self, "Saving failed", f"The saving of the reconstruction(s) for the visit {name} to the database failed.")
                    else:
                        self.reconstruction_service.create_reconstruction(reconstruction_dict)
                        if self.reconstruction_service.get_reconstruction_for_visit(visit):
                            savings = True

                        # Inform the user about the saving
                        if savings:
                            QMessageBox.information(self, "Saving done", f"Reconstruction(s) for the visit {name} has/have been saved in the database.")
                        else:
                            QMessageBox.information(self, "Saving failed", f"The saving of the reconstruction(s) for the visit {name} to the database failed.")
        except Exception as e:
            QMessageBox.information(self, "Saving failed", f"The saving of the reconstruction(s) for the visit {name}  to the database failed.")

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
                QMessageBox.information(self, "Export Successful", f"The files have been successfully exported to {destination_directory}.")
            else:
                QMessageBox.warning(self, "Export Failed", "No files were exported. There might be an issue with the data or permissions.")

        # Inform user that the export failed
        except Exception as e:
            print(f"An error occurred during export: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"An error occurred during the export process: {str(e)}")

    def __download_stl_file(self):
        """
        Callback for the download button to store graphs as .stl for 3d printing
        """

        # Prompt the user to choose a destination directory
        destination_directory = QFileDialog.getExistingDirectory(self, "Select Directory")

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
                QMessageBox.information(self, "Export Successful", f"The files have been successfully exported to {destination_directory}.")
            else:
                QMessageBox.warning(self, "Export Failed", "No files were exported. There might be an issue with the data or permissions.")

        # Inform user that the export failed
        except Exception as e:
            print(f"An error occurred during export: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"An error occurred during the export process: {str(e)}")

    def __download_vtkhdf_file(self):
        """
        Callback for the download button to store graphs as .vtkhdf for ML with enhanced attributes
        """
        from PyQt6.QtWidgets import QInputDialog
        import config

        if not self.visits:
            QMessageBox.warning(self, "Export Error", "No visualizations to export.")
            return

        frame_options = [
            "No vertex pressure data (~5MB)",
            "Per-slice HRM pressure data (compact per-height values, ~10MB)",
            "All vertex pressure data (Complete data, potentially large files, ~100MB+)",
        ]

        # Use HTML for proper line breaks in the label
        dialog_text = (
            "What vertex pressure data would you like to export?"
            "<ul>"
            "<li><b>No vertex pressure data:</b> Only 3D geometry, metadata, and pressure statistics. Smallest files (~5MB)</li>"
            "<li><b>Per-slice HRM pressure data:</b> Compact per-height values across frames. Smaller files (~10MB)</li>"
            "<li><b>All vertex pressure data:</b> Complete per-vertex pressure data with all frames. Larger files (~100MB+)</li>"
            "</ul>"
            "<br><i>Note: Pressure metadata and statistics are always included in both options.</i>"
        )

        choice, ok = QInputDialog.getItem(self, "Frame Export Options", dialog_text, frame_options, 1, False)  # Default to Per-slice

        if not ok:
            return

        # Determine max frames and compression mode based on choice
        pressure_export_mode = "per_vertex"
        if "No vertex pressure data" in choice:
            max_frames = 0
            compression_mode = "minimal"
            pressure_export_mode = "none"
        elif "Per-slice" in choice:
            max_frames = -1
            compression_mode = "full"
            pressure_export_mode = "per_slice"
        else:  # All vertex
            max_frames = -1
            compression_mode = "full"
            pressure_export_mode = "per_vertex"

        # Validation selection: if prompt disabled in config, skip and default to no validation export
        export_validation_attributes = False
        validation_format = "json"
        if getattr(config, "enable_validation_export_prompt", True):
            validation_options = ["No validation attributes", "Export validation attributes (JSON format)"]
            validation_dialog_text = (
                "Do you want to export validation attributes for the validation framework?"
                "<ul>"
                "<li><b>No validation attributes:</b> Only export the 3D mesh file</li>"
                "<li><b>JSON format:</b> Export validation data in a single JSON file</li>"
                "</ul>"
                "<br><i>Validation attributes enable automated validation of reconstruction accuracy.</i>"
            )
            validation_choice, validation_ok = QInputDialog.getItem(self, "Validation Export Options", validation_dialog_text, validation_options, 0, False)
            if not validation_ok:
                return
            export_validation_attributes = validation_choice == validation_options[1]

        destination_directory = QFileDialog.getExistingDirectory(self, "Select Directory for VTKHDF Export")

        if not destination_directory:
            print("User cancelled the directory selection")
            return  # Exit the method if no directory was selected

        # Use os.path.normpath to normalize the path for the current operating system
        destination_directory = os.path.normpath(destination_directory)

        try:
            from logic.dataoutput.vtkhdf_exporter import VTKHDFExporter
            from logic.database.database import get_db
            from PyQt6.QtWidgets import QInputDialog

            # Initialize enhanced exporter with database session
            db_session = get_db()
            exporter = VTKHDFExporter(db_session=db_session, max_pressure_frames=max_frames, pressure_export_mode=pressure_export_mode)

            all_created_files = []
            # Initialize validation files tracking
            if export_validation_attributes:
                self._validation_files = []

            # loop through all visits.items (these are figures which are displayed in different threads)
            for i, (name, visit_data) in enumerate(self.visits.items()):
                visit_name = name.split(".")[0] if "." in name else name

                # Export entire visit using the optimized pipeline
                try:
                    # Extract patient_id and visit_id from name
                    # For visit name like "[Visit_ID_1]_Patient_1_InitialDiagnostic_1901"
                    # Extract patient identifier (try multiple patterns)
                    patient_id = None

                    # Try pattern 1: Extract "Patient_1" from "]_Patient_1_"
                    patient_id_match = re.search(r"\]_([^_]+_\d+)_", visit_name)
                    if patient_id_match:
                        patient_id = patient_id_match.group(1)  # Gets "Patient_1"
                    else:
                        # Try pattern 2: Extract "Patient" from "]_Patient_"
                        patient_id_match = re.search(r"\]_([^_]+)_", visit_name)
                        if patient_id_match:
                            patient_id = patient_id_match.group(1)  # Gets "Patient"
                        else:
                            # Try pattern 3: Extract just the number from "Patient_1"
                            patient_id_match = re.search(r"Patient_(\d+)", visit_name)
                            if patient_id_match:
                                patient_id = patient_id_match.group(1)  # Gets "1"

                    visit_id_match = re.search(r"Visit_ID_(\d+)", visit_name)
                    visit_id = int(visit_id_match.group(1)) if visit_id_match else None

                    export_result = exporter.export_visit_reconstructions(
                        visit_data,
                        visit_name,
                        destination_directory,
                        patient_id=patient_id,
                        visit_id=visit_id,
                        export_validation_attributes=export_validation_attributes,
                        validation_attributes_format=validation_format,
                    )

                    mesh_files = export_result.get("mesh_files", [])
                    validation_files = export_result.get("validation_files", [])
                    all_created_files.extend(mesh_files)

                    # Track validation files separately for the final message
                    if export_validation_attributes:
                        if not hasattr(self, '_validation_files'):
                            self._validation_files = []
                        self._validation_files.extend(validation_files)

                    total_files = len(mesh_files) + len(validation_files)
                    print(f"Successfully exported visit: {visit_name} ({total_files} files)")

                except Exception as e:
                    print(f"Error exporting visit {visit_name}: {str(e)}")
                    continue

            # Inform the user that the export is complete
            if all_created_files:
                # Conditional pressure features based on what was exported
                if pressure_export_mode == "none" or max_frames == 0:
                    pressure_features = "• Pressure metadata and statistics\n"
                elif pressure_export_mode == "per_slice":
                    pressure_features = "• Per-slice HRM pressure (compact)\n• Pressure metadata and statistics\n"
                else:
                    pressure_features = "• Per-vertex HRM pressure data\n• Pressure metadata and statistics\n"

                # Add validation files info to success message
                validation_info = ""
                if export_validation_attributes and hasattr(self, '_validation_files'):
                    validation_info = f"\n• {len(self._validation_files)} validation attribute files ({validation_format.upper()} format)"

                QMessageBox.information(
                    self,
                    "VTKHDF Export Successful",
                    f"Successfully exported {len(all_created_files)} VTKHDF files to:\n{destination_directory}\n\n"
                    f"VTKHDF files features included:\n"
                    f"{pressure_features}"
                    f"• Per-vertex wall thickness\n"
                    f"• Per-vertex anatomical region classification (LES/tubular)\n"
                    f"• Comprehensive patient and visit metadata\n"
                    f"• Geometric features (normals, curvature)\n"
                    f"• Complete acquisition parameters\n"
                    f"• HDF5 organization for efficient data access"
                    f"{validation_info}",
                )
            else:
                QMessageBox.warning(self, "Export Failed", "No VTKHDF files were exported. Please check the console for error details.")

        # Inform user that the export failed
        except Exception as e:
            print(f"An error occurred during VTKHDF export: {str(e)}")
            QMessageBox.critical(self, "VTKHDF Export Error", f"An error occurred during the VTKHDF export process: {str(e)}")

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
                    [
                        "Id-Visit",
                        "Id-Picture",
                        "Volume Tubular",
                        "Volume Sphincter",
                        "Esophagus Length (cm)",
                        "Mean over all (Volume * max(tubular pressure from frame))",
                        "Mean over all (Volume * min(tubular pressure from frame))",
                        "Mean over all (Volume * mean(tubular pressure from frame))",
                        "Mean over all (Volume / max(sphincter pressure from frame))",
                        "Mean over all (Volume / min(sphincter pressure from frame))",
                        "Mean over all (Volume / mean(sphincter pressure from frame))",
                        "Tubular Pressure Max",
                        "Tubular Pressure Min",
                        "Tubular Pressure Mean",
                        "Sphincter Pressure Max",
                        "Sphincter Pressure Min",
                        "Sphincter Pressure Mean",
                        "Esophageal Pressurization Index",
                    ]
                )

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
                        tubular_metric_mean = metrics["metric_tubular_overall"]["mean"]
                        tubular_metric_min = metrics["metric_tubular_overall"]["min"]
                        tubular_metric_max = metrics["metric_tubular_overall"]["max"]
                        sphincter_metric_mean = metrics["metric_sphincter_overall"]["mean"]
                        sphincter_metric_min = metrics["metric_sphincter_overall"]["min"]
                        sphincter_metric_max = metrics["metric_sphincter_overall"]["max"]
                        tubular_pressure_mean = metrics["pressure_tubular_overall"]["mean"]
                        tubular_pressure_min = metrics["pressure_tubular_overall"]["min"]
                        tubular_pressure_max = metrics["pressure_tubular_overall"]["max"]
                        sphincter_pressure_mean = metrics["pressure_sphincter_overall"]["mean"]
                        sphincter_pressure_min = metrics["pressure_sphincter_overall"]["min"]
                        sphincter_pressure_max = metrics["pressure_sphincter_overall"]["max"]
                        volume_tubular = metrics["volume_sum_tubular"]
                        volume_sphincter = metrics["volume_sum_sphincter"]
                        esophagus_length = visit_data.visualization_data_list[j].figure_creator.get_esophagus_full_length_cm()
                        esophageal_pressurization_index = metrics["esophageal_pressurization_index"]

                        # Write metrics data to CSV file
                        writer.writerow(
                            [
                                visit_name.encode("utf-8"),
                                id_minute,
                                round(volume_tubular, 4),
                                round(volume_sphincter, 4),
                                round(esophagus_length, 4),
                                round(tubular_metric_max, 4),
                                round(tubular_metric_min, 4),
                                round(tubular_metric_mean, 4),
                                round(sphincter_metric_max, 4),
                                round(sphincter_metric_min, 4),
                                round(sphincter_metric_mean, 4),
                                round(tubular_pressure_max, 4),
                                round(tubular_pressure_min, 4),
                                round(tubular_pressure_mean, 4),
                                round(sphincter_pressure_max, 4),
                                round(sphincter_pressure_min, 4),
                                round(sphincter_pressure_mean, 4),
                                round(esophageal_pressurization_index, 4),
                            ]
                        )

            # Check if the file was actually created
            if os.path.exists(destination_file_path):
                export_successful = True
            else:
                print(f"Failed to create file: {destination_file_path}")

            if export_successful:
                # Inform the user that the export is complete
                QMessageBox.information(self, "Export Successful", f"The files have been successfully exported to {destination_file_path}.")
            else:
                QMessageBox.warning(self, "Export Failed", "No files were exported. There might be an issue with the data or permissions.")
        except Exception as e:
            # Inform user that the export failed
            print(f"An error occurred during export: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"An error occurred during the export process: {str(e)}")

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
                    [
                        "Id-Visit",
                        "Id-Picture",
                        "Frame",
                        "Length Tubular",
                        "Length Sphincter",
                        "Volume Tubular",
                        "Volume Sphincter",
                        "Max tubular pressure in frame",
                        "Min tubular pressure in frame",
                        "Mean tubular pressure in frame",
                        "Volume * max(tubular pressure from frame)",
                        "Volume * min(tubular pressure from frame)",
                        "Volume * mean(tubular pressure from frame)",
                        "Max sphincter pressure in frame",
                        "Min sphincter pressure in frame",
                        "Mean sphincter pressure in frame",
                        "Volume / max(sphincter pressure from frame)",
                        "Volume / min(sphincter pressure from frame)",
                        "Volume / mean(sphincter pressure from frame)",
                    ]
                )

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
                        for frame in range(len(metrics["metric_tubular"]["max"])):
                            max_pressure_tubular_per_frame = metrics["pressure_tubular_per_frame"]["max"][frame]
                            min_pressure_tubular_per_frame = metrics["pressure_tubular_per_frame"]["min"][frame]
                            mean_pressure_tubular_per_frame = metrics["pressure_tubular_per_frame"]["mean"][frame]
                            max_pressure_sphincter_per_frame = metrics["pressure_sphincter_per_frame"]["max"][frame]
                            min_pressure_sphincter_per_frame = metrics["pressure_sphincter_per_frame"]["min"][frame]
                            mean_pressure_sphincter_per_frame = metrics["pressure_sphincter_per_frame"]["mean"][frame]
                            metric_max_tubular = metrics["metric_tubular"]["max"][frame]
                            metric_min_tubular = metrics["metric_tubular"]["min"][frame]
                            metric_mean_tubular = metrics["metric_tubular"]["mean"][frame]
                            metric_max_sphincter = metrics["metric_sphincter"]["max"][frame]
                            metric_min_sphincter = metrics["metric_sphincter"]["min"][frame]
                            metric_mean_sphincter = metrics["metric_sphincter"]["mean"][frame]
                            volume_tubular = metrics["volume_sum_tubular"]
                            volume_sphincter = metrics["volume_sum_sphincter"]
                            len_tubular = metrics["len_tubular"]
                            len_sphincter = metrics["len_sphincter"]

                            # Write metrics data to CSV file
                            writer.writerow(
                                [
                                    visit_name.encode("utf-8"),
                                    id_minute,
                                    frame,
                                    round(len_tubular, 4),
                                    round(len_sphincter, 4),
                                    round(volume_tubular, 4),
                                    round(volume_sphincter, 4),
                                    round(max_pressure_tubular_per_frame, 4),
                                    round(min_pressure_tubular_per_frame, 4),
                                    round(mean_pressure_tubular_per_frame, 4),
                                    round(metric_max_tubular, 4),
                                    round(metric_min_tubular, 4),
                                    round(metric_mean_tubular, 4),
                                    round(max_pressure_sphincter_per_frame, 4),
                                    round(min_pressure_sphincter_per_frame, 4),
                                    round(mean_pressure_sphincter_per_frame, 4),
                                    round(metric_max_sphincter, 4),
                                    round(metric_min_sphincter, 4),
                                    round(metric_mean_sphincter, 4),
                                ]
                            )
            # Check if the file was actually created
            if os.path.exists(destination_file_path_metriks):
                export_successful = True
            else:
                print(f"Failed to create file: {destination_file_path_metriks}")

            if export_successful:
                # Inform the user that the export is complete
                QMessageBox.information(self, "Export Successful", f"The files have been successfully exported to {destination_file_path_metriks}.")
            else:
                QMessageBox.warning(self, "Export Failed", "No files were exported. There might be an issue with the data or permissions.")

        except Exception as e:
            # Inform user that the export failed
            print(f"An error occurred during export: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"An error occurred during the export process: {str(e)}")

    def __extend_patient_data(self):
        """
        Callback for extending patient data
        """
        # Open the Data Window to enable selection of new data
        # Pass flag to indicate this should return to visualization window
        data_window = gui.data_window.DataWindow(self.master_window, self.patient_data, return_to_visualization=True)
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

    # Required abstract methods from BaseWorkflowWindow
    def _supports_undo(self) -> bool:
        """The visualization window doesn't support undo operations"""
        return False

    def _has_unsaved_changes(self) -> bool:
        """The visualization window doesn't have unsaved changes to track"""
        return False

    def _get_current_state(self):
        """No state to save in visualization window"""
        return None

    def _restore_state(self, state):
        """No state to restore in visualization window"""
        pass

    def __adjust_current_segmentation(self):
        """
        Load the saved reconstruction of the currently displayed visit and
        restart the normal reconstruction workflow from the beginning, with both
        HRM and TBE steps preloaded from the saved reconstruction.
        """
        try:
            from logic.database.database import get_db
            from logic.workflow.segmentation_adjustment import start_xray_adjustment, start_hrm_adjustment

            db_session = get_db()

            if not self.visits:
                QMessageBox.warning(self, "No data", "No visualization loaded to adjust.")
                return

            # Use the first visit in the current visualization context
            first_visit_name = next(iter(self.visits.keys()))
            match = re.search(r"Visit_ID_(\d+)", first_visit_name)
            if not match:
                QMessageBox.warning(self, "Visit not found", "Could not parse visit ID from the current visualization.")
                return

            visit_id = int(match.group(1))
            # Provide in-memory override so re-adjustment uses the latest unsaved edits
            visit_data_override = self.visits.get(first_visit_name, None)

            # Start at HRM (DCI) step so user can adjust pressures/LES/UES,
            # then proceed to X-ray segmentation with preloaded polygons
            if not start_hrm_adjustment(self.master_window, db_session, visit_id, visit_data_override=visit_data_override):
                QMessageBox.warning(self, "Adjustment unavailable", "No reconstruction found or failed to load HRM/segmentation for this visit.")
                return
            # Note: after finishing DCI step, workflow continues into X-ray windows; if needed call below directly.
            # start_xray_adjustment(self.master_window, db_session, visit_id)

            # Do NOT close this window here. We keep it alive so that the Back button
            # can return to the existing visualization without a black screen.
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start segmentation adjustment: {e}")

    def _before_going_back(self):
        """Clean up visualizations before going back"""
        # Stop all figure creation threads
        if hasattr(self, "thread") and self.thread:
            for thread in self.thread:
                if thread and thread.isRunning():
                    thread.terminate()
                    thread.wait()  # Wait for thread to finish

        # Close progress dialog if it exists
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # Stop all dash servers and close web views (aggressively free QWebEngine resources like cache/profile)
        for dash_server in self.dash_servers:
            try:
                dash_server.stop()
            except Exception:
                pass

        for web_view in self.web_views:
            try:
                # Navigate to about:blank to break any active connections first
                web_view.setHtml("")
            except Exception:
                pass
            try:
                page = web_view.page()
                if page is not None:
                    try:
                        profile = page.profile()
                        if profile is not None:
                            try:
                                profile.clearHttpCache()
                                profile.clearAllVisitedLinks()
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                web_view.close()
            except Exception:
                pass
            try:
                web_view.deleteLater()
            except Exception:
                pass

        # Clear the lists
        self.dash_servers.clear()
        self.web_views.clear()

        # Align behavior with the Reset button: clear reconstructed visits so the
        # next visualization starts from a clean PatientData state. This avoids
        # stale references that can affect the embedded browser on Windows.
        try:
            if hasattr(self, "patient_data") and hasattr(self.patient_data, "visit_data_dict"):
                self.patient_data.visit_data_dict = {}
        except Exception:
            pass

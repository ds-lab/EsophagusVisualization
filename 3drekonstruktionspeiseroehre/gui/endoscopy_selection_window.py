import logic.image_polygon_detection as image_polygon_detection
import numpy as np
import os
import cv2
from gui.base_workflow_window import BaseWorkflowWindow
from gui.info_window import InfoWindow
from gui.master_window import MasterWindow
from gui.visualization_window import VisualizationWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.widgets import PolygonSelector
from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMessageBox
from shapely.geometry import Polygon
from PIL import Image


class EndoscopySelectionWindow(BaseWorkflowWindow):
    """Window where the user selects the polyon shape on the endoscopy images"""

    def __init__(
        self, master_window: MasterWindow, patient_data: PatientData, visit: VisitData
    ):
        """
        Initialize EndoscopySelectionWindow.

        Args:
            master_window (MasterWindow): The MasterWindow in which the next window will be displayed.
            visualization_data (VisualizationData): An instance of VisualizationData that the endoscopy images belong to.
            patient_data (PatientData): An instance of the current PatientData that the VisualizationDate belongs to.
        """
        # Store parameters
        self.visit = visit

        # Check if we're returning from a visualization (endoscopy polygons already exist)
        existing_polygons = None
        if (
            self.visit.visualization_data_list
            and self.visit.visualization_data_list[0].endoscopy_polygons is not None
        ):
            existing_polygons = self.visit.visualization_data_list[0].endoscopy_polygons

        # Clear any existing endoscopy polygons from the visit to ensure clean state
        # This prevents data corruption when returning from visualization window
        for vis in self.visit.visualization_data_list:
            vis.endoscopy_polygons = None

        # Call parent constructor
        super().__init__(master_window, patient_data, visit, None)

        self.ui = uic.loadUi("./ui-files/endoscopy_selection_window_design.ui", self)

        # Note: We track unsaved changes by comparing current_polygon with polygon_list

        self.current_image_index = 0
        # list of points (not cm)
        self.current_polygon = []
        # Temporary storage for polygon selections (saved automatically as user draws)
        self.temp_polygon_storage = {}
        self.figure_canvas = FigureCanvasQTAgg(Figure())
        self.ui.gridLayout.addWidget(self.figure_canvas)
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        # Setup navigation buttons after UI is loaded
        self._setup_navigation_buttons()

        # Ensure apply button is enabled when window is opened/reopened
        if hasattr(self.ui, "apply_button"):
            self.ui.apply_button.setEnabled(True)
        self.plot_ax = self.figure_canvas.figure.subplots()
        self.figure_canvas.figure.subplots_adjust(
            bottom=0.05, top=0.95, left=0.05, right=0.95
        )

        # Get endoscopy images (same for all visualisation data since only xray differ)
        self.endoscopy_images = [
            np.array(Image.open(file))
            for file in visit.visualization_data_list[0].endoscopy_files
        ]

        # Initialize polygon_list as a list with None values for each image
        # (must be done after endoscopy_images is defined)
        self.polygon_list = [None] * len(self.endoscopy_images)

        # If we had existing polygons (returning from visualization), restore them
        if existing_polygons is not None and len(existing_polygons) == len(
            self.endoscopy_images
        ):
            self.polygon_list = [poly.copy() for poly in existing_polygons]
            # Also populate temporary storage for smooth editing
            for i, poly in enumerate(existing_polygons):
                if poly is not None:
                    self.temp_polygon_storage[i] = poly.tolist()

            # Determine starting image index based on navigation history
            # If we came directly from visualization window (back button), start on last image
            # If we came from earlier in the workflow (TBE -> forward), start on first image
            if (
                hasattr(self.master_window, "navigation_stack")
                and len(self.master_window.navigation_stack) > 0
            ):
                # Check if the previous window was the visualization window
                previous_window_type = type(
                    self.master_window.navigation_stack[-1]
                ).__name__
                if previous_window_type == "VisualizationWindow":
                    # Coming directly from visualization - start on last image for final adjustments
                    self.current_image_index = len(self.endoscopy_images) - 1
                else:
                    # Coming from earlier workflow steps - start on first image for review
                    self.current_image_index = 0
            else:
                # Default to first image if we can't determine the navigation path
                self.current_image_index = 0

        self.__load_image(self.endoscopy_images[self.current_image_index])
        self.__update_button_text()

    def __menu_button_clicked(self):
        """
        Callback for the menu button.

        Shows an InfoWindow with relevant information.
        """
        info_window = InfoWindow()
        info_window.show_endoscopy_selection_info()
        info_window.show()

    def __update_button_text(self):
        """
        Updates the text of the apply button based on the current image index.
        """
        if not self.__is_last_image():
            self.ui.apply_button.setText("Apply selection and load next image")
        else:
            self.ui.apply_button.setText("Apply selection and generate visualization")

        # Update window title to show current image progress
        total_images = len(self.endoscopy_images)
        current_image_num = self.current_image_index + 1
        self.setWindowTitle(
            f"Selection of the cross-section of the esophagus - Image {current_image_num}/{total_images}"
        )

    def __is_last_image(self) -> bool:
        """
        Checks if the last image is loaded.

        Returns:
            bool: True if the last image is loaded, False otherwise.
        """
        return self.current_image_index == len(self.endoscopy_images) - 1

    def __load_image(self, image):
        """
        Loads the given image and initializes the polygon selector.

        Args:
            image: The image to load.
        """
        # Clear the plot completely to avoid overlapping selectors
        self.plot_ax.clear()
        self.plot_ax.imshow(image)
        self.plot_ax.axis("off")

        # Disconnect and remove any existing selector to prevent overlapping polygons
        if hasattr(self, "selector") and self.selector is not None:
            try:
                self.selector.disconnect_events()
                self.selector.clear()
            except:
                pass  # Ignore errors if selector is already disconnected

        # Create a new polygon selector
        self.selector = PolygonSelector(
            self.plot_ax, self.__onselect, useblit=True, props=dict(color="red")
        )

        # Get auto-detected polygon for fallback
        polygon = image_polygon_detection.calculate_endoscopy_polygon(image)

        # Restore polygon state for this image
        restored_polygon = None

        # First priority: Check if we have a saved polygon in the final polygon_list
        if (
            self.current_image_index < len(self.polygon_list)
            and self.polygon_list[self.current_image_index] is not None
        ):
            restored_polygon = self.polygon_list[self.current_image_index].tolist()
        # Second priority: Check temporary storage
        elif self.current_image_index in self.temp_polygon_storage:
            restored_polygon = self.temp_polygon_storage[self.current_image_index]
        # Third priority: Use auto-detected polygon
        elif len(polygon) > 0:
            restored_polygon = polygon

        # Apply the restored polygon if we have one
        if restored_polygon is not None and len(restored_polygon) > 2:
            # Store the polygon for our internal tracking
            self.current_polygon = restored_polygon.copy()

            # The key insight: instead of trying to manually set internal coordinates,
            # we'll use the PolygonSelector's verts property and trigger a proper update
            try:
                # Set the vertices - this is the main interface for restoring polygons
                self.selector.verts = restored_polygon.copy()

                # Make sure the selector is visible
                self.selector.set_visible(True)

                # The critical part: we need to trigger the selector's internal update
                # without causing coordinate mismatches
                if hasattr(self.selector, "_update_line"):
                    # This method properly updates the visual representation
                    self.selector._update_line()
                elif hasattr(self.selector, "update"):
                    self.selector.update()

                # Mark as completed to prevent accidental editing
                if hasattr(self.selector, "_selection_completed"):
                    self.selector._selection_completed = True

            except Exception as e:
                print(f"Warning: Polygon restoration failed: {e}")
                # Fallback: just store the polygon internally and let user re-select if needed
                pass

            # Update temporary storage
            self.temp_polygon_storage[self.current_image_index] = (
                restored_polygon.copy()
            )
        else:
            # No polygon to restore, start fresh
            self.current_polygon = []

        # Redraw the canvas to ensure proper display
        self.figure_canvas.draw()

        # Use a delayed refresh to ensure the polygon is properly displayed
        # This is important because matplotlib sometimes needs a moment to process the changes
        if restored_polygon is not None and len(restored_polygon) > 2:
            from PyQt6.QtCore import QTimer

            def delayed_refresh():
                try:
                    # Force a redraw and ensure the polygon is visible
                    if hasattr(self.selector, "set_visible"):
                        self.selector.set_visible(True)
                    self.figure_canvas.draw()
                except:
                    pass  # Ignore errors in delayed refresh

            # Use a shorter delay for better responsiveness
            QTimer.singleShot(25, delayed_refresh)

    def __onselect(self, polygon):
        """
        Called when a polygon selection is finished.

        Args:
            polygon: The new polygon selection.
        """
        self.current_polygon = polygon
        # Automatically save the current polygon selection for this image
        self.temp_polygon_storage[self.current_image_index] = polygon.copy()

    def __reset_button_clicked(self):
        """
        Callback for the reset button.

        Resets the polygon selection.
        """
        self.__reset_selector()

    def __apply_button_clicked(self):
        """
        Callback for the apply button.

        Applies the current polygon selection and either loads the next image or generates visualization.
        """
        if len(self.current_polygon) > 2:
            shapely_poly = Polygon(self.current_polygon)
            if shapely_poly.is_valid:
                # Save current polygon to the final polygon list at the correct index
                self.polygon_list[self.current_image_index] = np.array(
                    self.current_polygon, dtype=int
                )
                # Also ensure it's saved in temporary storage
                self.temp_polygon_storage[self.current_image_index] = (
                    self.current_polygon.copy()
                )

                if self.ui.checkBox.isChecked():
                    self.__save_current_polygon()
                if self.__is_last_image():
                    self.ui.apply_button.setDisabled(True)

                    # Validate that all polygons have been defined
                    missing_polygons = [
                        i for i, poly in enumerate(self.polygon_list) if poly is None
                    ]

                    if missing_polygons:
                        QMessageBox.critical(
                            self,
                            "Data Validation Error",
                            f"Missing polygon selections for image(s): {[i+1 for i in missing_polygons]}. "
                            "Please ensure all endoscopy images have been segmented before proceeding.",
                        )
                        return

                    # Update the polygon for all visualization objects in visit
                    for vis in self.visit.visualization_data_list:
                        vis.endoscopy_polygons = [
                            poly.copy() for poly in self.polygon_list
                        ]

                    self.patient_data.add_visit(self.visit.name, self.visit)
                    visualization_window = VisualizationWindow(
                        self.master_window, self.patient_data
                    )
                    self.master_window.switch_to(visualization_window)
                    self.close()

                else:
                    self.current_image_index += 1
                    self.__load_image(self.endoscopy_images[self.current_image_index])
                    self.__update_button_text()
            else:
                QMessageBox.critical(
                    self, "Error", "The selection must not have any intersections."
                )
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Please draw the cross-section of the esophagus as a polygon.",
            )

    def __save_current_polygon(self):
        """
        Saves the current polygon as a mask image in the specified folder.
        """
        safe_visit_name = (
            self.visit.name.replace(":", "_").replace("[", "_").replace("]", "_")
        )
        base_path = rf"C:\DataAchalasia\{safe_visit_name}"

        if not os.path.exists(base_path):
            os.makedirs(base_path)

        img_filename = f"{self.current_image_index}_endoscopy.jpg"
        img_path = os.path.join(base_path, img_filename)

        image = self.endoscopy_images[self.current_image_index].astype(np.uint8)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cv2.imwrite(img_path, rgb_image)

        # Save the mask as PNG
        mask_filename = f"{self.current_image_index}_endoscopy_mask.jpg"
        mask_path = os.path.join(base_path, mask_filename)

        mask_image = np.zeros(
            self.endoscopy_images[self.current_image_index].shape[:2], dtype=np.uint8
        )
        cv2.fillPoly(mask_image, [np.array(self.current_polygon, dtype=int)], 255)
        cv2.imwrite(mask_path, mask_image)

    def __reset_selector(self):
        """
        Starts a new polygon selection by resetting the selector.
        """
        if hasattr(self, "selector") and self.selector is not None:
            try:
                # Use the proper interface to clear the polygon selector
                # This is much safer than manually manipulating internal attributes
                self.selector.verts = []

                # Make sure it's visible for new selections
                self.selector.set_visible(True)

                # Clear the visual representation
                self.selector.clear()

                # Reset selection state if available
                if hasattr(self.selector, "_selection_completed"):
                    self.selector._selection_completed = False

                # Force a redraw to clear any existing polygons
                self.figure_canvas.draw()

            except Exception as e:
                print(f"Warning: Error during selector reset: {e}")
                # Fallback: try basic reset
                try:
                    self.selector.clear()
                    self.figure_canvas.draw()
                except:
                    pass  # Ignore errors in fallback

        # Clear our internal state
        self.current_polygon.clear()

        # Clear the temporary storage for this image
        if self.current_image_index in self.temp_polygon_storage:
            del self.temp_polygon_storage[self.current_image_index]

    # Abstract methods required by BaseWorkflowWindow
    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        # We have unsaved changes if:
        # 1. There's a current polygon selection AND
        # 2. We haven't applied it yet (polygon at current index is None)
        return (
            len(self.current_polygon) > 2
            and self.polygon_list[self.current_image_index] is None
        )

    def _before_going_back(self):
        """Cleanup before going back"""
        # Any cleanup operations can go here
        pass

    def _handle_back_button(self):
        """
        Override back button behavior to handle multiple EGD images
        """
        # If we're not on the first image, go back to the previous image
        if self.current_image_index > 0:
            # Ask for confirmation if there are unsaved changes
            if self._has_unsaved_changes():
                from PyQt6.QtWidgets import QMessageBox

                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Going back will lose the current polygon selection. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Save current state before moving (if there's a valid polygon)
            if len(self.current_polygon) > 2:
                # Save to both storage locations for consistency
                self.temp_polygon_storage[self.current_image_index] = (
                    self.current_polygon.copy()
                )
                if self.polygon_list[self.current_image_index] is None:
                    self.polygon_list[self.current_image_index] = np.array(
                        self.current_polygon, dtype=int
                    )

            # Go back to previous image
            self.current_image_index -= 1

            # Load the previous image (this will automatically restore the polygon state)
            self.__load_image(self.endoscopy_images[self.current_image_index])

            self.__update_button_text()

            # Re-enable apply button
            self.ui.apply_button.setEnabled(True)
        else:
            # If we're on the first image, use the default back behavior
            super()._handle_back_button()

    def _on_window_activated(self):
        """
        Called when window is shown/activated - re-enable apply button
        """
        super()._on_window_activated()
        # Ensure apply button is always enabled when returning to this window
        if hasattr(self.ui, "apply_button"):
            self.ui.apply_button.setEnabled(True)

        # Force refresh of the current image to ensure polygon is displayed
        # This is especially important when returning from visualization window
        if hasattr(self, "endoscopy_images") and self.endoscopy_images:
            # Reload the current image to ensure polygon is properly displayed
            current_image = self.endoscopy_images[self.current_image_index]

            # Use QTimer to ensure this happens after the window is fully activated
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(50, lambda: self.__load_image(current_image))

    def closeEvent(self, event):
        """
        Override closeEvent to ensure proper cleanup of polygon selectors
        """
        # Disconnect and clean up the polygon selector
        if hasattr(self, "selector") and self.selector is not None:
            try:
                self.selector.disconnect_events()
                self.selector.clear()
            except:
                pass  # Ignore errors during cleanup

        # Call parent closeEvent
        super().closeEvent(event)

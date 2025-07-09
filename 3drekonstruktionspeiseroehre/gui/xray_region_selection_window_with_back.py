import os
import shutil
import numpy as np
import cv2
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtGui import QAction
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.widgets import PolygonSelector
from matplotlib.patches import Polygon
from PIL import Image
from shapely.geometry import Polygon as ShapelyPolygon
import copy

# Import the new base class
from gui.base_workflow_window import BaseWorkflowWindow
from gui.master_window import MasterWindow
from gui.position_selection_window import PositionSelectionWindow
from gui.info_window import InfoWindow
from logic.patient_data import PatientData
from logic.visit_data import VisitData
from logic import image_polygon_detection

# ML imports (if available)
try:
    import torch
    from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class XrayRegionSelectionWindowWithBack(BaseWorkflowWindow):
    """
    Enhanced X-ray Region Selection Window with back button and undo functionality
    """

    def __init__(
        self,
        master_window: MasterWindow,
        patient_data: PatientData,
        visit: VisitData,
        n,
    ):
        # Initialize visualization data
        self.visit = visit
        self.visualization_data = visit.visualization_data_list[n]
        self.n = n

        # Call parent constructor
        super().__init__(master_window, patient_data, visit, self.visualization_data)

        # Initialize UI
        self.ui = uic.loadUi("./ui-files/xray_region_selection_window_design.ui", self)
        self.master_window.maximize()

        # Setup the rest of the window
        self._setup_ui()
        self._setup_navigation_buttons()  # This will add back/undo buttons

        # Track changes for unsaved changes detection
        self.initial_state = None
        self.has_changes = False

    def _setup_ui(self):
        """Setup the UI components"""
        # Create a figure canvas for displaying the image
        self.figure_canvas = FigureCanvasQTAgg(Figure())
        self.ui.gridLayout.addWidget(self.figure_canvas)

        # Connect button click events to methods
        self.ui.reset_button.clicked.connect(self.__reset_button_clicked)
        self.ui.apply_button.clicked.connect(self.__apply_button_clicked)
        self.ui.nextSelection_button.clicked.connect(self.__next_button_clicked)
        self.ui.deletePoint_button.clicked.connect(self.__delete_button_clicked)

        # Create a menu button for displaying the Info-Window
        menu_button = QAction("Info", self)
        menu_button.triggered.connect(self.__menu_button_clicked)
        self.ui.menubar.addAction(menu_button)

        # Create a plot axis for displaying the image
        self.plot_ax = self.figure_canvas.figure.subplots()
        self.figure_canvas.figure.subplots_adjust(
            bottom=0.05, top=0.95, left=0.05, right=0.95
        )

        # Initialize polygon selection
        self.polygon_colors = ["red", "blue", "green"]
        self.current_polygon_index = 0
        self.polygon_selectors = []
        self.polygon_points = {}
        self.checkboxes = [self.ui.oesophagus, self.ui.spine, self.ui.barium]
        self.checkbox_names = {
            self.ui.oesophagus: "oesophagus",
            self.ui.spine: "spine",
            self.ui.barium: "barium",
        }

        # Load and display the X-ray image
        image = Image.open(self.visualization_data.xray_file)
        self.xray_image = np.array(image)
        self.plot_ax.imshow(self.xray_image)
        self.plot_ax.axis("off")

        # Initialize polygon based on ML model usage
        if self.visualization_data.use_model and ML_AVAILABLE:
            self._initialize_with_ml()
        else:
            self._initialize_without_ml()

        # Save initial state
        self._save_initial_state()

    def _initialize_with_ml(self):
        """Initialize polygon using ML model"""
        try:
            mask = self._predict_mask_with_nnunet_v2()
            self.mask = (mask > 0.5).astype(np.uint8) * 255
            self.polygonOes = self._mask_to_largest_polygon()
            self._init_first_polygon_ml()
        except Exception as e:
            print(f"ML initialization failed: {e}, falling back to traditional method")
            self._initialize_without_ml()

    def _initialize_without_ml(self):
        """Initialize polygon using traditional image processing"""
        self.polygonOes = image_polygon_detection.calculate_xray_polygon(
            self.xray_image
        )
        self._init_first_polygon()

    def _init_first_polygon(self):
        """Initialize the first polygon selector"""
        color = self.polygon_colors[0]
        self.selector = PolygonSelector(
            self.plot_ax, self._onselect, useblit=True, props=dict(color=color)
        )
        self.polygon_selectors.append(self.selector)

        if len(self.polygonOes) > 2:
            self.selector.verts = self.polygonOes
            self.polygon_points["oesophagus"] = self.selector.verts
        else:
            self.selector.verts = [(0, 0)]
            self._reset_selector()
        self.figure_canvas.draw_idle()

    def _init_first_polygon_ml(self):
        """Initialize polygon with ML results"""
        color = self.polygon_colors[0]
        self.selector = PolygonSelector(
            self.plot_ax, self._onselect, useblit=True, props=dict(color=color)
        )
        self.polygon_selectors.append(self.selector)

        if isinstance(self.polygonOes, ShapelyPolygon):
            points = np.array(self.polygonOes.exterior.coords)
        else:
            points = self.polygonOes

        if len(points) > 2:
            self.selector.verts = points[::10]
            self.polygon_points["oesophagus"] = self.selector.verts
        else:
            self.selector.verts = [(0, 0)]
            self._reset_selector()

        self.figure_canvas.draw_idle()

    def _onselect(self, verts):
        """Handle polygon selection"""
        checkbox = self.checkboxes[self.current_polygon_index]
        polygon_name = self.checkbox_names[checkbox]
        self.polygon_points[polygon_name] = verts
        self.has_changes = True
        self._save_state_for_undo()  # Save state after each change

    # Override base class methods
    def _supports_undo(self) -> bool:
        """Enable undo functionality for segmentation"""
        return True

    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        return self.has_changes

    def _get_current_state(self):
        """Get current state for undo"""
        return {
            "polygon_points": copy.deepcopy(self.polygon_points),
            "current_polygon_index": self.current_polygon_index,
            "selector_verts": (
                copy.deepcopy(self.selector.verts)
                if hasattr(self, "selector")
                else None
            ),
        }

    def _restore_state(self, state):
        """Restore previous state"""
        self.polygon_points = state["polygon_points"]
        self.current_polygon_index = state["current_polygon_index"]

        if state["selector_verts"] and hasattr(self, "selector"):
            self.selector.verts = state["selector_verts"]

        # Redraw the canvas
        self.figure_canvas.draw_idle()
        self.has_changes = True

    def _save_initial_state(self):
        """Save the initial state"""
        self.initial_state = self._get_current_state()
        self.has_changes = False

    def _before_going_back(self):
        """Cleanup before going back"""
        # Any cleanup operations can go here
        pass

    # Button handlers
    def __reset_button_clicked(self):
        """Reset current polygon"""
        self._save_state_for_undo()
        self._reset_selector()
        self.has_changes = True

    def __apply_button_clicked(self):
        """Apply current segmentation and move to next step"""
        valid = all(self._validate_polygon(name) for name in self.polygon_points)

        if valid:
            self.ui.apply_button.setDisabled(True)

            # Save the esophagus polygon
            self.visualization_data.xray_polygon = np.array(
                self.polygon_points["oesophagus"], dtype=int
            )
            self.visualization_data.xray_image_height = self.xray_image.shape[0]
            self.visualization_data.xray_image_width = self.xray_image.shape[1]

            # Process and save masks
            self._process_and_save_masks()

            # Mark as saved
            self.has_changes = False

            # Move to next window
            position_selection_window = PositionSelectionWindow(
                self.master_window,
                None,
                self.patient_data,
                self.visit,
                self.n,
                self.polygon_points["oesophagus"],
            )
            self.master_window.switch_to(position_selection_window)
            self.close()
        else:
            QMessageBox.critical(self, "Error", "Please draw all polygons.")

    def __next_button_clicked(self):
        """Move to next polygon"""
        self._save_state_for_undo()
        # Implementation for next polygon selection
        pass

    def __delete_button_clicked(self):
        """Delete current polygon"""
        self._save_state_for_undo()
        # Implementation for polygon deletion
        self.has_changes = True

    def __menu_button_clicked(self):
        """Show info window"""
        info_window = InfoWindow()
        info_window.show_xray_region_selection_info()
        info_window.show()

    # Helper methods
    def _reset_selector(self):
        """Reset the polygon selector"""
        if hasattr(self, "selector"):
            self.selector.clear()
            self.figure_canvas.draw_idle()

    def _validate_polygon(self, name):
        """Validate a polygon"""
        points = self.polygon_points.get(name, [])
        if len(points) > 2:
            shapely_poly = ShapelyPolygon(points)
            return shapely_poly.is_valid
        return False

    def _process_and_save_masks(self):
        """Process and save polygon masks"""
        # Implementation for mask processing
        pass

    def _predict_mask_with_nnunet_v2(self):
        """Predict mask using nnUNet v2"""
        # Implementation for ML prediction
        # This is a simplified version - the full implementation would be more complex
        return np.zeros_like(self.xray_image)

    def _mask_to_largest_polygon(self):
        """Convert mask to largest polygon"""
        # Implementation for mask to polygon conversion
        return [(0, 0), (100, 0), (100, 100), (0, 100)]

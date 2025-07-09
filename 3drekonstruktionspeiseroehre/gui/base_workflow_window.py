from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QWidget,
    QVBoxLayout,
    QToolBar,
    QSizePolicy,
    QSpacerItem,
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction, QIcon
from abc import ABCMeta, abstractmethod
import copy


# Create a combined metaclass that resolves the conflict
class CombinedMeta(type(QMainWindow), ABCMeta):
    pass


class BaseWorkflowWindow(QMainWindow, metaclass=CombinedMeta):
    """
    Base class for workflow windows that provides back button and undo functionality
    """

    def __init__(
        self, master_window, patient_data=None, visit_data=None, visualization_data=None
    ):
        super().__init__()
        self.master_window = master_window
        self.patient_data = patient_data
        self.visit_data = visit_data
        self.visualization_data = visualization_data

        # Navigation functionality only

        # Don't setup navigation buttons in constructor - they need to be setup after UI is loaded

    def _setup_navigation_toolbar(self):
        """
        Create a navigation toolbar with back button and other actions
        """
        try:
            # Create navigation toolbar
            self.nav_toolbar = QToolBar("Navigation", self)
            self.nav_toolbar.setMovable(False)
            self.nav_toolbar.setFloatable(False)

            # Add toolbar to the top of the window
            self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.nav_toolbar)

            # Create back button
            self.back_action = QAction("← Back", self)
            self.back_action.triggered.connect(self._handle_back_button)
            self.back_action.setEnabled(True)
            self.back_action.setToolTip("Go back to previous window")
            self.nav_toolbar.addAction(self.back_action)

            # Add separator
            self.nav_toolbar.addSeparator()

            # Add spacer to push export button to the right
            spacer = QWidget()
            spacer.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            self.nav_toolbar.addWidget(spacer)

            # Add export glTF button (only for certain windows)
            if self._should_show_export_button():
                self.export_gltf_action = QAction("Export All glTF", self)
                self.export_gltf_action.triggered.connect(self._handle_export_gltf)
                self.export_gltf_action.setToolTip(
                    "Export all reconstructions as glTF files for ML"
                )
                self.nav_toolbar.addAction(self.export_gltf_action)

        except Exception as e:
            # Silently handle any errors
            pass

    def _should_show_export_button(self):
        """
        Override in subclasses to show export button where appropriate
        """
        return False

    def _handle_export_gltf(self):
        """
        Handle export glTF button click - override in subclasses
        """
        pass

    def _setup_navigation_buttons(self):
        """
        Legacy method - now calls the new toolbar setup
        """
        self._setup_navigation_toolbar()

    def _can_go_back(self) -> bool:
        """
        Check if we can go back to previous window
        """
        return self.master_window.can_go_back()

    def _handle_back_button(self):
        """
        Handle back button click - with confirmation if unsaved changes
        """
        if self._has_unsaved_changes():
            from PyQt6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Going back will lose these changes. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Perform any cleanup before going back
        self._before_going_back()

        # Go back using master window navigation
        if self.master_window.go_back():
            self.close()
        else:
            # If no navigation history, close current window and return to main data window
            from gui.data_window import DataWindow
            from logic.patient_data import PatientData

            # Create a new data window
            data_window = DataWindow(
                self.master_window, self.patient_data or PatientData()
            )
            self.master_window.switch_to(data_window, add_to_history=False)
            self.close()

    # Abstract methods to be implemented by subclasses
    @abstractmethod
    def _has_unsaved_changes(self) -> bool:
        """
        Check if there are unsaved changes in the current window
        """
        pass

    def _before_going_back(self):
        """
        Called before going back - override for cleanup operations
        """
        pass

    def showEvent(self, event):
        """
        Override showEvent to handle window activation
        """
        super().showEvent(event)
        self._on_window_activated()

    def _on_window_activated(self):
        """
        Called when window is shown/activated - override to reset UI state
        """
        # Re-enable apply button if it exists
        if hasattr(self, "ui") and hasattr(self.ui, "apply_button"):
            self.ui.apply_button.setEnabled(True)

import config
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QIcon
from utils.path_utils import resource_path


class MasterWindow:
    """Flexible Window that shows other windows inside"""

    def __init__(self):
        """
        init MasterWindow
        """
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.resize(config.window_start_size_width, config.window_start_size_height)
        self.stacked_widget.closeEvent = self.__stacked_widget_close_event
        self.stacked_widget.setWindowIcon(QIcon(resource_path("media/icon.ico")))

        # Center the window on screen
        self._center_window()

        # Navigation history for back functionality
        self.navigation_stack = []
        self.current_window = None

    def _center_window(self):
        """
        Center the window on the screen
        """
        # Center using frame geometry to account for window frame/titlebar
        screen = QApplication.primaryScreen()
        if not screen:
            return
        screen_center = screen.availableGeometry().center()
        frame_geom = self.stacked_widget.frameGeometry()
        frame_geom.moveCenter(screen_center)
        self.stacked_widget.move(frame_geom.topLeft())

    def switch_to(self, window: QWidget, add_to_history: bool = True):
        """
        shows the given window object
        :param window: window to show inside this MasterWindow
        :param add_to_history: whether to add current window to navigation history
        """
        current_widget = self.stacked_widget.currentWidget()

        # Add current window to history before switching (if it exists and we want history)
        if current_widget and add_to_history:
            self.navigation_stack.append(current_widget)

        # Remove current widget if it exists
        if current_widget:
            self.stacked_widget.removeWidget(current_widget)

        self.stacked_widget.addWidget(window)
        self.stacked_widget.setCurrentWidget(window)
        self.stacked_widget.setWindowTitle(window.windowTitle())
        self.current_window = window
        # Re-center after switching content (size/layout may have changed)
        self._center_window()

    def can_go_back(self) -> bool:
        """
        Check if we can navigate back
        """
        return len(self.navigation_stack) > 0

    def go_back(self):
        """
        Navigate back to the previous window
        """
        if self.can_go_back():
            previous_window = self.navigation_stack.pop()
            self.switch_to(previous_window, add_to_history=False)
            return True
        return False

    def clear_navigation_history(self):
        """
        Clear the navigation history (useful when starting a new workflow)
        """
        self.navigation_stack.clear()

    def show(self):
        """
        show this MasterWindow
        """
        self.stacked_widget.show()
        # Re-center after showing to ensure proper positioning
        self._center_window()

    def maximize(self):
        """
        maximize this window
        """
        # self.stacked_widget.setWindowState(Qt.WindowMaximized)
        self.stacked_widget.setWindowState(Qt.WindowState.WindowMaximized)

    def activate(self):
        """
        sets focus on this window (needed as it is shown after the splashscreen)
        """
        self.stacked_widget.activateWindow()
        self.stacked_widget.raise_()
        self.stacked_widget.setWindowState(Qt.WindowState.WindowActive)

    # event has to be passed even though it _seems_ to be unused
    def __stacked_widget_close_event(self, event):
        """
        closing callback
        """
        # Close the currently visible window first
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            try:
                current_widget.close()
            except Exception:
                pass

        # Also close any windows kept in the navigation history to ensure
        # they release resources (e.g., Dash servers) when quitting the app
        try:
            while self.navigation_stack:
                previous = self.navigation_stack.pop()
                try:
                    previous.close()
                except Exception:
                    pass
        except Exception:
            pass

import config
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QIcon


class MasterWindow:
    """Flexible Window that shows other windows inside"""

    def __init__(self):
        """
        init MasterWindow
        """
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.resize(
            config.window_start_size_width, config.window_start_size_height
        )
        self.stacked_widget.closeEvent = self.__stacked_widget_close_event
        self.stacked_widget.setWindowIcon(QIcon("./media/icon.ico"))

        # Center the window on screen
        self._center_window()

        # Navigation history for back functionality
        self.navigation_stack = []
        self.current_window = None

    def _center_window(self):
        """
        Center the window on the screen
        """
        # Get the screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Get the window size
        window_size = self.stacked_widget.size()

        # Calculate center position
        x = (screen_geometry.width() - window_size.width()) // 2
        y = (screen_geometry.height() - window_size.height()) // 2

        # Move the window to center
        self.stacked_widget.move(x, y)

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
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            current_widget.close()

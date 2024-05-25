import config
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QIcon

class MasterWindow:
    """Flexible Window that shows other windows inside"""

    def __init__(self):
        """
        init MasterWindow
        """
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.stacked_widget.resize(config.window_start_size_width, config.window_start_size_height)
        self.stacked_widget.closeEvent = self.__stacked_widget_close_event
        self.stacked_widget.setWindowIcon(QIcon("./media/mini-icon.png"))

    def switch_to(self, window: QWidget):
        """
        shows the given window object
        :param window: window to show inside this MasterWindow
        """
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            self.stacked_widget.removeWidget(current_widget)
        self.stacked_widget.addWidget(window)
        self.stacked_widget.setCurrentWidget(window)
        self.stacked_widget.setWindowTitle(window.windowTitle())

    def show(self):
        """
        show this MasterWindow
        """
        self.stacked_widget.show()

    def maximize(self):
        """
        maximize this window
        """
        #self.stacked_widget.setWindowState(Qt.WindowMaximized)
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

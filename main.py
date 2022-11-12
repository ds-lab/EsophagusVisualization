import sys
from PyQt5.QtWidgets import QApplication
from file_selection_window import FileSelectionWindow
from PyQt5 import QtWidgets, QtCore
from master_window import MasterWindow

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # create the MasterWindow and show the first UI
    master_window = MasterWindow()
    master_window.show()
    master_window.activate()
    file_selection_window = FileSelectionWindow(master_window)
    master_window.switch_to(file_selection_window)
    try:
        # close the splash screen if running as pyinstaller-exe
        import pyi_splash
        pyi_splash.close()
    except ModuleNotFoundError:
        pass
    app.exec_()

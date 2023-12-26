import sys

from gui.file_selection_window import FileSelectionWindow
from gui.master_window import MasterWindow
from logic.database import create_db_and_tables_local, create_db_and_tables_local_declarative
from gui.select_center_window import SelectCenterWindow
from PyQt6.QtWidgets import QApplication

# Upgrade to Qt6 https://www.pythonguis.com/faq/pyqt5-vs-pyqt6/#:~:text=The%20upgrade%20path%20from%20PyQt5,both%20PyQt%20and%20Qt%20itself.
# The high DPI (dots per inch) scaling attributes 
# Qt.AA_EnableHighDpiScaling, Qt.AA_DisableHighDpiScaling and Qt.AA_UseHighDpiPixmaps have been deprecated because high DPI is enabled by default in PyQt6 and can’t be disabled

#QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)  #Qt5
#QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)  #Qt5
#QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts, True)  #Qt5

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # create the MasterWindow and show the first UI

    master_window = MasterWindow()
    master_window.show()
    master_window.activate()
    select_center_window = SelectCenterWindow(master_window)
    master_window.switch_to(select_center_window)
    #file_selection_window = FileSelectionWindow(master_window)
    #master_window.switch_to(file_selection_window)
    create_db_and_tables_local_declarative()
    try:
        # close the splash screen if running as pyinstaller-exe
        import pyi_splash
        pyi_splash.close()
    except ModuleNotFoundError:
        pass
    app.exec()

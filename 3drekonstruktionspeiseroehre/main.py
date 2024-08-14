import sys

from gui.master_window import MasterWindow
from logic.database.database import create_db_and_tables_local_declarative
from PyQt6.QtWidgets import QApplication
from gui.data_window import DataWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # create the MasterWindow and show the first UI

    master_window = MasterWindow()
    master_window.show()
    master_window.activate()
    data_window = DataWindow(master_window)
    master_window.switch_to(data_window)
    create_db_and_tables_local_declarative()
    try:
        # close the splash screen if running as pyinstaller-exe
        import pyi_splash

        pyi_splash.close()
    except ModuleNotFoundError:
        pass
    app.exec()

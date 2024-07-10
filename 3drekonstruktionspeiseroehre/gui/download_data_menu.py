from PyQt6 import uic, QtCore
from PyQt6.QtWidgets import QMainWindow, QFileDialog


class DownloadData(QMainWindow):  # Ändere die Basisklasse zu QMainWindow
    data_selected = QtCore.pyqtSignal(list, str)

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("./ui-files/download_data_menu_design.ui", self)

        # Connect Buttons to Functions
        self.ui.check_all_button.clicked.connect(self.__check_all_button_clicked)
        self.ui.uncheck_all_button.clicked.connect(self.__uncheck_all_button_clicked)
        self.ui.download_data_button.clicked.connect(self.__download_data_button_clicked)

        self.checkboxes = [
            self.ui.previous_therapies,
            self.ui.eckardt_scores,
            self.ui.gerd_scores,
            self.ui.medications,
            self.ui.manometries,
            self.ui.barium_swallows,
            self.ui.endoscopies,
            self.ui.endoflips,
            self.ui.botox_injections,
            self.ui.poems,
            self.ui.pneumatic_dilations,
            self.ui.lhms,
            self.ui.complications
        ]

    def __check_all_button_clicked(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def __uncheck_all_button_clicked(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def __download_data_button_clicked(self):
        selected_data = ['patients', 'visits']
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                selected_data.append(checkbox.objectName())

        # Prompt the user to choose a destination directory
        destination_file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")

        if destination_file_path:
            # Emit the signal with the selected data and file path
            self.data_selected.emit(selected_data, destination_file_path)
            # Close the dialog
            self.close()

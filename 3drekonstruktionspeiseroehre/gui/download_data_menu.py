from PyQt6 import uic, QtCore
from PyQt6.QtWidgets import QDialog, QFileDialog


class DownloadData(QDialog):
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
            self.ui.eckardt_score,
            self.ui.gerd_score,
            self.ui.medication,
            self.ui.manometry,
            self.ui.barium_swallow,
            self.ui.endoscopy,
            self.ui.endoflip,
            self.ui.botox_injection,
            self.ui.poem,
            self.ui.pneumatic_dilation,
            self.ui.lhm,
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
                selected_data.append(checkbox.text())

        # Prompt the user to choose a destination directory
        destination_file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")

        if destination_file_path:
            # Emit the signal with the selected data and file path
            self.data_selected.emit(selected_data, destination_file_path)
            # Close the dialog
            self.close()

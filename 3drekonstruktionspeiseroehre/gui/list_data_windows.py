from PyQt6.QtWidgets import QMainWindow, QTableView

from logic.pyqt_models import PatientTableModel


class ListPatients(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 800, 600)

        # Erstelle das Model als Klassenattribut
        self.patient_model = PatientTableModel()

        # Erstelle die Ansicht
        view = QTableView(self)
        view.setModel(self.patient_model)

        self.setCentralWidget(view)
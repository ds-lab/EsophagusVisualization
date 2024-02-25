from PyQt6 import QtCore, uic, QtWidgets, QtGui
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout, QMainWindow
from sqlalchemy.orm import sessionmaker

from gui.master_window import MasterWindow
from logic.database import database
from logic.database.data_declarative_models import Patient
from logic.services.patient_service import PatientService

from logic.database.pyqt_models import CustomPatientModel



class ShowDataWindow(QMainWindow):

    def __init__(self, master_window: MasterWindow):
        super(ShowDataWindow, self).__init__()
        self.ui = uic.loadUi("./ui-files/show_data_window_design.ui", self)
        self.tableView = self.ui.tableView
        self.master_window = master_window
        self.db = database.get_db()
        self.patient_service = PatientService(self.db)

        Session = sessionmaker(bind=database.engine_local.connect())
        session = Session()

        patientsArr = []
        for patient in session.query(Patient).all():
            patientsArr.append(patient.toDict())

        self.user_data = patientsArr

        # self.user_data = self.patient_service.get_all_patients()
        print(f"USER DATA: {self.user_data}")
        # self.user_data = databaseOperations.get_multiple_data()
        self.model = CustomPatientModel(self.user_data)
        # self.delegate = InLineEditDelegate() # for inline editing
        self.tableView.setModel(self.model)
        self.tableView.setItemDelegate(self.delegate)
        self.tableView.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.context_menu)
        self.tableView.verticalHeader().setDefaultSectionSize(30)
        self.tableView.setColumnWidth(0, 50)
        self.tableView.resizeColumnsToContents()
        #self.tableView.hideColumn(0)
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QAbstractTableModel, QVariant
from PyQt6.QtSql import QSqlTableModel
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout
from PyQt6.lupdate import user
from sqlalchemy.orm import sessionmaker

from logic import database
from logic.data_declarative_models import Patient
from logic.services import patient_service
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService


class PatientView(QWidget):

    def __init__(self, rows):
        super(PatientView, self).__init__()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        # Optional, set the labels that show on top
        self.table.setHorizontalHeaderLabels(("patient_id", "ancestry", "birth_year", "previous_therapies"))

        self.table.setRowCount(len(rows))
        for row, cols in enumerate(rows):
            for col, text in enumerate(cols):
                table_item = QTableWidgetItem(text)
                # Optional, but very useful.
                #table_item.setData(QtCore.Qt.UserRole+1, user)
                self.table.setItem(row, col, table_item)

        # Also optional. Will fit the cells to its contents.
        self.table.resizeColumnsToContents()

        # Just display the table here.
        layout = QHBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)
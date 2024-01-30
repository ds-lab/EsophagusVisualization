from PyQt6.QtCore import Qt, QAbstractTableModel, QVariant
from PyQt6.QtSql import QSqlTableModel
from sqlalchemy.orm import sessionmaker

from logic import database
from logic.data_declarative_models import Patient
from logic.services import patient_service
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService


class PatientTableModel(QAbstractTableModel):

    def __init__(self, parent, header, *args):
        self.db = database.get_db()
        self.patient_service = PatientService(self.db)
        self.visit_service = VisitService(self.db)

        QAbstractTableModel.__init__(self, parent, *args)
        # fetch data
        results = patient_service.get_all_patients()
        #results = connection.execute(db.select([demoTable])).fetchall()
        self.mylist = results
        self.header = header

    def rowCount(self, parent):
        return len(self.mylist)

    def columnCount(self, parent):
        return len(self.mylist[0])

    def data(self, index, role):
        # populate data
        if not index.isValid():
            return None
        if (role == Qt.DisplayRole):
            return self.mylist[index.row()][index.column()]
        else:
            return QVariant()

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None
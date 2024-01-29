from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlTableModel


class PatientTableModel(QSqlTableModel):
    def __init__(self):
        super().__init__()

        self.setTable("patients")  
        self.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.select()
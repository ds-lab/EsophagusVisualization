from PyQt6 import QtCore, uic, QtWidgets, QtGui
from PyQt6.QtCore import Qt, QAbstractTableModel, QVariant
from PyQt6.QtSql import QSqlTableModel
from PyQt6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout, QMainWindow
from PyQt6.lupdate import user
from sqlalchemy.orm import sessionmaker

from gui.master_window import MasterWindow
from logic import database
from logic.data_declarative_models import Patient
from logic.services import patient_service
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService


class PatientView(QMainWindow):

    def __init__(self, master_window: MasterWindow):
        super(PatientView, self).__init__()
        self.ui = uic.loadUi("./ui-files/show_data_design.ui", self)
        self.master_window = master_window

        self.user_data = databaseOperations.get_multiple_data()
        self.model = CustomPatientModel(self.user_data)
        self.delegate = InLineEditDelegate()
        self.tableView.setModel(self.model)
        self.tableView.setItemDelegate(self.delegate)
        self.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.context_menu)
        self.tableView.verticalHeader().setDefaultSectionSize(50)
        self.tableView.setColumnWidth(0, 30)
        self.tableView.hideColumn(0)
        self.tableView_2.setModel(self.model)
        self.tableView_3.setModel(self.model)

    def context_menu(self):
        menu = QtWidgets.QMenu()
        add_data = menu.addAction("Add New Data")
        add_data.setIcon(QtGui.QIcon(":/icons/images/add-icon.png"))
        add_data.triggered.connect(lambda: self.model.insertRows())
        if self.tableView.selectedIndexes():
            remove_data = menu.addAction("Remove Data")
            remove_data.setIcon(QtGui.QIcon(":/icons/images/remove.png"))
            remove_data.triggered.connect(lambda: self.model.removeRows(self.tableView.currentIndex()))
        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())


# adapted from: https://github.com/vfxpipeline/Python-MongoDB-Example/blob/master/lib/customModel.py
class CustomPatientModel(QtCore.QAbstractTableModel):
    """
    Custom Table Model to handle DB-Data
    """


    def __init__(self, data):
        QtCore.QAbstractTableModel.__init__(self)
        self.user_data = data
        self.columns = list(self.user_data[0].keys())
        self.db = database.get_db()
        self.patient_service = PatientService(self.db)

    def flags(self, index):
        """
        Make table editable.
        make first column non editable
        :param index:
        :return:
        """
        if index.column() > 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
        elif index.column() == 1:
            return QtCore.Qt.DecorationRole
        else:
            return QtCore.Qt.ItemIsSelectable

    def rowCount(self, *args, **kwargs):
        """
        set row counts
        :param args:
        :param kwargs:
        :return:
        """
        return len(self.user_data)

    def columnCount(self, *args, **kwargs):
        """
        set column counts
        :param args:
        :param kwargs:
        :return:
        """
        return len(self.columns)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        set column header data
        :param section:
        :param orientation:
        :param role:
        :return:
        """
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.columns[section].title()

    def data(self, index, role):
        """
        Display Data in table cells
        :param index:
        :param role:
        :return:
        """
        row = self.user_data[index.row()]
        column = self.columns[index.column()]
        try:
            # if index.column() == 1:
            #     selected_row = self.user_data[index.row()]
            #     image_data = selected_row['photo']
            #     image = QtGui.QImage()
            #     image.loadFromData(image_data)
            #     icon = QtGui.QIcon()
            #     icon.addPixmap(QtGui.QPixmap.fromImage(image))
            #     return icon
            # elif role == QtCore.Qt.DisplayRole:
            return str(row[column])
        except KeyError:
            return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """
        Edit data in table cells
        :param index:
        :param value:
        :param role:
        :return:
        """
        if index.isValid():
            selected_row = self.user_data[index.row()]
            selected_column = self.columns[index.column()]
            selected_row[selected_column] = value
            self.dataChanged.emit(index, index, (QtCore.Qt.DisplayRole,))
            ok = self.patient_service.update_patient(selected_row['_id'], selected_row)
            # ok = databaseOperations.update_existing(selected_row['_id'], selected_row)
            if ok:
                return True
        return False

    def insertRows(self):
        row_count = len(self.user_data)
        self.beginInsertRows(QtCore.QModelIndex(), row_count, row_count)
        empty_data = {key: None for key in self.columns if not key == '_id'}
        document_id = self.patient_service.create_patient(empty_data)
        # document_id = databaseOperations.insert_data(empty_data)
        new_data = self.patient_service.get_patient(document_id)
        # new_data = databaseOperations.get_single_data(document_id)
        self.user_data.append(new_data)
        row_count += 1
        self.endInsertRows()
        return True

    def removeRows(self, position):
        row_count = self.rowCount()
        row_count -= 1
        self.beginRemoveRows(QtCore.QModelIndex(), row_count, row_count)
        row_id = position.row()
        document_id = self.user_data[row_id]['_id']
        self.patient_service.delete_patient(document_id)
        # databaseOperations.remove_data(document_id)
        self.user_data.pop(row_id)
        self.endRemoveRows()
        return True


class ProfilePictureDelegate(QtWidgets.QStyledItemDelegate):
    """
    This will open QFileDialog to select image
    """

    def __init__(self):
        QtWidgets.QStyledItemDelegate.__init__(self)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QFileDialog()
        return editor

    def setModelData(self, editor, model, index):
        selected_file = editor.selectedFiles()[0]
        image = open(selected_file, 'rb').read()
        model.setData(index, image)


class InLineEditDelegate(QtWidgets.QItemDelegate):
    """
    Delegate is important for inline editing of cells
    """

    def createEditor(self, parent, option, index):
        return super(InLineEditDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        text = index.data(QtCore.Qt.EditRole) or index.data(QtCore.Qt.DisplayRole)
        editor.setText(str(text))

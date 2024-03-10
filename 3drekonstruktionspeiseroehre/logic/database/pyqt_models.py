from PyQt6 import QtCore, uic, QtWidgets, QtGui
from PyQt6.QtCore import Qt
from logic.database import database
from logic.services.patient_service import PatientService
from logic.services.previous_therapy_service import PreviousTherapyService
from logic.services.visit_service import VisitService


# adapted from: https://github.com/vfxpipeline/Python-MongoDB-Example/blob/master/lib/customModel.py
class CustomPatientModel(QtCore.QAbstractTableModel):
    """
    Custom Table Model to handle DB-Data
    """

    def __init__(self, data):
        QtCore.QAbstractTableModel.__init__(self)
        if data is None: # in case a database-connection could not be established
            self.patient_array = []
            self.columns = []
        else:
            self.patient_array = data
            self.columns = list(self.patient_array[0].keys()) if self.patient_array else [] # in case there are no data in the database
        self.db = database.get_db()
        self.patient_service = PatientService(self.db)

    def flags(self, index):
        """
        Make only first column selectable
        """
        if index.column() > 0:
            return Qt.ItemFlag.ItemIsEnabled
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def rowCount(self, *args, **kwargs):
        """
        set row counts
        """
        return len(self.patient_array)

    def columnCount(self, *args, **kwargs):
        """
        set column counts
        """
        return len(self.columns)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """
        set column header data
        """
        if orientation == QtCore.Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section].title()

    def data(self, index, role):
        """
        Display Data in table cells
        """
        row = self.patient_array[index.row()]
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
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return str(row[column])
        except KeyError:
            return None

    # def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
    #     """
    #     Edit data in table cells
    #     :param index:
    #     :param value:
    #     :param role:
    #     :return:
    #     """
    #     if index.isValid():
    #         selected_row = self.patient_array[index.row()]
    #         selected_column = self.columns[index.column()]
    #         selected_row[selected_column] = value
    #         self.dataChanged.emit(index, index, (Qt.ItemDataRole.DisplayRole,))
    #         ok = self.patient_service.update_patient(selected_row['patient_id'], selected_row)
    #         if ok:
    #             return True
    #     return False

    def insertRows(self):
        row_count = len(self.patient_array)
        self.beginInsertRows(QtCore.QModelIndex(), row_count, row_count)
        empty_data = {key: None for key in self.columns if not key == 'patient_id'}
        document_id = self.patient_service.create_patient(empty_data)
        new_data = self.patient_service.get_patient(document_id)
        self.patient_array.append(new_data)
        row_count += 1
        self.endInsertRows()
        return True

    def removeRows(self, position):
        row_count = self.rowCount()
        row_count -= 1
        self.beginRemoveRows(QtCore.QModelIndex(), row_count, row_count)
        row_id = position.row()
        document_id = self.patient_array[row_id]['patient_id']
        self.patient_service.delete_patient(document_id)
        self.patient_array.pop(row_id)
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


class CustomPreviousTherapyModel(QtCore.QAbstractTableModel):
    """
    Custom Table Model to handle DB-Data
    """

    def __init__(self, data):
        QtCore.QAbstractTableModel.__init__(self)
        self.previous_therapies_array = data
        self.columns = list(self.previous_therapies_array[0].keys()) if self.previous_therapies_array != [] else []
        self.db = database.get_db()
        self.previous_therapies_service = PreviousTherapyService(self.db)

    def flags(self, index):
        """
        Make only first column selectable
        """
        if index.column() > 0:
            return Qt.ItemFlag.ItemIsEnabled
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def rowCount(self, *args, **kwargs):
        """
        set row counts
        """
        return len(self.previous_therapies_array)

    def columnCount(self, *args, **kwargs):
        """
        set column counts
        """
        return len(self.columns)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """
        set column header data
        """
        if orientation == QtCore.Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section].title()

    def data(self, index, role):
        """
        Display Data in table cells
        """
        row = self.previous_therapies_array[index.row()]
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
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return str(row[column])
        except KeyError:
            return None

    # def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
    #     """
    #     Edit data in table cells
    #     :param index:
    #     :param value:
    #     :param role:
    #     :return:
    #     """
    #     if index.isValid():
    #         selected_row = self.patient_array[index.row()]
    #         selected_column = self.columns[index.column()]
    #         selected_row[selected_column] = value
    #         self.dataChanged.emit(index, index, (Qt.ItemDataRole.DisplayRole,))
    #         ok = self.patient_service.update_patient(selected_row['patient_id'], selected_row)
    #         if ok:
    #             return True
    #     return False

    def insertRows(self):
        row_count = len(self.previous_therapies_array)
        self.beginInsertRows(QtCore.QModelIndex(), row_count, row_count)
        empty_data = {key: None for key in self.columns if not key == 'previous_therapy_id'}
        document_id = self.previous_therapies_service.create_previous_therapy(empty_data)
        new_data = self.previous_therapies_service.get_previous_therapy(document_id)
        self.previous_therapies_array.append(new_data)
        row_count += 1
        self.endInsertRows()
        return True

    def removeRows(self, position):
        row_count = self.rowCount()
        row_count -= 1
        self.beginRemoveRows(QtCore.QModelIndex(), row_count, row_count)
        row_id = position.row()
        document_id = self.previous_therapies_array[row_id]['previous_therapy_id']
        self.previous_therapies_service.delete_previous_therapy(document_id)
        self.previous_therapies_array.pop(row_id)
        self.endRemoveRows()
        return True


class CustomVisitsModel(QtCore.QAbstractTableModel):
    """
    Custom Table Model to handle DB-Data
    """

    def __init__(self, data):
        QtCore.QAbstractTableModel.__init__(self)
        self.visits_array = data
        self.columns = list(self.visits_array[0].keys()) if self.visits_array != [] else []
        self.db = database.get_db()
        self.visit_service = VisitService(self.db)

    def flags(self, index):
        """
        Make only first column selectable
        """
        if index.column() > 0:
            return Qt.ItemFlag.ItemIsEnabled
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def rowCount(self, *args, **kwargs):
        """
        set row counts
        """
        return len(self.visits_array)

    def columnCount(self, *args, **kwargs):
        """
        set column counts
        """
        return len(self.columns)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """
        set column header data
        """
        if orientation == QtCore.Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section].title()

    def data(self, index, role):
        """
        Display Data in table cells
        """
        row = self.visits_array[index.row()]
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
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return str(row[column])
        except KeyError:
            return None

    # def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
    #     """
    #     Edit data in table cells
    #     :param index:
    #     :param value:
    #     :param role:
    #     :return:
    #     """
    #     if index.isValid():
    #         selected_row = self.patient_array[index.row()]
    #         selected_column = self.columns[index.column()]
    #         selected_row[selected_column] = value
    #         self.dataChanged.emit(index, index, (Qt.ItemDataRole.DisplayRole,))
    #         ok = self.patient_service.update_patient(selected_row['patient_id'], selected_row)
    #         if ok:
    #             return True
    #     return False

    def insertRows(self):
        row_count = len(self.visits_array)
        self.beginInsertRows(QtCore.QModelIndex(), row_count, row_count)
        empty_data = {key: None for key in self.columns if not key == 'visit_id'}
        document_id = self.visit_service.create_visit(empty_data)
        new_data = self.visit_service.get_visity(document_id)
        self.visits_array.append(new_data)
        row_count += 1
        self.endInsertRows()
        return True

    def removeRows(self, position):
        row_count = self.rowCount()
        row_count -= 1
        self.beginRemoveRows(QtCore.QModelIndex(), row_count, row_count)
        row_id = position.row()
        document_id = self.visit_array[row_id]['visit_id']
        self.visit_service.delete_visit(document_id)
        self.visit_array.pop(row_id)
        self.endRemoveRows()
        return True
from PyQt6 import QtGui
from PyQt6.QtWidgets import QMessageBox
from flask import jsonify
from sqlalchemy import select, delete, update, insert, func
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import BariumSwallowFile, BariumSwallow, Visit
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError


class BariumSwallowService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_barium_swallow(self, id: int):
        stmt = select(BariumSwallow).where(BariumSwallow.tbe_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_barium_swallow_for_visit(self, visit_id: int) -> list[BariumSwallow, None]:
        stmt = select(BariumSwallow).where(BariumSwallow.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def delete_barium_swallow_for_visit(self, visit_id: int):
        stmt = delete(BariumSwallow).where(BariumSwallow.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_barium_swallow(self, id: int):
        stmt = delete(BariumSwallow).where(BariumSwallow.tbe_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_barium_swallow(self, id: int, data: dict):
        stmt = update(BariumSwallow).where(BariumSwallow.tbe_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_barium_swallow(self, data: dict):
        stmt = insert(BariumSwallow).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()


class BariumSwallowFileService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_barium_swallow_file(self, id: int):
        stmt = select(BariumSwallowFile).where(BariumSwallowFile.tbe_file_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_barium_swallow_files_for_visit(self, visit_id: int) -> list[BariumSwallowFile, None]:
        stmt = select(BariumSwallowFile).where(BariumSwallowFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).all()
            if result:
                return [row[0] for row in result]
            else:
                return None
        except OperationalError as e:
            self.show_error_msg()

    def delete_barium_swallow_file(self, id: str):
        stmt = delete(BariumSwallowFile).where(BariumSwallowFile.tbe_file_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_barium_swallow_files_for_visit(self, visit_id: str):
        stmt = delete(BariumSwallowFile).where(BariumSwallowFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_barium_swallow_file(self, id: str, data: dict):
        stmt = update(BariumSwallowFile).where(BariumSwallowFile.tbe_file_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_barium_swallow_file(self, data: dict):
        stmt = insert(BariumSwallowFile).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def get_all_barium_swallow_files(self) -> list[BariumSwallowFile, None]:
        stmt = select(BariumSwallowFile)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()

    def get_barium_swallow_image(self, id: int):
        stmt = select(BariumSwallowFile).where(BariumSwallowFile.tbe_file_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                image = result[0].file
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image, 'jpeg')
                return pixmap
        except OperationalError as e:
            self.show_error_msg()

    def get_barium_swallow_images_for_visit(self, visit_id: int):
        try:
            stmt = select(BariumSwallowFile).where(BariumSwallowFile.visit_id == visit_id)
            results = self.db.execute(stmt).all()
            pixmaps = []
            if results:
                for barium_swallow_file in results:
                    image = barium_swallow_file[0].file
                    pixmap = QtGui.QPixmap()
                    pixmap.loadFromData(image, 'jpeg')
                    pixmaps.append(pixmap)
            return pixmaps
        except OperationalError as e:
            self.show_error_msg()

    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()

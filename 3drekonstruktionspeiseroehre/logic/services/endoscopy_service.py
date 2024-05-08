from PyQt6 import QtGui
from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert, func
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import EndoscopyFile, Endoscopy, Visit
from sqlalchemy.exc import OperationalError

class EndoscopyService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_endoscopy(self, id: int):
        stmt = select(Endoscopy).where(Endoscopy.egd_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_endoscopy_for_visit(self, visit_id: int) -> list[Endoscopy, None]:
        stmt = select(Endoscopy).where(Endoscopy.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def delete_endoscopy_for_visit(self, visit_id: int):
        stmt = delete(Endoscopy).where(Endoscopy.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_endoscopy(self, id: int):
        stmt = delete(Endoscopy).where(Endoscopy.egd_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_endoscopy(self, id: int, data: dict):
        stmt = update(Endoscopy).where(Endoscopy.egd_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_endoscopy(self, data: dict):
        stmt = insert(Endoscopy).values(**data)
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


class EndoscopyFileService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_endoscopy_file(self, id: int):
        stmt = select(EndoscopyFile).where(EndoscopyFile.endoscopy_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_endoscopy_files_for_visit(self, visit_id: int) -> list[EndoscopyFile, None]:
        stmt = select(EndoscopyFile).where(EndoscopyFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).all()
            if result:
                return [row[0] for row in result]
            else:
                return None
        except OperationalError as e:
            self.show_error_msg()

    def delete_endoscopy_file(self, id: str):
        stmt = delete(EndoscopyFile).where(EndoscopyFile.endoscopy_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_endoscopy_file_for_visit(self, visit_id: str):
        stmt = delete(EndoscopyFile).where(EndoscopyFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_endoscopy_file(self, id: str, data: dict):
        stmt = update(EndoscopyFile).where(EndoscopyFile.endoscopy_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_endoscopy_file(self, data: dict):
        stmt = insert(EndoscopyFile).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def get_all_endoscopy_files(self) -> list[EndoscopyFile, None]:
        stmt = select(EndoscopyFile)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()

    def count_endoscopy_files(self) -> int:
        stmt = select(func.count()).select_from(EndoscopyFile).join(Visit).where(Visit.visit_id == id)
        try:
            result = self.db.execute(stmt).scalar()
            return result
        except OperationalError as e:
            self.show_error_msg()

    def get_endoscopy_image(self, id: int):
        stmt = select(EndoscopyFile).where(EndoscopyFile.endoscopy_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                image = result[0].file
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image, 'jpeg')
                return pixmap
        except OperationalError as e:
            self.show_error_msg()

    def get_endoscopy_images_for_visit(self, visit_id: int):
        try:
            stmt = select(EndoscopyFile).where(EndoscopyFile.visit_id == visit_id)
            results = self.db.execute(stmt).all()
            pixmaps = []
            if results:
                for endoscopy_file in results:
                    image = endoscopy_file[0].file
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


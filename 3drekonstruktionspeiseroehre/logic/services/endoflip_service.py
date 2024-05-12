from PyQt6.QtWidgets import QMessageBox
from PyQt6 import QtGui
from sqlalchemy import select, delete, update, insert
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import Endoflip, EndoflipFile, EndoflipImage


class EndoflipService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_endoflip(self, id: int):
        stmt = select(Endoflip).where(Endoflip.endoflip_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_endoflip_for_visit(self, visit_id: int) -> list[Endoflip, None]:
        stmt = select(Endoflip).where(Endoflip.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def delete_endoflip_for_visit(self, visit_id: int):
        stmt = delete(Endoflip).where(Endoflip.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_endoflip(self, id: int):
        stmt = delete(Endoflip).where(Endoflip.endoflip_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_endoflip(self, id: int, data: dict):
        stmt = update(Endoflip).where(Endoflip.endoflip_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_endoflip(self, data: dict):
        stmt = insert(Endoflip).values(**data)
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


class EndoflipFileService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_endoflip_file(self, id: int):
        stmt = select(EndoflipFile).where(EndoflipFile.endoflip_file_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_endoflip_files_for_visit(self, visit_id: int) -> list[EndoflipFile, None]:
        stmt = select(EndoflipFile).where(EndoflipFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).all()
            if result:
                return [row[0] for row in result]
            else:
                return None
        except OperationalError as e:
            self.show_error_msg()

    def delete_endoflip_file_for_visit(self, visit_id: int):
        stmt = delete(EndoflipFile).where(EndoflipFile.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_endoflip_file(self, id: int):
        stmt = delete(EndoflipFile).where(EndoflipFile.endoflip_file_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_endoflip_file(self, id: int, data: dict):
        stmt = update(EndoflipFile).where(EndoflipFile.endoflip_file_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_endoflip_file(self, data: dict):
        stmt = insert(EndoflipFile).values(**data)
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


class EndoflipImageService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_endoflip_image(self, id: int):
        stmt = select(EndoflipImage).where(EndoflipImage.endoflip_image_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_endoflip_timepoints_for_visit(self, visit_id: int) -> list[EndoflipImage, None]:
        stmt = select(EndoflipImage).where(EndoflipImage.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).all()
            if result:
                return [row[0].timepoint for row in result]
            else:
                return None
        except OperationalError as e:
            self.show_error_msg()

    def delete_endoflip_image(self, id: str):
        stmt = delete(EndoflipImage).where(EndoflipImage.endoflip_image_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_endoflip_images_for_visit(self, visit_id: str):
        stmt = delete(EndoflipImage).where(EndoflipImage.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_endoflip_image(self, id: str, data: dict):
        stmt = update(EndoflipImage).where(EndoflipImage.endoflip_image_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_endoflip_image(self, data: dict):
        stmt = insert(EndoflipImage).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def get_all_endoflip_images(self) -> list[EndoflipImage, None]:
        stmt = select(EndoflipImage)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()

    def get_endoflip_image(self, id: int):
        stmt = select(EndoflipImage).where(EndoflipImage.endoflip_image_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                image = result[0].file
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image, 'jpeg')
                return pixmap
        except OperationalError as e:
            self.show_error_msg()

    def get_endoflip_images_for_visit(self, visit_id: int):
        try:
            stmt = select(EndoflipImage).where(EndoflipImage.visit_id == visit_id)
            results = self.db.execute(stmt).all()
            pixmaps = []
            if results:
                for endoflip_file in results:
                    image = endoflip_file[0].file
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

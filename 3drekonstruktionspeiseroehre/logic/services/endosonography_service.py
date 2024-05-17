from PyQt6 import QtGui
from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert, func
from sqlalchemy.orm import Session
from logic.database.data_declarative_models import EndosonographyImage, EndosonographyVideo
from sqlalchemy.exc import OperationalError


class EndosonographyImageService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_endosonography_file(self, id: int):
        stmt = select(EndosonographyImage).where(EndosonographyImage.endosonography_image_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_endosonography_files_for_visit(self, visit_id: int) -> list[EndosonographyImage, None]:
        stmt = select(EndosonographyImage).where(EndosonographyImage.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).all()
            if result:
                return [row[0] for row in result]
            else:
                return None
        except OperationalError as e:
            self.show_error_msg()

    def delete_endosonography_file(self, id: str):
        stmt = delete(EndosonographyImage).where(EndosonographyImage.endosonography_image_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_endosonography_file_for_visit(self, visit_id: str):
        stmt = delete(EndosonographyImage).where(EndosonographyImage.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_endosonography_file(self, id: str, data: dict):
        stmt = update(EndosonographyImage).where(EndosonographyImage.endosonography_image_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_endosonography_file(self, data: dict):
        stmt = insert(EndosonographyImage).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def get_all_endosonography_files(self) -> list[EndosonographyImage, None]:
        stmt = select(EndosonographyImage)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()

    def get_endosonography_image(self, id: int):
        stmt = select(EndosonographyImage).where(EndosonographyImage.endosonography_image_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                image = result[0].file
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image, 'jpeg')
                return pixmap
        except OperationalError as e:
            self.show_error_msg()

    def get_endosonography_images_for_visit(self, visit_id: int):
        try:
            stmt = select(EndosonographyImage).where(EndosonographyImage.visit_id == visit_id)
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


class EndosonographyVideoService:

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_endosonography_file(self, id: int):
        stmt = select(EndosonographyVideo).where(EndosonographyVideo.endosonography_video_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                return result[0]
        except OperationalError as e:
            self.show_error_msg()

    def get_endosonography_files_for_visit(self, visit_id: int) -> list[EndosonographyVideo, None]:
        stmt = select(EndosonographyVideo).where(EndosonographyVideo.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).all()
            if result:
                return [row[0] for row in result]
            else:
                return None
        except OperationalError as e:
            self.show_error_msg()

    def delete_endosonography_file(self, id: str):
        stmt = delete(EndosonographyVideo).where(EndosonographyVideo.endosonography_video_id == id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def delete_endosonography_file_for_visit(self, visit_id: str):
        stmt = delete(EndosonographyVideo).where(EndosonographyVideo.visit_id == visit_id)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def update_endosonography_file(self, id: str, data: dict):
        stmt = update(EndosonographyVideo).where(EndosonographyVideo.endosonography_video_id == id).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def create_endosonography_file(self, data: dict):
        stmt = insert(EndosonographyVideo).values(**data)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount  # Return the number of rows affected
        except OperationalError as e:
            self.db.rollback()
            self.show_error_msg()

    def get_all_endosonography_files(self) -> list[EndosonographyImage, None]:
        stmt = select(EndosonographyImage)
        try:
            result = self.db.execute(stmt).all()
            return list(map(lambda row: row[0].toDict(), result))
        except OperationalError as e:
            self.show_error_msg()

    def get_endosonography_video(self, id: int):
        stmt = select(EndosonographyVideo).where(EndosonographyVideo.endosonography_video_id == id)
        try:
            result = self.db.execute(stmt).first()
            if result:
                image = result[0].file
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image, 'jpeg')
                return pixmap
        except OperationalError as e:
            self.show_error_msg()

    def get_endosonography_videos_for_visit(self, visit_id: int):
        try:
            stmt = select(EndosonographyVideo).where(EndosonographyVideo.visit_id == visit_id)
            results = self.db.execute(stmt).all()
            videos = []
            if results:
                for endosonography_file in results:
                    video = endosonography_file[0].file
                    videos.append(video)
            return videos
        except OperationalError as e:
            self.show_error_msg()

    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()


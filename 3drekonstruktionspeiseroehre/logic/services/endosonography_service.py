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
    def __init__(self, db_session, db_engine):
        self.db = db_session
        self.db_engine = db_engine

    def save_video_for_visit(self, visit_id: int, video_file_path: str):
        # Abrufen der rohen Verbindung für psycopg2-Operationen
        conn = self.db_engine.raw_connection()
        try:
            # Lesen der Videodatei als binäre Daten
            with open(video_file_path, 'rb') as f:
                video_data = f.read()

            # Erstellen eines neuen Large Object und Abrufen der OID
            with conn.cursor() as cursor:
                cursor.execute("SELECT lo_create(0)")
                oid = cursor.fetchone()[0]

                # Öffnen des Large Objects im Schreibmodus
                lo = conn.lobject(oid, 'wb')
                lo.write(video_data)
                lo.close()

                # Speichern der OID in der Datenbanktabelle
                new_video = EndosonographyVideo(visit_id=visit_id, video_oid=oid)
                self.db.add(new_video)
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
        finally:
            conn.close()

    def get_endosonography_videos_for_visit(self, visit_id: int):
        # Abrufen der rohen Verbindung für psycopg2-Operationen
        conn = self.db_engine.raw_connection()
        try:
            # Abfragen der Videodaten-Records basierend auf visit_id
            stmt = select(EndosonographyVideo).where(EndosonographyVideo.visit_id == visit_id)
            results = self.db.execute(stmt).scalars().all()

            videos = []
            if results:
                with conn.cursor() as cursor:
                    for video_record in results:
                        oid = video_record.video_oid
                        # Öffnen des Large Objects im Lesemodus und Abrufen der Videodaten
                        lo = conn.lobject(oid, 'rb')
                        video_data = lo.read()
                        lo.close()
                        videos.append(video_data)
            return videos
        except Exception as e:
            self.show_error_msg()
        finally:
            conn.close()

    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()


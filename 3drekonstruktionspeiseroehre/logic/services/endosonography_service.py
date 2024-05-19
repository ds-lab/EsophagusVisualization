from PyQt6 import QtGui
from PyQt6.QtWidgets import QMessageBox
from sqlalchemy import select, delete, update, insert, func
import psycopg2
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

    def get_video_oids_for_visit(self, visit_id: int):
        stmt = select(EndosonographyVideo).where(EndosonographyVideo.visit_id == visit_id)
        try:
            result = self.db.execute(stmt).all()
            if result:
                return [row[0].video_oid for row in result]
            else:
                return None
        except OperationalError as e:
            self.show_error_msg()

    def delete_videos_for_visit(self, visit_id: int):
        oids = self.get_video_oids_for_visit(visit_id)
        print(f"oids: {oids}")
        if not oids:
            print(f"No videos found for visit_id: {visit_id}")
            return

        conn = self.db_engine.raw_connection()
        try:
            with conn.cursor() as cursor:
                for oid in oids:
                    try:
                        cursor.execute("SELECT lo_unlink(%s)", (oid,))
                        print(f"Deleted Large Object with OID: {oid}")
                    except psycopg2.Error as e:
                        print(f"Error deleting Large Object with OID {oid}: {e}")

            conn.commit()

            # Entfernen der Einträge aus der Tabelle
            self.db.query(EndosonographyVideo).filter(EndosonographyVideo.visit_id == visit_id).delete()
            self.db.commit()
            print(f"Deleted video records for visit_id: {visit_id}")
        except Exception as e:
            conn.rollback()
            self.db.rollback()
            print(f"Error deleting videos for visit_id {visit_id}: {e}")
        finally:
            conn.close()

    def save_video_for_visit(self, visit_id: int, video_file_path: str):
        conn = self.db_engine.raw_connection()
        try:
            with open(video_file_path, 'rb') as f:
                video_data = f.read()

            with conn.cursor() as cursor:
                # Sicherstellen, dass die Transaktion gestartet wird
                conn.autocommit = False

                cursor.execute("SELECT lo_create(0)")
                oid = cursor.fetchone()[0]
                print(f"Created Large Object with OID: {oid}")

                lo = conn.lobject(oid, 'wb')
                lo.write(video_data)
                lo.close()

                # Sicherstellen, dass die Transaktion abgeschlossen wird
                conn.commit()

                # Speichern der OID in der Datenbanktabelle
                new_video = EndosonographyVideo(visit_id=visit_id, video_oid=oid)
                self.db.add(new_video)
                self.db.commit()
                print(f"Saved video for visit_id: {visit_id} with OID: {oid}")
        except Exception as e:
            self.db.rollback()
            print(f"Error saving video: {e}")
            raise e
        finally:
            conn.close()

    def get_endosonography_videos_for_visit(self, visit_id: int):
        conn = self.db_engine.raw_connection()
        try:
            stmt = select(EndosonographyVideo).where(EndosonographyVideo.visit_id == visit_id)
            results = self.db.execute(stmt).scalars().all()
            videos = []
            if results:
                with conn.cursor() as cursor:
                    for video_record in results:
                        oid = video_record.video_oid
                        print(f"Fetching video with OID: {oid}")
                        try:
                            lo = conn.lobject(oid, 'rb')
                            video_data = lo.read()
                            lo.close()
                            videos.append(video_data)
                        except psycopg2.Error as e:
                            print(f"Error fetching Large Object with OID {oid}: {e}")
                            continue
            return videos
        except Exception as e:
            print(f"Error: {e}")
            self.show_error_msg()
            return []
        finally:
            conn.close()

    def show_error_msg(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("An error occurred.")
        msg.setInformativeText("Please check the connection to the database.")
        msg.exec()


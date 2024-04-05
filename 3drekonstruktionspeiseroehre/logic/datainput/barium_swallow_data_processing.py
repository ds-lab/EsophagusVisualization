from PIL import Image
import re
from io import BytesIO
import os
from logic.services.barium_swallow_service import BariumSwallowFileService
from logic.database import database

def process_and_upload_barium_swallow_images(selected_visit, filenames):
    for i, filename in enumerate(filenames):
        match = re.search(r'(?P<time>[0-9]+)', filename)
        if match:
            time = int(match.group('time'))
            fileextension = os.path.splitext(filename)[1][1:]
            print(fileextension)
            if fileextension.lower() in ['jpg', 'jpeg']:
                extension = 'JPEG'
            elif fileextension.lower() in ['png']:
                extension = 'PNG'
            else:
                # Handle unsupported file extensions
                continue

            file = Image.open(filename)
            file_bytes = BytesIO()
            file.save(file_bytes, format=extension)
            file_bytes = file_bytes.getvalue()

            tbe_file_dict = {
                'visit_id': selected_visit,
                'filename': filename,  # ToDo Filename langfristig besser nicht abspeichern
                'file': file_bytes
            }

            db = database.get_db()
            barium_swallow_service = BariumSwallowFileService(db)
            barium_swallow_service.create_barium_swallow_file(tbe_file_dict)

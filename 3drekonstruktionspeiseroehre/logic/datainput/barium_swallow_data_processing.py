import re

from PIL import Image
from io import BytesIO
import os
from logic.services.barium_swallow_service import BariumSwallowFileService
from logic.database import database
from gui.show_message import ShowMessage


def process_and_upload_barium_swallow_images(selected_visit, filenames):
    for i, filename in enumerate(filenames):
        timeextract = os.path.basename(filename)
        match = re.search(r'(?P<time>[0-9]+)', timeextract)
        if match:
            time = match.group('time')
            fileextension = os.path.splitext(filename)[1][1:]

            if fileextension.lower() in ['jpg', 'jpeg']:
                extension = 'JPEG'
            elif fileextension.lower() in ['png']:
                extension = 'JPEG'
            else:
                ShowMessage.wrong_format(fileextension, ['JPEG', 'PNG'])
                break

            file = Image.open(filename)

            if fileextension.lower() == 'png':
                file = file.convert('RGB')

            file_bytes = BytesIO()
            file.save(file_bytes, format=extension)
            file_bytes = file_bytes.getvalue()

            tbe_file_dict = {
                'visit_id': selected_visit,
                'minute_of_picture': time,
                'file': file_bytes
            }

            db = database.get_db()
            barium_swallow_service = BariumSwallowFileService(db)
            barium_swallow_service.create_barium_swallow_file(tbe_file_dict)

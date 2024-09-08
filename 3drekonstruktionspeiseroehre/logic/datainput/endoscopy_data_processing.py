from PIL import Image
import re
from io import BytesIO
import os
from logic.services.endoscopy_service import EndoscopyFileService
from logic.database import database
from gui.show_message import ShowMessage


def process_and_upload_endoscopy_images(selected_visit, filenames):
    for i, filename in enumerate(filenames):
        match = re.search(r'_(?P<pos>[0-9]+)cm', filename)
        if match:
            position = int(match.group('pos'))
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

            endoscopy_file_dict = {
                'visit_id': selected_visit,
                'image_position': position,
                'file': file_bytes
            }

            db = database.get_db()
            endoscopy_service = EndoscopyFileService(db)
            endoscopy_service.create_endoscopy_file(endoscopy_file_dict)

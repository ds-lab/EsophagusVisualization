import re

from PIL import Image
from io import BytesIO
import os
from logic.services.endosonography_service import EndosonographyImageService
from logic.database import database
from gui.show_message import ShowMessage


def process_and_upload_endosonography_images(selected_visit, filenames):
    for i, filename in enumerate(filenames):
        positionextract = os.path.basename(filename)
        match = re.search(r'_(?P<pos>[0-9]+)cm', positionextract)
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

            file = file.convert('RGB')

            file_bytes = BytesIO()
            file.save(file_bytes, format=extension)
            file_bytes = file_bytes.getvalue()

            endosono_file_dict = {
                'visit_id': selected_visit,
                'image_position': position,
                'file': file_bytes
            }

            db = database.get_db()
            endosonography_service = EndosonographyImageService(db)
            endosonography_service.create_endosonography_file(endosono_file_dict)

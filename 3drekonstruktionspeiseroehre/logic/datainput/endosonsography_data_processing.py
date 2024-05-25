from PIL import Image
import re
from io import BytesIO
import os
from logic.services.endoscopy_service import EndoscopyFileService
from logic.database import database
import cv2
import pickle


def process_and_upload_endosonography_videos(selected_visit, filenames):
    for i, filename in enumerate(filenames):

        db = database.get_db()
        endoscopy_service = EndoscopyFileService(db)
        endoscopy_service.create_endoscopy_file(endoscopy_file_dict)
import os
from PIL import Image
from io import BytesIO
import pandas as pd
import re
from logic.services.endoflip_service import EndoflipFileService, EndoflipImageService
from logic.database import database
import pickle
from gui.show_message import ShowMessage


def conduct_endoflip_file_upload(selected_visit, timepoint, data_bytes, endoflip_screenshot):
    endoflip_bytes = pickle.dumps(endoflip_screenshot)
    endoflip_file_dict = {
        'visit_id': selected_visit,
        'timepoint': timepoint,
        'file': data_bytes,
        'screenshot': endoflip_bytes
    }
    db = database.get_db()
    endoflip_file_service = EndoflipFileService(db)
    endoflip_file_service.create_endoflip_file(endoflip_file_dict)


def process_endoflip_xlsx(file_path: str) -> dict:
    """
    Process an Endoflip data Excel file (.xlsx) and extract relevant information.

    Args:
        file_path (str): The path to the Excel file to be processed.

    Returns:
        dict: A dictionary containing extracted data and aggregates.
    """
    if not file_path or not file_path.endswith(".xlsx"):
        raise ValueError("Not xlsx format.")

    # Read the Excel file
    data = pd.read_excel(file_path, header=None)
    data_bytes = pickle.dumps(data)

    # Find starting header row (doctors use the first couple rows for their annotations)
    row_start = 0
    for row in range(data.shape[0]):
        if str(data.iat[row, 0]).startswith("Time,"):
            row_start = row
            break

    # Extract the comma-separated string of column names from the third row of the first column              
    column_names_str = data.iloc[row_start, 0]
    column_names = str(column_names_str).split(',')
    column_names = [name.strip() for name in column_names]

    # Drop the starting rows that don't contain data
    data = data.iloc[row_start + 1:]

    # Drop rows where all values are NaN
    data = data.dropna(how='all')

    # Split the first column into individual values using commas as separators (csv inside xlsx, see data)
    data.iloc[:, 0] = data.iloc[:, 0].apply(lambda x: x.split(',') if isinstance(x, str) else x)

    # Create a DataFrame with the comma-separated values as columns and assign the extracted column names
    df = pd.DataFrame(data.iloc[:, 0].to_list(), columns=column_names)

    # Filter those rows where the ballon is fully inflated to 30ml or 40ml
    filtered_data = df[(df['BV'].isin(['30', '40'])) & (df['Pump Status'] == 'S')]
    grouped_data = filtered_data.groupby('BV')

    # Define the regex pattern to select columns starting with 'E' and ending with 'DS050*' 
    pattern = re.compile(r'^E\d+DS(050|100)\*$')

    # Calculate the min,max,mean and median for both 30ml and 40ml
    aggregations = {}
    for name, group in grouped_data:
        selected_columns = group.filter(regex=pattern)

        # Extract distance (5mm or 10mm) in cm
        distance_string = pattern.search(selected_columns.columns[0]).group(1)
        if distance_string == "050":
            distance = 0.5
        else:
            distance = 1

        # Get aggregations including distance of sensors for both ballon volumes
        aggregations[name] = {
            'distance': distance,
            'aggregates': selected_columns.astype(float).agg(['min', 'max', 'mean', 'median'])
        }

    return data_bytes, aggregations


def process_and_upload_endoflip_images(selected_visit, filenames):
    for i, filename in enumerate(filenames):
        timeextract = os.path.basename(filename)
        match = re.search(r'(before|during|after)', timeextract)
        if match:
            timepoint = match.group(0)
            fileextension = os.path.splitext(filename)[1][1:]

            if fileextension.lower() in ['jpg', 'jpeg']:
                extension = 'JPEG'
            elif fileextension.lower() in ['png']:
                extension = 'JPEG'
            else:
                ShowMessage.wrong_format(fileextension, ['JPEG', 'PNG'])
                break

            file = Image.open(filename)

            if file.mode in ["RGBA", "P"]:
                file = file.convert("RGB")

            file_bytes = BytesIO()
            file.save(file_bytes, format=extension)
            file_bytes = file_bytes.getvalue()

            endoflip_image_dict = {
                'visit_id': selected_visit,
                'timepoint': timepoint,
                'file': file_bytes
            }

            db = database.get_db()
            endoflip_service = EndoflipImageService(db)
            endoflip_service.create_endoflip_image(endoflip_image_dict)

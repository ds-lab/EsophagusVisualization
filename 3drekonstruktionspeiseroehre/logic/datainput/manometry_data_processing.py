import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QMessageBox
import config
from logic.services.manometry_service import ManometryFileService
from logic.database import database
import pickle


def process_and_upload_manometry_file(selected_visit, filename):
    error = False
    try:
        file = pd.read_csv(filename, skiprows=config.csv_skiprows, header=0, index_col=0)
        df = file.drop(config.csv_drop_columns, axis=1)
        matrix = df.to_numpy()
        matrix = matrix.T  # sensors in axis 0
        pressure_matrix = np.flipud(matrix)  # sensors from top to bottom
    except:
        error = True
    if error or pressure_matrix.shape[1] < 1:
        QMessageBox.critical(None, "Invalid File", "Error: The file does not have the expected format.")

    if not error:
        pressure_matrix_bytes = pressure_matrix.tobytes()
        pressure_matrix_shape = pressure_matrix.shape
        file_bytes = pickle.dumps(file)
        manometry_file_dict = {
            'visit_id': selected_visit,
            'file': file_bytes,
            'pressure_matrix': pressure_matrix_bytes,
            'pressure_matrix_shape_0': pressure_matrix_shape[0],
            'pressure_matrix_shape_1': pressure_matrix_shape[1]
        }
        db = database.get_db()
        manometry_file_service = ManometryFileService(db)
        if manometry_file_service.get_manometry_file_for_visit(selected_visit):
            manometry_file = manometry_file_service.get_manometry_file_for_visit(selected_visit)
            manometry_file_service.update_manometry_file(manometry_file.manometry_file_id, manometry_file_dict)
        else:
            manometry_file_service.create_manometry_file(manometry_file_dict)

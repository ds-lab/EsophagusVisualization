import cv2
import numpy as np
from logic.figure_creator.figure_creator_with_endoscopy import FigureCreatorWithEndoscopy
from logic.figure_creator.figure_creator_without_endoscopy import FigureCreatorWithoutEndoscopy
from logic.visit_data import VisitData
from PyQt6.QtCore import QThread, pyqtSignal


class FigureCreationThread(QThread):
    """Thread that creates the plotly figure"""

    progress_value = pyqtSignal(int)
    return_value = pyqtSignal(VisitData)
    error_occurred = pyqtSignal(str)

    def __init__(self, visit: VisitData):
        """
        init FigureCreationThread
        :param visit: VisitData
        """
        super().__init__()
        self.visit = visit

    def run(self):
        """
        to be run as thread
        starts figure creation
        """
        try:
            # Work on a copy to allow filtering invalid visualizations
            original_visualizations = list(self.visit.visualization_data_list)
            valid_visualizations = []
            errors = []

            total = max(1, len(original_visualizations))

            for idx, visualization_data in enumerate(original_visualizations):
                try:
                    # Ensure X-ray dimensions exist; infer from file if missing
                    if getattr(visualization_data, "xray_image_height", None) is None or getattr(visualization_data, "xray_image_width", None) is None:
                        xray_file = getattr(visualization_data, "xray_file", None)
                        if xray_file is not None:
                            try:
                                # Read bytes from file-like object (BytesIO)
                                if hasattr(xray_file, "getvalue"):
                                    data_bytes = xray_file.getvalue()
                                else:
                                    try:
                                        xray_file.seek(0)
                                    except Exception:
                                        pass
                                    data_bytes = xray_file.read()
                                np_bytes = np.frombuffer(data_bytes, dtype=np.uint8)
                                decoded = cv2.imdecode(np_bytes, cv2.IMREAD_UNCHANGED)
                                if decoded is not None:
                                    h, w = decoded.shape[:2]
                                    visualization_data.xray_image_height = h
                                    visualization_data.xray_image_width = w
                            except Exception:
                                # Best-effort inference; continue to validation below
                                pass

                    # Validate essentials
                    if getattr(visualization_data, "xray_image_height", None) is None or getattr(visualization_data, "xray_image_width", None) is None:
                        raise ValueError("Missing X-ray image dimensions for visualization")
                    if getattr(visualization_data, "xray_polygon", None) is None or len(getattr(visualization_data, "xray_polygon", [])) < 3:
                        raise ValueError("Missing or invalid X-ray segmentation polygon for visualization")

                    # Create mask from polygon
                    mask = np.zeros((visualization_data.xray_image_height, visualization_data.xray_image_width))
                    cv2.drawContours(mask, [np.array(visualization_data.xray_polygon)], -1, 1, -1)
                    visualization_data.xray_mask = mask

                    # Update progress roughly to halfway across all items
                    self.progress_value.emit(int(50 * (idx + 1) / total))

                    # Create figure
                    if visualization_data.endoscopy_polygons is not None:
                        figure_creator = FigureCreatorWithEndoscopy(visualization_data)
                    else:
                        figure_creator = FigureCreatorWithoutEndoscopy(visualization_data)
                    visualization_data.figure_creator = figure_creator
                    valid_visualizations.append(visualization_data)
                except Exception as e_item:
                    errors.append(str(e_item))
                    # Skip this visualization and continue with the next one
                    continue

            # Keep only the valid visualizations
            self.visit.visualization_data_list = valid_visualizations

            if len(valid_visualizations) > 0:
                self.progress_value.emit(100)
                self.return_value.emit(self.visit)
            else:
                # All failed – report the first error
                message = errors[0] if errors else "Unknown error during figure creation"
                self.error_occurred.emit(message)
        except Exception as e:
            # Emit error signal with the error message
            self.error_occurred.emit(str(e))

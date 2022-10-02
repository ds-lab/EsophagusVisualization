import cv2
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from figure_creator import FigureCreator
from figure_creator_without_endoscopy import FigureCreatorWithoutEndoscopy
from figure_creator_with_endoscopy import FigureCreatorWithEndoscopy
from visualization_data import VisualizationData


class FigureCreationThread(QThread):
    """Thread that creates the plotly figure"""

    progress_value = pyqtSignal(int)
    return_value = pyqtSignal(FigureCreator)

    def __init__(self, visualization_data: VisualizationData):
        """
        init FigureCreationThread
        :param visualization_data: VisualizationData
        """
        super().__init__()
        self.visualization_data = visualization_data

    def run(self):
        """
        to be run as thread
        starts figure creation
        """
        mask = np.zeros((self.visualization_data.xray_image_height, self.visualization_data.xray_image_width))
        cv2.drawContours(mask, [np.array(self.visualization_data.xray_polygon)], -1, 1, -1)
        self.visualization_data.xray_mask = mask
        self.progress_value.emit(50)

        if self.visualization_data.endoscopy_polygons is not None:
            figure_creator = FigureCreatorWithEndoscopy(self.visualization_data)
        else:
            figure_creator = FigureCreatorWithoutEndoscopy(self.visualization_data)
        self.progress_value.emit(100)
        self.return_value.emit(figure_creator)

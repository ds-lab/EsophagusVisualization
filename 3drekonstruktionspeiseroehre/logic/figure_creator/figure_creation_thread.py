import cv2
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from logic.figure_creator.figure_creator import FigureCreator
from logic.figure_creator.figure_creator_without_endoscopy import FigureCreatorWithoutEndoscopy
from logic.figure_creator.figure_creator_with_endoscopy import FigureCreatorWithEndoscopy
from logic.visualization_data import VisualizationData
from logic.visit_data import VisitData


class FigureCreationThread(QThread):
    """Thread that creates the plotly figure"""

    progress_value = pyqtSignal(int)
    return_value = pyqtSignal(VisitData)

    def __init__(self, visit: VisitData):
        """
        init FigureCreationThread
        :param visualization_data: VisualizationData
        """
        super().__init__()
        self.visit = visit

    def run(self):
        """
        to be run as thread
        starts figure creation
        """
        for visualization_data in self.visit.visualization_data_list:
            mask = np.zeros((visualization_data.xray_image_height, visualization_data.xray_image_width))
            cv2.drawContours(mask, [np.array(visualization_data.xray_polygon)], -1, 1, -1)
            visualization_data.xray_mask = mask
            self.progress_value.emit(50)

            if visualization_data.endoscopy_polygons is not None:
                figure_creator = FigureCreatorWithEndoscopy(visualization_data)
            else:
                figure_creator = FigureCreatorWithoutEndoscopy(visualization_data)
            visualization_data.figure_creator = figure_creator

        self.progress_value.emit(100)
        self.return_value.emit(self.visit)

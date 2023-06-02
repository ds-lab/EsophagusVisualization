from typing import List
from logic.visualization_data import VisualizationData

class PatientData:
    def __init__(self):
        """
        init PatientData
        """
        self.visualization_data_list: List[VisualizationData] = []

    def number_of_visualizations(self) -> int:
        return len(self.visualization_data_list)

        
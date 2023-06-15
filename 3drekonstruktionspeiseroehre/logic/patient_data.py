from typing import List, Dict
from logic.visualization_data import VisualizationData

class PatientData:
    def __init__(self):
        """
        init PatientData
        """
        self.visualization_data_dict: Dict[str, VisualizationData] = {}

    def number_of_visualizations(self) -> int:
        return len(self.visualization_data_dict)

    def add_visualization(self, name: str, visualization_data: VisualizationData):
        self.visualization_data_dict[name] = visualization_data

        
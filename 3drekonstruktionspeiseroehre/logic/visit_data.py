from typing import List, Dict
from logic.visualization_data import VisualizationData

class VisitData:
    def __init__(self, name):
        """
        init VisitData
        """
        self.visualization_data_list: List[VisualizationData] = []
        self.name = name

    def number_of_visualizations(self) -> int:
        return len(self.visualization_data_list)

    def add_visualization(self, visualization_data: VisualizationData) -> None:
        self.visualization_data_list.append(visualization_data)

    def remove_visualization(self, index) -> None:
        del self.visualization_data_list[index]

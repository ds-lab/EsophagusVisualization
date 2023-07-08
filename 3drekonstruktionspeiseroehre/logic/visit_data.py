from typing import List

from logic.visualization_data import VisualizationData


class VisitData:
    def __init__(self, name):
        """
        Initializes the VisitData object.

        Args:
            name (str): The name of the visit.
        """
        self.visualization_data_list: List[VisualizationData] = []
        self.name = name

    def number_of_visualizations(self) -> int:
        """
        Returns the number of visualizations in the VisitData.

        Returns:
            int: The number of visualizations.
        """
        return len(self.visualization_data_list)

    def add_visualization(self, visualization_data: VisualizationData) -> None:
        """
        Adds a visualization to the VisitData.

        Args:
            visualization_data (VisualizationData): The VisualizationData object to be added.
        """
        self.visualization_data_list.append(visualization_data)

    def remove_visualization(self, index) -> None:
        """
        Removes a visualization from the VisitData.

        Args:
            index (int): The index of the visualization to be removed.
        """
        if 0 <= index < len(self.visualization_data_list):
            del self.visualization_data_list[index]

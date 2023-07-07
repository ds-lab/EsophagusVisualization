from typing import Dict

from logic.visit_data import VisitData


class PatientData:
    def __init__(self):
        """
        Initializes the PatientData object.
        """
        self.visit_data_dict: Dict[str, VisitData] = {}

    def number_of_visits(self) -> int:
        """
        Returns the number of visits in the PatientData.

        Returns:
            int: The number of visits.
        """
        return len(self.visit_data_dict)

    def add_visit(self, name: str, visit_data: VisitData) -> None:
        """
        Adds a visit to the PatientData.

        Args:
            name (str): The name of the visit.
            visit_data (VisitData): The VisitData object to be added.
        """
        self.visit_data_dict[name] = visit_data

    def remove_visit(self, name) -> None:
        """
        Removes a visit from the PatientData.

        Args:
            name: The name of the visit to be removed.
        """
        del self.visit_data_dict[name]

        
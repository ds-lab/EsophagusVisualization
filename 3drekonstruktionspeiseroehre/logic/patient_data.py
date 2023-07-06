from typing import List, Dict
from logic.visit_data import VisitData

class PatientData:
    def __init__(self):
        """
        init PatientData
        """
        self.visit_data_dict: Dict[str, VisitData] = {}

    def number_of_visits(self) -> int:
        return len(self.visit_data_dict)

    def add_visit(self, name: str, visit_data: VisitData) -> None:
        self.visit_data_dict[name] = visit_data

    def remove_visit(self, name) -> None:
        del self.visit_data_dict[name]

        
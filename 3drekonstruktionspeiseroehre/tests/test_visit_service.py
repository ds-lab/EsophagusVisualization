import unittest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete, insert
from logic.database import engine_local, Base
from logic.data_declarative_models import Patient, Visit
from logic.services import patient_service, visit_service

Base.metadata.create_all(engine_local)

Session = sessionmaker(bind=engine_local)

patient_1 = {"patient_id": "p_1_test",
             "ancestry": "test_anchestry",
             "birth_year": 1993,
             "previous_therapies": False}

patient_2 = {"patient_id": "p_2_test",
             "ancestry": "test_anchestry",
             "birth_year": 1991,
             "previous_therapies": True}
visit_1 = {
            "visit_id": 3,
            "patient_id": "p_1_test",
            "measure": "test_measure",
            "center": "test_center",
            "age_at_visit": 40
        }


class TestVisitService(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.session.execute(delete(Visit))
        self.session.execute(delete(Patient))
        self.session.execute(insert(Patient).values(**patient_1))
        self.session.execute(insert(Patient).values(**patient_2))
        self.session.execute(insert(Visit).values(**visit_1))
        self.session.commit()

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_create_visit(self):
        visit_1 = {
            "visit_id": 1,
            "patient_id": "p_1_test",
            "measure": "test_measure",
            "center": "test_center",
            "age_at_visit": 40
        }
        visit_2 = {
            "visit_id": 2,
            "patient_id": "p_23_test",
            "measure": "test_measure",
            "center": "test_center",
            "age_at_visit": 40
        }
        
        result_1 = visit_service.create_visit(visit_1, self.session)
        assert result_1 == 1
        with self.assertRaises(Exception):
            visit_service.create_visit(visit_2, self.session)

    def test_update_visit(self):
        update_data = {"measure": "3434e"}
        result_1 = visit_service.update_visit(
            visit_1["visit_id"], update_data, self.session)

        result_2 = visit_service.update_visit(
            22, update_data, self.session)
        
        assert result_1 == 1
        assert result_2 == 0

    def test_delete_visit(self):
        result_1 = visit_service.delete_visit(
            visit_1["visit_id"], self.session)
        result_2 = visit_service.delete_visit(
            "unexistent_id", self.session)

        assert result_1 == 1
        assert result_2 == 0

    def test_get_visit(self):
        result_1 = visit_service.get_visit(
            visit_1["visit_id"], self.session)
        assert result_1 != None

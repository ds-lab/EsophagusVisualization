import unittest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from logic.database import engine_local, Base
from logic.data_declarative_models import Patient
from logic.services import patient_service

Base.metadata.create_all(engine_local)

Session = sessionmaker(bind=engine_local)

patient_1 = {"patient_id": "123test",
             "ancestry": "test_anchestry",
             "birth_year": 1993,
             "previous_therapies": False}


class TestPatientService(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.session.execute(delete(Patient))
        self.session.commit()

    def tearDown(self):
        self.session.rollback()

    def test_create_user(self):
        data = patient_1
        created_patient = patient_service.create_patient(data, self.session)
        assert created_patient == 1

    def test_update_patient(self):
        patient_id = "123test"
        update_data = {"birth_year": 1992}
        patient_service.create_patient(patient_1, self.session)

        result_1 = patient_service.update_patient(
            patient_id, update_data, self.session)

        result_2 = patient_service.update_patient(
            "not_existent_id", update_data, self.session)
        
        result_3 = patient_service.update_patient(
            patient_id, {"birth_year": "1991"}, self.session)
        
        assert result_1 == 1
        assert result_2 == 0
        assert result_3 == 1
    
    def test_delete_patiert(self):
        patient_service.create_patient(patient_1, self.session)

        result_1 = patient_service.delete_patient(patient_1["patient_id"], self.session)
        result_2 = patient_service.delete_patient("unexistent_id", self.session)

        assert result_1 == 1
        assert result_2 == 0
    
    def test_get_patient(self):
        patient_service.create_patient(patient_1, self.session)
        result_1 = patient_service.get_patient(patient_1["patient_id"], self.session)
        assert result_1 != None

import unittest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from logic.database import engine_local, Base
from logic.data_declarative_models import Patient
from logic.services.patient_service import PatientService

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
        self.patient_service = PatientService(self.session)

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_create_patient(self):
        data = patient_1
        created_patient = self.patient_service.create_patient(data)
        assert created_patient == 1

    def test_update_patient(self):
        patient_id = "123test"
        update_data = {"birth_year": 1992}
        self.patient_service.create_patient(patient_1)

        result_1 = self.patient_service.update_patient(
            patient_id, update_data)

        result_2 = self.patient_service.update_patient(
            "not_existent_id", update_data)
        
        result_3 = self.patient_service.update_patient(
            patient_id, {"birth_year": "1991"})
        
        assert result_1 == 1
        assert result_2 == 0
        assert result_3 == 1
    
    def test_delete_patiert(self):
        self.patient_service.create_patient(patient_1)

        result_1 = self.patient_service.delete_patient(patient_1["patient_id"])
        result_2 = self.patient_service.delete_patient("unexistent_id")

        assert result_1 == 1
        assert result_2 == 0
    
    def test_get_patient(self):
        self.patient_service.create_patient(patient_1)
        result_1 = self.patient_service.get_patient(patient_1["patient_id"])
        assert result_1 != None

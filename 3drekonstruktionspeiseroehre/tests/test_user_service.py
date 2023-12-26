import unittest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete
from logic.database import engine_local, Base
from logic.data_declarative_models import Patient
from logic.services import patient_service

Base.metadata.create_all(engine_local)

Session = sessionmaker(bind=engine_local)

class TestPatientService(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.session.execute(delete(Patient))
        self.session.commit()
    
    def tearDown(self):
        self.session.rollback()
    
    def test_create_user(self):
        data = {"patient_id": "123test",
                     "ancestry": "test_anchestry",
                     "birth_year": 1993,
                     "previous_therapies": False}
        created_patient = patient_service.create_patient(data, self.session)
        assert created_patient == 1
        
    def test_update_user(self):
        data = {"patient_id": "123test",
                     "ancestry": "test_anchestry",
                     "birth_year": 1993,
                     "previous_therapies": False}
        created_patient = patient_service.create_patient(data, self.session)
        assert created_patient == 1
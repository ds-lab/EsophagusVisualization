from logic.database import database
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService
from logic.services.eckardtscore_service import EckardtscoreService
from logic.services.manometry_service import ManometryService, ManometryFileService
from logic.services.previous_therapy_service import PreviousTherapyService
from logic.services.endoscopy_service import EndoscopyFileService
from logic.services.endoflip_service import EndoflipFileService
from logic.services.barium_swallow_service import BariumSwallowFileService


class CheckDataExistence:

    def __init(self):
        self.db = database.get_db()
        self.patient_service = PatientService(self.db)
        self.previous_therapy_service = PreviousTherapyService(self.db)
        self.visit_service = VisitService(self.db)
        self.eckardtscore_service = EckardtscoreService(self.db)
        self.manometry_service = ManometryService(self.db)
        self.manometry_file_service = ManometryFileService(self.db)
        self.barium_swallow_file_service = BariumSwallowFileService(self.db)
        self.endoscopy_file_service = EndoscopyFileService(self.db)
        self.endoflip_file_service = EndoflipFileService(self.db)

    def patient_exists(self):
        patient = self.patient_service.get_patient(
            self.ui.patient_id_field.text())
        if patient:
            return True
        return False


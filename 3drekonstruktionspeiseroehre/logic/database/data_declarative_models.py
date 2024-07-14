from sqlalchemy import Boolean, ForeignKey, Integer, PickleType, String, Float, inspect, LargeBinary
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"
    patient_id = mapped_column(String(30), primary_key=True)
    gender = mapped_column(String(6))
    ethnicity = mapped_column(String(50))
    birth_year = mapped_column(Integer)
    year_first_diagnosis = mapped_column(Integer)
    year_first_symptoms = mapped_column(Integer)
    center = mapped_column(String(20))

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class PreviousTherapy(Base):
    __tablename__ = "previous_therapies"
    previous_therapy_id = mapped_column(Integer, primary_key=True)
    patient_id = mapped_column(ForeignKey(
        "patients.patient_id", ondelete="CASCADE"), nullable=False)
    therapy = mapped_column(String, nullable=False)
    year = mapped_column(Integer, nullable=True)
    center = mapped_column(String(20), nullable=True)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Visit(Base):
    __tablename__ = "visits"
    visit_id = mapped_column(Integer, primary_key=True)
    patient_id = mapped_column(ForeignKey(
        "patients.patient_id", ondelete="CASCADE"), nullable=False)
    year_of_visit = mapped_column(Integer, nullable=False)
    visit_type = mapped_column(String(50), nullable=False)
    therapy_type = mapped_column(String(50), nullable=True)
    months_after_therapy = mapped_column(Integer, nullable=True)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class EckardtScore(Base):
    __tablename__ = "eckardt_scores"
    eckardt_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    dysphagia = mapped_column(Integer)
    retrosternal_pain = mapped_column(Integer)
    regurgitation = mapped_column(Integer)
    weightloss = mapped_column(Integer)
    total_score = mapped_column(Integer, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Gerd(Base):
    __tablename__ = "gerd_scores"
    gerd_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    grade = mapped_column(String(20))
    heart_burn = mapped_column(Boolean)
    ppi_use = mapped_column(Boolean)
    acid_exposure_time = mapped_column(Float)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Medication(Base):
    __tablename__ = "medications"
    medication_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    medication_use = mapped_column(String)
    medication_name = mapped_column(String)
    medication_dose = mapped_column(Float)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class BotoxInjection(Base):
    __tablename__ = "botox_injections"
    botox_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    botox_units = mapped_column(Integer)
    botox_height = mapped_column(Integer)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class PneumaticDilatation(Base):
    __tablename__ = "pneumatic_dilatations"
    pneumatic_dilatation_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    balloon_volume = mapped_column(String(5))
    quantity = mapped_column(Integer)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class LHM(Base):
    __tablename__ = "lhms"
    lhm_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    op_duration = mapped_column(Integer)
    length_myotomy = mapped_column(Float)
    fundoplicatio = mapped_column(Boolean)
    type_fundoplicatio = mapped_column(String(8))

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class POEM(Base):
    __tablename__ = "poems"
    poem_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    procedure_duration = mapped_column(Integer)
    height_mucosal_incision = mapped_column(Integer)
    length_mucosal_incision = mapped_column(Float)
    length_submuscosal_tunnel = mapped_column(Float)
    localization_myotomy = mapped_column(String(10))
    length_tubular_myotomy = mapped_column(Float)
    length_gastric_myotomy = mapped_column(Float)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Complications(Base):
    __tablename__ = "complications"
    complication_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    bleeding = mapped_column(String(10))
    perforation = mapped_column(String(10))
    capnoperitoneum = mapped_column(String(10))
    mucosal_tears = mapped_column(String(10))
    pneumothorax = mapped_column(String(10))
    pneumomediastinum = mapped_column(String(10))
    other_complication = mapped_column(String(10))

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Manometry(Base):
    __tablename__ = "manometries"
    manometry_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    catheter_type = mapped_column(String(20))
    patient_position = mapped_column(String(20))
    resting_pressure = mapped_column(Integer)
    ipr4 = mapped_column(Integer)
    dci = mapped_column(Integer)
    dl = mapped_column(Integer)
    ues_upper_boundary = mapped_column(Integer)
    ues_lower_boundary = mapped_column(Integer)
    les_upper_boundary = mapped_column(Integer)
    les_lower_boundary = mapped_column(Integer)
    les_length = mapped_column(Integer)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class ManometryFile(Base):
    __tablename__ = "manometry_files"
    manometry_file_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    file = mapped_column(PickleType, nullable=False)
    pressure_matrix = mapped_column(PickleType, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class BariumSwallow(Base):
    __tablename__ = "barium_swallows"
    tbe_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    type_contrast_medium = mapped_column(String(50))
    amount_contrast_medium = mapped_column(Integer)
    height_contrast_medium_1min = mapped_column(Integer)
    height_contrast_medium_2min = mapped_column(Integer)
    height_contrast_medium_5min = mapped_column(Integer)
    width_contrast_medium_1min = mapped_column(Integer)
    width_contrast_medium_2min = mapped_column(Integer)
    width_contrast_medium_5min = mapped_column(Integer)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class BariumSwallowFile(Base):
    __tablename__ = "barium_swallow_files"
    tbe_file_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    minute_of_picture = mapped_column(Integer)
    filename = mapped_column(String)
    file = mapped_column(PickleType)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Endoscopy(Base):
    __tablename__ = "endoscopies"
    egd_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    position_les = mapped_column(Integer)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class EndoscopyFile(Base):
    __tablename__ = "endoscopy_files"
    endoscopy_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    image_position = mapped_column(Integer, nullable=False)
    file = mapped_column(PickleType, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Endoflip(Base):
    __tablename__ = "endoflips"
    endoflip_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    csa_before = mapped_column(Float)
    di_before = mapped_column(Float)
    dmin_before = mapped_column(Float)
    ibp_before = mapped_column(Float)
    csa_during = mapped_column(Float)
    di_during = mapped_column(Float)
    dmin_during = mapped_column(Float)
    ibp_during = mapped_column(Float)
    csa_after = mapped_column(Float)
    di_after = mapped_column(Float)
    dmin_after = mapped_column(Float)
    ibp_after = mapped_column(Float)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class EndoflipFile(Base):
    __tablename__ = "endoflip_files"
    endoflip_file_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    timepoint = mapped_column(String(10))
    file = mapped_column(PickleType, nullable=True)
    screenshot = mapped_column(PickleType)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class EndoflipImage(Base):
    __tablename__ = "endoflip_images"
    endoflip_image_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    timepoint = mapped_column(String(10))
    file = mapped_column(PickleType, nullable=True)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class EndosonographyImage(Base):
    __tablename__ = "endosonography_images"
    endosonography_image_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_position = mapped_column(Integer, nullable=False)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    file = mapped_column(PickleType, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class EndosonographyVideo(Base):
    __tablename__ = "endosonography_videos"
    endosonography_video_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    video_oid = mapped_column(Integer, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Reconstruction(Base):
    __tablename__ = "reconstructions"
    reconstruction_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    reconstruction_file = mapped_column(PickleType, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


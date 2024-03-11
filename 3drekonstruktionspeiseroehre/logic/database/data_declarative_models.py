from sqlalchemy import Boolean, ForeignKey, Integer, PickleType, String, Enum, Date, Float, create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, mapped_column, sessionmaker


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

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
    
    def __str__(self) -> str:
        return f"[patient_id: {self.patient_id}, birth_year: {self.birth_year}]"
    
    def __repr__(self) -> str:
        return f"[patient_id: {self.patient_id}, birth_year: {self.birth_year}]"


class Visit(Base):
    __tablename__ = "visits"
    visit_id = mapped_column(Integer, primary_key=True)
    patient_id = mapped_column(ForeignKey(
        "patients.patient_id", ondelete="CASCADE"), nullable=False)
    year_of_visit = mapped_column(Integer, nullable=False)
    visit_type = mapped_column(String(50), nullable=False)
    therapy_type = mapped_column(String(50), nullable=False)
    year_first_symptoms = mapped_column(Integer, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Therapy(Base):
    __tablename__ = "therapies"
    therapy_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    therapy = mapped_column(String(30), nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Followup(Base):
    __tablename__ = "followups"
    folloup_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    followup = mapped_column(Integer, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class PreviousTherapy(Base):
    __tablename__ = "previous_therapies"
    previous_therapy_id = mapped_column(Integer, primary_key=True)
    patient_id = mapped_column(ForeignKey(
        "patients.patient_id", ondelete="CASCADE"), nullable=False)
    therapy = mapped_column(String, nullable=False)
    year = mapped_column(Integer, nullable=True)
    year_not_known = mapped_column(Boolean, nullable=True)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Metric(Base):
    __tablename__ = "metrics"
    metric_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    # Zeitpunkt des Breischluckbildes
    time = mapped_column(Integer, nullable=False)
    metric_tubular_mean = mapped_column(Float, nullable=False)
    metric_sphincter_mean = mapped_column(Float, nullable=False)
    metric_tubular_max = mapped_column(Float, nullable=False)
    metric_sphincter_max = mapped_column(Float, nullable=False)
    metric_tubular_min = mapped_column(Float, nullable=False)
    metric_sphincter_min = mapped_column(Float, nullable=False)
    pressure_tubular_max = mapped_column(Float, nullable=False)
    pressure_sphincter_max = mapped_column(Float, nullable=False)
    volume_tubular = mapped_column(Float, nullable=False)
    volume_sphincter = mapped_column(Float, nullable=False)
    esophagus_length_cm = mapped_column(Float, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class VisualizationData(Base):
    __tablename__ = "visualization_data_list"
    visualization_id = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id", ondelete="CASCADE"), nullable=False)
    visualization_data = mapped_column(PickleType, nullable=False)

    def toDict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


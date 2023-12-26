from sqlalchemy import Boolean, ForeignKey, Integer, PickleType, String, Enum, Date, Float, create_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"
    patient_id = mapped_column(String(30), primary_key=True)
    ancestry = mapped_column(String(15))
    birth_year = mapped_column(Integer)
    previous_therapies = mapped_column(Boolean)


class Visit(Base):
    __tablename__ = "visits"
    visit_id = mapped_column(Integer, primary_key=True)
    patient_id = mapped_column(ForeignKey(
        "patients.patient_id"), nullable=False)
    measure = mapped_column(String(11), nullable=False)
    center = mapped_column(String(20), nullable=False)
    age_at_visit = mapped_column(Integer, nullable=False)


class Therapy(Base):
    __tablename__ = "therapies"
    therapy_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id"), nullable=False)
    therapy = mapped_column(Enum, nullable=False)


class Followup(Base):
    __tablename__ = "followups"
    folloup_id = mapped_column(Integer, primary_key=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id"), nullable=False)
    followup = mapped_column(Integer, nullable=False)


class PreviousTherapy(Base):
    __tablename__ = "previous_therapies"
    previous_therapy_id = mapped_column(Integer, primary_key=True)
    patient_id = mapped_column(ForeignKey(
        "patients.patient_id"), nullable=False)
    therapy = mapped_column(Enum, nullable=False)
    times = mapped_column(Integer, nullable=True)
    last_date = mapped_column(Date, nullable=True)


class Metric(Base):
    __tablename__ = "metrics"
    metric_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id"), nullable=False)
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


class VisualizationData(Base):
    __tablename__ = "visualization_data_list"
    visualization_id = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    visit_id = mapped_column(ForeignKey("visits.visit_id"), nullable=False)
    visualization_data = mapped_column(PickleType, nullable=False)


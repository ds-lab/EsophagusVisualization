from sqlalchemy import MetaData, Table, Column, Integer, String, Enum, Date, ForeignKey, Boolean, Float, PickleType

metadata_obj = MetaData()


patients_table = Table(
    "patients",
    metadata_obj,
    Column("patient_id", String(30), primary_key=True),
    Column("ancestry", String(15)),
    Column("birth_year", Integer),
    Column("previous_therapies", Boolean)
)

visits_table = Table(
    "visits",
    metadata_obj,
    Column("visit_id", Integer, primary_key=True, autoincrement=True),
    Column("patient_id", ForeignKey("patients.patient_id"), nullable=False),
    Column("measure", String(11), nullable=False),
    Column("center", String(20), nullable=False),
    Column("age_at_visit", Integer, nullable=False)
)

therapy_table = Table(
    "therapies",
    metadata_obj,
    Column("therapy_id", Integer, primary_key=True),
    Column("visit_id", ForeignKey("visits.visit_id"), nullable=False),
    Column("therapy", Enum, nullable=False)
)

followup_table = Table(
    "followups",
    metadata_obj,
    Column("followup_id", Integer, primary_key=True),
    Column("visit_id", ForeignKey("visits.visit_id"), nullable=False),
    Column("followup", Integer, nullable=False)
)

previous_therapies_table = Table(
    "previous_therapies",
    metadata_obj,
    Column("previous_therapy_id", Integer, primary_key=True),
    Column("patient_id", ForeignKey("patients.patient_id"), nullable=False),
    Column("therapy", Enum, nullable=False),
    Column("times", Integer, nullable=True),
    Column("last_date", Date, nullable=True)  # Wann hat der Pat. die Therapie zuletzt bekommen (Datum)
)

metrics_table = Table(
    "metrics",
    metadata_obj,
    Column("metric_id", Integer, primary_key=True, autoincrement=True),
    Column("visit_id", ForeignKey("visits.visit_id"), nullable=False),
    Column("time", Integer, nullable=False),  # Zeitpunkt des Breischluckbildes
    Column("metric_tubular_mean", Float, nullable=False),
    Column("metric_sphincter_mean", Float, nullable=False),
    Column("metric_tubular_max", Float, nullable=False),
    Column("metric_sphincter_max", Float, nullable=False),
    Column("metric_tubular_min", Float, nullable=False),
    Column("metric_sphincter_min", Float, nullable=False),
    Column("pressure_tubular_max", Float, nullable=False),
    Column("pressure_sphincter_max", Float, nullable=False),
    Column("volume_tubular", Float, nullable=False),
    Column("volume_sphincter", Float, nullable=False),
    Column("esophagus_length_cm", Float, nullable=False),
)

visualization_table = Table(
    "visualization_data_list",
    metadata_obj,
    Column("visualization_id", Integer, primary_key=True, autoincrement=True),
    Column("visit_id", ForeignKey("visits.visit_id"), nullable=False),
    Column("visualization_data", PickleType, nullable=False)
)
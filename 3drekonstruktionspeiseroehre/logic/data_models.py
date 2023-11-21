from sqlalchemy import MetaData, Table, Column, Integer, String, Enum, Date, ForeignKey, Boolean, Float, PickleType

metadata_obj = MetaData()


patients_table = Table(
    "patients",
    metadata_obj,
    Column("patient_id", String(30), primary_key=True),
    Column("ancestry", Enum),   # Kann man in der GUI auch auf ein in Python definiertes Enum zugreifen? Sonst ginge hier auch String.
    Column("birth_year", Date),
    Column("previous_therapies", Boolean)
)

visits_table = Table(
    "visits",
    metadata_obj,
    Column("visit_id", Integer, primary_key=True),
    Column("patient_id", ForeignKey("patients.patient_id"), nullable=False),
    Column("time", Integer), # z.B. Integer -1 steht für vor Therapie, 0 steht für Therapie, alle andereren Werte stehen für die Monate nach Therapie
    # dies die -1 und 0 kann/sollte von uns automatisch eingetragen werden, je nachdem was in der GUI angeklickt wird
    # evtl. Jahre in Monate umrechnen
    Column("therapy", Enum, nullable=False),
    Column("center", String(20), nullable=False),
    Column("date", Date, nullable=False)  # brauchen das Datum um das Alter des Patienten zu verschiedenen Zeitpunkten berechnen zu können
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


CREATE TABLE patients (
    patient_id VARCHAR(30) PRIMARY KEY,
    gender VARCHAR(6),
    ethnicity VARCHAR(50),
    birth_year INT,
    year_first_diagnosis INT,
    year_first_symptoms INT
);

CREATE TABLE visits (
    visit_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(30) REFERENCES patients(patient_id) ON DELETE CASCADE NOT NULL,
    year_of_visit INTEGER NOT NULL,
    visit_type VARCHAR(50) NOT NULL,
    therapy_type VARCHAR(50) NOT NULL
);

CREATE TABLE therapies (
    therapy_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    therapy VARCHAR(30) NOT NULL
);

CREATE TABLE followups (
    followup_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    followup INT NOT NULL
);

CREATE TABLE previous_therapies (
    previous_therapy_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(30) REFERENCES patients(patient_id) ON DELETE CASCADE NOT NULL,
    therapy VARCHAR NOT NULL,
    year INT,
    year_not_known BOOLEAN
);

CREATE TABLE metrics (
    metric_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    time INT NOT NULL,
    metric_tubular_mean FLOAT NOT NULL,
    metric_sphincter_mean FLOAT NOT NULL,
    metric_tubular_max FLOAT NOT NULL,
    metric_sphincter_max FLOAT NOT NULL,
    metric_tubular_min FLOAT NOT NULL,
    metric_sphincter_min FLOAT NOT NULL,
    pressure_tubular_max FLOAT NOT NULL,
    pressure_sphincter_max FLOAT NOT NULL,
    volume_tubular FLOAT NOT NULL,
    volume_sphincter FLOAT NOT NULL,
    esophagus_length_cm FLOAT NOT NULL
);

CREATE TABLE visualization_data_list (
    visualization_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    visualization_data BYTEA NOT NULL
);

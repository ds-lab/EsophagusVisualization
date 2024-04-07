CREATE TABLE patients (
    patient_id VARCHAR(30) PRIMARY KEY,
    gender VARCHAR(6),
    ethnicity VARCHAR(50),
    birth_year INT,
    year_first_diagnosis INT,
    year_first_symptoms INT,
    center VARCHAR(20)
);

CREATE TABLE previous_therapies (
    previous_therapy_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(30) REFERENCES patients(patient_id) ON DELETE CASCADE NOT NULL,
    therapy VARCHAR NOT NULL,
    year INT,
    center VARCHAR(20)
);

CREATE TABLE visits (
    visit_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(30) REFERENCES patients(patient_id) ON DELETE CASCADE NOT NULL,
    year_of_visit INT NOT NULL,
    visit_type VARCHAR(50) NOT NULL,
    therapy_type VARCHAR(50),
    months_after_therapy INT NOT NULL
);

CREATE TABLE eckardt_scores (
    eckardt_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    dysphagia INT,
    retrosternal_pain INT,
    regurgitation INT,
    weightloss INT,
    total_score INT NOT NULL
);

CREATE TABLE gerd_scores (
    gerd_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    grade VARCHAR(20),
    heard_burn BOOLEAN,
    ppi_use BOOLEAN,
    acid_exposure_time FLOAT
);

CREATE TABLE medications (
    medication_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    use_antithrombotic_medication BOOLEAN,
    type_antithrombotic_medication VARCHAR,
    dose_antithrombotic_medication INT,
    use_anticoagulation BOOLEAN,
    type_anticoagulation VARCHAR,
    dose_anticoagulation INT
);

CREATE TABLE botox_injections (
    botox_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    botox_units INT,
    botox_height INT
);

CREATE TABLE pneumatic_dilitations (
    pneumatic_dilitation_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    ballon_volume VARCHAR(5),
    quantity INT
);

CREATE TABLE lhms (
    lhm_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    op_duration INT,
    length_myotomy FLOAT,
    fundoplicatio BOOLEAN,
    type_fundoplicatio VARCHAR(8)
);

CREATE TABLE poems (
    poem_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    procedure_duration INT,
    height_mucosal_incision INT,
    length_mucosal_incision FLOAT,
    length_submuscosal_tunnel FLOAT,
    localization_myotomy VARCHAR(10),
    length_tubular_myotomy FLOAT,
    length_gastric_myotomy FLOAT
);

CREATE TABLE complications (
    complication_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    no_complications BOOLEAN,
    bleeding VARCHAR(10),
    perforation VARCHAR(10),
    capnoperitoneum VARCHAR(10),
    mucosal_tears VARCHAR(10),
    pneumothorax VARCHAR(10),
    pneumomediastinum VARCHAR(10),
    other VARCHAR(10)
);

CREATE TABLE manometries (
    manometry_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    catheder_type VARCHAR(20),
    patient_position VARCHAR(20),
    resting_pressure INT,
    ipr4 INT,
    dci INT,
    dl INT,
    ues_upper_boundary INT,
    ues_lower_boundary INT,
    les_upper_boundary INT,
    les_lower_boundary INT,
    les_length INT
);

CREATE TABLE manometry_files (
    manometry_file_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    file BYTEA NOT NULL
);

CREATE TABLE barium_swallows (
    tbe_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    type_contrast_medium VARCHAR(50),
    amount_contrast_medium INT,
    height_contast_medium_1min INT,
    height_contast_medium_2min INT,
    height_contast_medium_5min INT,
    width_contast_medium_1min INT,
    width_contast_medium_2min INT,
    width_contast_medium_5min INT
);

CREATE TABLE barium_swallow_files (
    tbe_file_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    filename VARCHAR,
    file BYTEA NOT NULL
);

CREATE TABLE endoscopies (
    egd_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    position_les INT
);

CREATE TABLE endoscopy_files (
    endoscopy_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    image_position INT NOT NULL,
    filename VARCHAR NOT NULL,
    file BYTEA NOT NULL
);

CREATE TABLE endoflips (
    endoflip_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    csa FLOAT,
    dist FLOAT,
    dmin FLOAT,
    ibp FLOAT
);

CREATE TABLE endoflip_files (
    endoflip_file_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    file BYTEA,
    screenshot BYTEA
);

CREATE TABLE endosonographies (
    endosonography_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    esophageal_wall_thickness INT
);

CREATE TABLE endosonography_files (
    endosonography_file_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    file BYTEA NOT NULL
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

CREATE TABLE visualization_data_list (
    visualization_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    visualization_data BYTEA NOT NULL
);

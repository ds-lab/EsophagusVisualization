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
    months_after_therapy INT
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
    heart_burn BOOLEAN,
    ppi_use BOOLEAN,
    acid_exposure_time FLOAT
);

CREATE TABLE medications (
    medication_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    medication_use VARCHAR,
    medication_name VARCHAR,
    medication_dose FLOAT
);

CREATE TABLE botox_injections (
    botox_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    botox_units INT,
    botox_height INT
);

CREATE TABLE pneumatic_dilatations (
    pneumatic_dilatation_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    balloon_volume VARCHAR(5),
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
    bleeding VARCHAR(10),
    perforation VARCHAR(10),
    capnoperitoneum VARCHAR(10),
    mucosal_tears VARCHAR(10),
    pneumothorax VARCHAR(10),
    pneumomediastinum VARCHAR(10),
    other_complication VARCHAR(10)
);

CREATE TABLE manometries (
    manometry_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    catheter_type VARCHAR(20),
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
    file BYTEA NOT NULL,
    pressure_matrix BYTEA NOT NULL
);

CREATE TABLE barium_swallows (
    tbe_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    type_contrast_medium VARCHAR(50),
    amount_contrast_medium INT,
    height_contrast_medium_1min INT,
    height_contrast_medium_2min INT,
    height_contrast_medium_5min INT,
    width_contrast_medium_1min INT,
    width_contrast_medium_2min INT,
    width_contrast_medium_5min INT
);

CREATE TABLE barium_swallow_files (
    tbe_file_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    minute_of_picture INT,
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
    csa_before FLOAT,
    di_before FLOAT,
    dmin_before FLOAT,
    ibp_before FLOAT,
    csa_during FLOAT,
    di_during FLOAT,
    dmin_during FLOAT,
    ibp_during FLOAT,
    csa_after FLOAT,
    di_after FLOAT,
    dmin_after FLOAT,
    ibp_after FLOAT
);

CREATE TABLE endoflip_files (
    endoflip_file_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    timepoint VARCHAR(10),
    file BYTEA,
    screenshot BYTEA
);

CREATE TABLE endoflip_images (
    endoflip_image_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    timepoint VARCHAR(10),
    file BYTEA
);

CREATE TABLE endosonography_images (
    endosonography_image_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    image_position INT NOT NULL,
    file BYTEA NOT NULL
);

CREATE TABLE endosonography_videos (
    endosonography_video_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    video_oid OID NOT NULL
);

CREATE TABLE reconstructions (
    reconstruction_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id) ON DELETE CASCADE NOT NULL,
    reconstruction_file BYTEA NOT NULL
);

-- Trigger-Function for deleting Large Objects
CREATE OR REPLACE FUNCTION delete_large_object() RETURNS TRIGGER AS $$
BEGIN
    PERFORM lo_unlink(OLD.video_oid);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger for deleting Large Objects
CREATE TRIGGER trg_delete_large_object
AFTER DELETE ON endosonography_videos
FOR EACH ROW
EXECUTE FUNCTION delete_large_object();


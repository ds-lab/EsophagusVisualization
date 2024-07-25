# Esophagus Visualization and Data Management Software

This software is designed to support the diagnosis and treatment of achalasia by storing patient data and generating 3D visualizations of the esophagus. 
The software was developed for the University Hospital Augsburg, and integrates various diagnostic data to create comprehensive patient records and a reliable 3d reconstructions.

## Key Features

- **Patient and Visit Management**: Save and manage data about patients, their visits, and their therapies, including complications and outcomes.
- **Imaging Data Storage**: Store imaging data such as barium swallow images, endoscopy images, EndoFLIP images,  endosonography images, and endosonography videos, linked to patient records and visits.
- **Diagnostic File Handling**: Handle and store manometry files (.csv) and EndoFLIP files (.xlsx) from diagnostic instruments.
- **3D Esophagus Visualization**: Generate 3D reconstructions of the esophagus from barium swallow X-rays and optionally endoscopy images. These reconstructions can be saved and linked to patient records.
- **3D Visualization supports**:
  - **Pressure Mapping**: Create animated color mappings of manometry measurements on the 3D reconstruction.
  - **Distensibility Mapping**: Generate color mappings and tabular representations of EndoFLIP measurements on the 3D reconstruction.
  - **Multiple barium swallow images**: Switch between visualizations based on different barium swallow images with selection via radio button.
  - **Metrics**: Calculate metrics for the tubular region (volume x pressure) and the sphincter region (volume / pressure).
  - **Side-by-Side Comparison**: Display multiple 3d visualizations side-by-side for comparisons (e.g., pre/post-therapy, different patients).
- **Data Export**:
  - **3D Reconstructions**: Export metrics as .csv, the 3D reconstruction as .html for external display, and the reconstruction as .stl file for 3D printing.
  - **Database Exports**: Download data about patients, their visits, and their therapies for statistical analysis.

## Supported File Types

The software can handle and store the following file types:
- Manometry measurements (.csv from 'Laborie stationary measurement & analysis software' by Medical Measurement Systems B.V.)
- Frontal barium swallow X-ray images
- Endoscopy images of the esophagus (EGD)
- EndoFLIP files (.xlsx)
- Additionally, EndoFLIP images and endosonography images and videos can be uploaded and saved into the database (these files are not yet used for 3D visualization).

## Getting Started

### Setup Environment

1. **Create Environment**:
    ```sh
    conda create -n "esophagus-visualization" python=3.9.7 ipython
    conda activate esophagus-visualization
    ```

2. **Install Requirements**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Docker Setup**:  
- In the folder, where docker-compose.yml file is located run
    ```sh
    docker-compose up -d
    ```
- Access pgAdmin at `http://localhost:8080`
  - Username: `admin@admin.com`
  - Password: `123+qwe`
  - Server field: can be left empty

4. **Start the Application**:
    ```sh
    python ./3drekonstruktionspeiseroehre/main.py
    ```

## Creating an Executable

1. Adjust the path to the `dash_extensions` folder in the Conda environment in the `main.spec` file.
2. Run PyInstaller:
    ```sh
    pyinstaller --noconfirm --clean main.spec
    ```
    - Note: Adjust the path to main.spec if necessary.

The `dist` folder will contain the executable `ÖsophagusVisualisierung.exe` with Python and all necessary dependencies.

## Creating an Installer

1. Install InnoSetup.
2. Open and compile the `inno_setup_script.iss` file with InnoSetup.
    - Note: To edit, always open `inno_setup_script.iss` with InnoSetup to prevent file encoding issues.

## Configuration

Configuration values can be adjusted in the `config.py` file.

## Notes

- Developed with Python version 3.9.7.
- For dependency `cv2`, use `opencv-python-headless` instead of `opencv-python` to avoid conflicts with PyQt.
- Minimum version for `matplotlib` is 3.6.0rc2.
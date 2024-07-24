# Esophagus Visualization

This software generates a 3D visualization of the esophagus, which aids in the diagnosis and treatment of achalasia. The software was developed for use at the University Hospital Augsburg.

The software can handle the following data:
- A manometry measurement (exported as .csv from the 'Laborie stationary measurement & analysis software' by Medical Measurement Systems B.V.)
- A frontal barium swallow X-ray image
- Endoscopy images of the esophagus (EGD)
- EndoFLIP (exported as .xlsx)

Features:
- 3D reconstruction of the esophagus from a barium swallow X-ray and optionally endoscopy images
- Pressure: color mapping of manometry measurements on the 3D reconstruction as an animation
- Distensibility: color mapping and tabular representation of EndoFLIP measurements on the 3D reconstruction
- Easy integration and display of multiple barium swallow images (selection via radio buttons)
- Calculation of metrics for the tubular region (volume x pressure) and the sphincter region (volume / pressure)
- Side-by-side display of multiple esophagi (pre/post-therapy, different patients)
- Export of metrics as .csv
- Export of the reconstruction as .html for display outside the software
- Export of the reconstruction as .stl file for 3D printing

![Example: Visualization of two esophagi](https://github.com/Alici96/myrepo/blob/main/Demo1.png?raw=true)

## Setup

Create environment:

- conda create -n "esophagus-visualization" python=3.9.7 ipython

- conda activate esophagus-visualization

Install requirements:

- pip install -r requirements.txt

Docker-compose:

- run "docker-compose up -d" inside /3drekonstruktionspeiseroehre where docker-compose.yml file is located
- to access phpmyadmin open your browser and go to http://localhost:8080 username: admin@admin.com password: 123+qwe server field can be empty

Start with:

- python .\3drekonstruktionspeiseroehre\main.py

## Create Exe File

First, adjust the path to the 'dash_extensions' folder in the Conda environment in the 'main.spec' file.

Then:

- pyinstaller --noconfirm --clean main.spec  
(Note: Adjust the path to main.spec if necessary)

The new 'dist' folder now contains the executable 'ÖsophagusVisualisierung.exe' and Python with all necessary dependencies.

## Create Installer

After creating a package with PyInstaller, you can generate an installer from it using InnoSetup.

First, install InnoSetup, then open and compile the 'inno_setup_script.iss' file with it.  
(Note: To edit, open 'inno_setup_script.iss' with InnoSetup (not with PyCharm, for example), as the file encoding might change otherwise.)

## Configuration

Configuration values can be adjusted in the 'config.py' file.

## Notes

- created with Python version 3.9.7

- for dependency cv2: use opencv-python-headless instead of opencv-python to avoid conflicts with PyQt

- matplotlib minimum version 3.6.0rc2

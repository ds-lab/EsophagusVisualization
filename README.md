# Ösophagus-Visualisierung
Diese Software (Prototyp) generiert eine 3D-Visualisierung der Speiseröhre, welche zur Unterstützung der Diagnose von Achalasie dient. Als Ausgangsdaten werden hierfür die Daten einer Manometriemessung (exportiert aus der 'Laborie stationary measurement & analysis software' der Firma Medical Measurement Systems B.V.), ein frontales Breischluck-Röntgenbild und Endoskopieaufnahmen verwendet.


## Einrichtung
Environment erstellen:
- conda create -n "esophagus-visualization" python=3.9.7 ipython
- conda activate esophagus-visualization

Requirements installieren:
- pip install -r requirements.txt

Starten mit:
- python main.py

## Exe-Datei erstellen
Zuerst in der Datei 'main.spec' den Pfad zum Ordner 'dash_extensions' im Conda-Environment anpassen. 

Anschließend:

- pyinstaller --noconfirm main.spec

Der neue Ordner 'dist' beinhaltet nun die Exe-Datei 'ÖsophagusVisualisierung.exe' und Python mit allen nötigen Dependencies.

## Installer erstellen
Nachdem mit PyInstaller ein Gesamtpaket erstellt wurde, kann aus diesem mit InnoSetup ein Installer generiert werden.
Hierfür zuerst InnoSetup installieren und dann die Datei 'inno_setup_script.iss' damit öffnen und kompilieren.

## Konfiguration
In der Datei 'config.py' können Konfigurationswerte angepasst werden.

## Notizen
- erstellt mit Python-Version 3.9.7
- für dependency cv2: opencv-python-headless statt opencv-python, da sonst Konflikt mit PyQt
- matplotlib min. Version 3.6.0rc2

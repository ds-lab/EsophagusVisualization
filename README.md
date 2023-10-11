# Ösophagus-Visualisierung

Diese Software generiert eine 3D-Visualisierung der Speiseröhre, welche zur Unterstützung der Diagnose und Therapie von Achalasie dient. Entwickelt wurde die Software für den Einsatz am Universitätsklinikum Augsburg.

Hierbei kann die Software mit folgenden Daten umgehen: 
- einer Manometriemessung (exportiert als .csv aus der 'Laborie stationary measurement & analysis software' der Firma Medical Measurement Systems B.V.)
- ein frontales Breischluck-Röntgenbild
- Endoskopieaufnahmen des Ösophagus (ÖGD)
- EndoFLIP (exportiert als .xlsx)

Features:
- 3D Rekonstruktion des Ösophagus aus einem Breischluck-Röntgenbild und optional Endoskopie-Aufnahmen
- Druck: farbliches Mapping von Manometriemessungen auf die 3D-Rekonstruktion als Animation
- Dehnbarkeit: farbliches Mapping und tabellarische Darstellung von EndoFLIP-Messungen auf die 3D-Rekonstruktion 
- unkomplizierte Einbindung und Darstellung von mehreren Breischluck-Aufnahmen (Auswahl durch Radiobuttons)
- Berechnung der Metriken für den tubulären Bereich (Volumen x Druck) und den Sphinkter-Bereich (Volumen / Druck)
- Side-by-Side Darstellung von mehreren Speiseröhren (Prä/Post-Therapie, verschiedene Patienten)
- einfacher Import und Export von '.achalasie' Dateien, damit die Annotation der Daten pro Rekonstruktion nur einmalig geschehen muss 
- Export der Metriken als .csv 
- Export der Rekonstruktion als .html zur Darstellung außerhalb der Software
- Export der Rekonstruktion als .stl Datei zum 3D Druck
  
![Beispiel: Visualisierung zweier Speiseröhren](https://github.com/Alici96/myrepo/blob/main/Demo1.png?raw=true)


## Einrichtung

Environment erstellen:

- conda create -n "esophagus-visualization" python=3.9.7 ipython

- conda activate esophagus-visualization

  

Requirements installieren:

- pip install -r requirements.txt

  

Starten mit:

- python .\3drekonstruktionspeiseroehre\main.py

  

## Exe-Datei erstellen

Zuerst in der Datei 'main.spec' den Pfad zum Ordner 'dash_extensions' im Conda-Environment anpassen.

  

Anschließend:

  

- pyinstaller --noconfirm --clean main.spec

  

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

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog


class InfoWindow(QDialog):
    """Shows info text"""

    def __init__(self):
        """
        init InfoWindow
        """
        super().__init__()
        self.ui = uic.loadUi("./ui-files/info_window_design.ui", self)

    def show_file_selection_info(self):
        text = """In diesem Fenster werden die für die Generierung der 3D-Darstellung benötigten Dateien ausgewählt. 
        <br><br>Die Manometriedatei stammt dabei aus der 'Laborie stationary measurement & analysis software' der Firma 
        Medical Measurement Systems B.V. Sie kann dort nach der Auswahl des relevanten Messzeitraums über den 
        Menüpunkt 'Export'->'CSV' exportiert werden.<br><br>Das Röntgenbild sollte idealerweise einen möglichst 
        hohen Kontrast haben und beide Ösophagussphinkter beeinhalten.<br><br>
        Die Auswahl von Endoskopiebildern ist optional. Falls sie nicht ausgewählt werden, wird in der 3D-Darstellung 
        ein kreisförmiger Querschnitt verwendet. <br>Die Endoskopiebilder benötigen jeweils im Dateinamen eine 
        Positionsangabe z.B. 'name_10cm.png' (Format: Unterstrich + Ganzzahl + cm). <br>Die Zahl gibt hierbei die 
        Position dieser Aufnahme im Ösophagus ausgehend von einer in einem späteren Schritt einzutragenden 
        Position 0 an (von unten nach oben). <br>Bei den Endoskopiebildern ist außerdem darauf zu achten, dass diese 
        so angefertigt wurden, dass bezüglich der Drehung die linke Seite der Aufnahme der linken Seite auf dem 
        Röntgenbild entspricht (rechte Seite analog). 
        <br> Optional können Endoflip-Untersuchungsergebnisse hinzugefügt werden. Diese sollten im Format .xlsx 
        vorliegen und hierbei ein einzelnes Excel-Sheet beinhalten. <br>
        <br> Falls erwünscht, kann einer Rekonstruktion ein eindeutiger Name zugewiesen werden, welcher auch für den 
        Export verwendet wird.
        <br><br> Es ist ebenfalls möglich, ein oder mehrere zuvor exportierte Rekonstruktionen zu importieren.
        """
        self.ui.textEdit.setHtml(text)

    def show_xray_region_selection_info(self):
        text = """In diesem Fenster wird die Form des Ösophagus auf dem Röntgenbild als Polygon eingetragen. <br><br>Die 
        Software versucht dabei zunächst eine automatische Vorauswahl zu treffen. Diese muss anschließend vom Benutzer
        geprüft und korrigiert werden. <br>Bei kleinen Abweichungen können die einzelnen Punkte mit der Maus an die 
        richtige Stelle verschoben werden. Durch einen Rechtsklick kann ein Punkt entfernt werden. <br>Wenn die 
        automatische Auswahl stark abweicht, sollte die Form nach einem Klick auf 'Neue Auswahl starten' händisch 
        eingetragen werden. Durch einen Klick in die Graphik wird dabei jeweils ein neuer Punkt erstellt. <br>
        Bei einer händischen Einzeichnung ist zu beachten, dass die obere Schnittfläche des Ösophagus gerade einzuzeichnen ist. 
        Dabei dürfen keine scheife Formen eingezeichnet werden. <br>
        Abgeschlossen wird die Auswahl durch einen Klick auf den ersten Punkt."""
        self.ui.textEdit.setHtml(text)

    def show_position_selection_info(self):
        text = """In diesem Fenster werden für die Berechnung der 3D-Darstellung notwendige Positionen in das Röntenbild 
        eingetragen. In hellgrün wird der bereits eingezeichnete Breischluck-Umriss dargestellt. <br><br>Es sind dabei die Positionen von zwei beliebigen Sensoren der Manometriemessung 
        erforderlich. <br>Diese können aus der 'Laborie'-Software entnommen werden. <br>Für eine gute Präzision 
        sollten die Sensoren möglichst weit auseinander liegen, also etwa ein Sensor im Bereich des oberen Sphinkters 
        und einer im Bereich des unteren. Dabei ist zu beachten, dass keine lange Strecke ohne Sensoren abgedeckt werden sollte
        (besonders bei Einzeichnung des Sensors P1). 
        <br><br>Nach einem Klick auf die jeweilige Schaltfläche kann die Position in der Graphik per Mausklick eingetragen werden. 
        <br><br> Um eine möglichst genaue Rekonstruktion zu ermöglichen, muss außerdem der Übergangspunkt von Ösophagus 
        zu Magen (innerhalb des Ösophagus) eingezeichnet werden.
        <br><br>Für die Berechnung der Metriken wird die ungefähre Position des Übergangs zwischen tubulärem Abschnitt 
        und dem unteren Sphinkter, sowie die Länge des Sphinkters (ablesbar in der Laborie-Software) benötigt.
        <br><br>Wenn beim Start der Software auch Endoskopiebilder angegeben wurden, ist außerdem noch das Eintragen der 
        Position '0cm' (bezogen auf die Positionsangaben in den Dateinamen) in der Graphik nötig.
        <br><br> Gleichermaßen muss der Sensor P1 der Endoflip-Untersuchung eingegeben werden, wenn Endoflip-Daten übergeben wurden.
        """
        self.ui.textEdit.setHtml(text)

    def show_endoscopy_selection_info(self):
        text = """Analog zum Eintragen der Form des Ösophagus im Röntenbild werden in diesem Schritt die Querschnitte
        des Ösophagus in die Endoskopiebilder als Polygon eingetragen. <br><br>Die  Software versucht dabei wieder 
        zunächst eine automatische Vorauswahl zu treffen. <br>Diese muss anschließend vom Benutzer
        geprüft und korrigiert werden. <br>Bei kleinen Abweichungen können die einzelnen Punkte mit der Maus an die 
        richtige Stelle verschoben werden. Durch einen Rechtsklick kann ein Punkt entfernt werden. <br>Wenn die 
        automatische Auswahl stark abweicht, sollte die Form nach einem Klick auf 'Neue Auswahl starten' händisch 
        eingetragen werden. <br>Durch einen Klick in die Graphik wird dabei jeweils ein neuer Punkt erstellt. <br>
        Abgeschlossen wird die Auswahl durch einen Klick auf den ersten Punkt."""
        self.ui.textEdit.setHtml(text)

    def show_visualization_info(self):
        text = """Hier wird die generierte 3D-Darstellung angezeigt. <br><br>Die Darstellung kann mit der Maus 
        bewegt werden. <br>Standardmäßig wird sie durch Ziehen mit der Maus gedreht. <br>
        Durch gleichzeitiges Halten der Strg-Taste kann sie verschoben werden. <br>
        Mit dem Mausrad lässt sich die Größe ändern. <br><br> Anhand der Legende lässt sich die berechnete Größe
        des Ösophagus in Zentimetern ablesen. Weicht diese stark von der zu erwartenden Größe ab, deutet dies auf 
        falsch oder ungenau eingetragene Positionen der Sensoren hin.<br><br>
        Durch einen Klick auf 'Animation starten' lässt sich der zeitliche Verlauf der Druckwerte animiert 
        darstellen. <br>Über die Zeitleiste kann der Zeitpunkt außerdem manuell gewählt werden. <br><br>
        Darunter werden die berechneten Metriken für den tubulären Abschnitt (Volumen*Druck) und den unteren Sphinkter 
        (Volumen/Druck) im Zeitverlauf angezeigt.
        <br><br> Wurden Endoflip-Daten eingegeben, erscheint links von der 3D-Rekstruktion der Endoflip-Screenshot. 
        Hierbei werden von oben nach unten P16 bis P1 angezeigt. Unter 'Aggregationsform auswählen'
        kann die Aggregationsfunktion des Screenshots ausgewählt werden. <br> Außerdem kann unterhalb der Rekonstruktion 
        mit einem Schalter ausgewählt werden, welche Farben auf die Rekonstruktion projeziert werden.
        Bei der Projektion der Endoflip-Farben kann ausgewählt werden, ob ein Ballon-Volumen von 30 oder 40ml angezeigt 
        werden soll. Über 'Aggregationsform auswählen' kann die Aggregationsfunktion gewählt werden. 
        ACHTUNG: Die EndoFLIP-Datenaufbereitung wurde nicht auführlich getestet. Bitte immer mit der 
        Hersteller-Visualisierung gegenprüfen.
        <br><br> Werden mehrere Rekonstruktionen (Import multipler .achalasie Dateien oder über 'Weitere Rekonstruktionen 
        einfügen') angezeigt, so können diese durch das Gedrückthalten des linken Mauszeigers und dem 
        Ziehen an die gewünschte Stelle umsortiert werden.
        <br><br> Download: Die 3D Visualisierungen können über 'Download für Darstellung' als html Dateien exportiert werden. 
        Dies ermöglicht die Betrachtung der Rekonsturktionen im Browser und macht diese einbindbar in Powerpoint.
        Zudem ermöglicht der 'Download für Import' den Export von '.achalasie' Dateien. Dieser Export ermöglicht,
        dass die Rekonstruktionen nochmals bequem und unverändert in diesem Programm geöffnet werden können.
        Zusätzlich ermöglicht 'CSV Metriken Download' das Exportieren der Metriken.<br><br>
        Weiterhin können '.stl'-Dateien für den 3D-Druck heruntergeladen werden. Der Download dieser Dateien kann ein paar Minuten in Anspruch nehmen. <br><br>
        Nach erfolgreichem Download erhalten Sie bei allen Download-Formaten eine Bestätigung vom Programm. 
        Über 'Reset' kann die Eingabe zurückgesetzt werden und neue Dateien geladen werden.
        """
        self.ui.textEdit.setHtml(text)

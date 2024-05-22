from PyQt6 import uic
from PyQt6.QtWidgets import QDialog


class InfoWindow(QDialog):
    """Shows info text"""

    def __init__(self):
        """
        init InfoWindow
        """
        super().__init__()
        self.ui = uic.loadUi("./ui-files/info_window_design.ui", self)

    def show_file_selection_info(self):
        # ToDo Updaten mit Erklärung DB und entsprechenden Pfaden
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
        text = """In this window, the shape of the esophagus is traced on the X-ray image as a polygon. <br><br> 
        The software initially attempts an automatic preselection. This must then be reviewed and corrected by the user. <br> 
        For small deviations, individual points can be moved to the correct position with the mouse. A right-click can remove a point. <br> 
        If the automatic selection deviates significantly, the shape should be manually traced after clicking 'Start New Selection'. 
        Clicking in the graphic will create a new point each time. <br>
        When manually tracing, it should be noted that the upper cross-section of the esophagus must be traced straight. <br>
        The selection is completed by clicking on the first point."""
        self.ui.textEdit.setHtml(text)

    def show_position_selection_info(self):
        text = """In this window, positions necessary for the calculation of the 3D representation are entered into the X-ray image. 
        The outline of the barium swallow already drawn is shown in light green. <br><br> 
        The positions of any two sensors of the manometry measurement are required. <br> 
        These can be taken from the 'Laborie' software. <br> 
        For good precision, the sensors should be placed as far apart as possible, 
        with one sensor in the area of the upper sphincter and one in the area of the lower sphincter. 
        It should be noted that no long stretch should be left without sensors (especially when drawing sensor P1). <br><br> 
        After clicking on the respective button, the position in the graph can be entered by clicking with the mouse. <br><br> 
        To enable the most accurate reconstruction possible, the transition point from the esophagus to the stomach 
        (within the esophagus) must also be marked. <br><br> 
        For the calculation of the metrics, the approximate position of the transition between the tubular section and 
        the lower sphincter, as well as the length of the sphincter (readable in the Laborie software), are required. <br><br> 
        If endoscopy images were also provided at the start of the software, entering the position '0cm' (based on the position 
        indications in the file names) in the graph is also necessary. <br><br> 
        Similarly, if Endoflip data has been provided, sensor P1 of the Endoflip examination must be entered.
        """
        self.ui.textEdit.setHtml(text)

    def show_endoscopy_selection_info(self):
        text = """Analogous to outlining the shape of the esophagus in the X-ray image, in this step, 
        the cross-sections of the esophagus are traced onto the endoscopy images as a polygon. <br><br>
        The software attempts to make an automatic preselection first. <br>
        This preselection must then be reviewed and corrected by the user. <br>
        In case of minor deviations, individual points can be moved to the correct position using the mouse. A right-click removes a point. <br>
        If the automatic selection deviates significantly, the shape should be manually traced after clicking 'Start New Selection'. <br>
        Clicking on the graphic creates a new point each time. <br>The selection is completed by clicking on the first point."""
        self.ui.textEdit.setHtml(text)

    def show_visualization_info(self):
        text = """The generated 3D representation is displayed here. <br><br>The display can be done with the mouse 
        be moved. <br>By default, it is rotated by dragging with the mouse. <br>
        It can be moved by holding the Ctrl key at the same time.<br>
        Using the mouse wheel, the size can be changed. <br><br>
        The calculated size of the esophagus in centimeters can be read from the legend. 
        If this deviates significantly from the expected size, it indicates incorrectly or inaccurately entered sensor positions. <br><br>
        By clicking on 'Start Animation', the temporal evolution of pressure values can be animated. <br>
        The timeline also allows manual selection of the time point. <br><br>
        Below, the calculated metrics for the tubular section (Volume*Pressure) and the lower sphincter (Volume/Pressure) are displayed over time. <br><br>
        If EndoFLIP data is entered, the EndoFLIP screenshot appears to the left of the 3D reconstruction. 
        From top to bottom, P16 to P1 are displayed. Under 'Select Aggregation Form', the aggregation function of the screenshot can be chosen. <br>
        Furthermore, below the reconstruction, a switch can be used to select which colors are projected onto the reconstruction. 
        When projecting the EndoFLIP colors, it can be chosen whether a balloon volume of 30 or 40ml should be displayed. 
        'Select Aggregation Form' allows the aggregation function to be chosen. NOTE: EndoFLIP data processing has not been extensively tested. 
        Always cross-check with the manufacturer's visualization. <br><br>
        If multiple reconstructions (import of multiple .achalasia files or via 'Insert More Reconstructions') are displayed, 
        they can be rearranged by holding down the left mouse button and dragging them to the desired position. <br><br>
        Download: The 3D visualizations can be exported as HTML files via 'Download for Display'. 
        This allows the reconstructions to be viewed in the browser and makes them embeddable in PowerPoint. 
        In addition, 'Save reconstruction as file' allows the export of '.achalasia' files. 
        'Save reconstruction in DB' allows to save the reconstruction in the database.
        This export enables the reconstructions to be opened again conveniently and unchanged in this program. 
        Additionally, 'CSV Metrics Download' allows exporting the metrics. <br><br>
        Furthermore, '.stl' files can be downloaded for 3D printing. The download of these files may take a few minutes. 
        <br><br>After successful download, you will receive confirmation from the program for all download formats. 
        'Reset' can be used to reset the input and load new files.
        """
        self.ui.textEdit.setHtml(text)

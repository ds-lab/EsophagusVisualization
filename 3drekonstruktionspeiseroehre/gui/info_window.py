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

    def show_data_window_info(self):
        # ToDo Text noch schreiben
        text = """In this window, patients and visits can be created.<br>
    Most data are not mandatory.<br>
    Patients and visits can be selected by clicking on them in the patient or visit list to add further data.<br><br>
    To create a 3D reconstruction, at least the following data are required:<br>

    <ol>
        <li>A patient must be created or selected from the patient list.</li>
        <li>A visit must be selected or created for the selected patient.</li>
        <li>The following data must be entered for the selected visit:
            <ul>
                <li>Manometry file from the 'Laborie stationary measurement & analysis software' by Medical Measurement Systems B.V. in CSV format.</li>
                <li>One or more Barium Swallow images in JPG format.</li>
                <li>Additionally, endoscopy images can be optionally added to improve the reconstruction.</li>
                <li>Endoflip data are also optional but will be used for additional representation in the 3D reconstruction if entered.</li>
                <li>The remaining visit data serve to build a knowledge database to learn the correlation between different patient and treatment parameters and the outcome.</li>
            </ul>
        </li>
        <li>When a visit with the necessary data is selected, the reconstruction can be created by clicking "Create Visualization for selected Patient and selected Visit". If a reconstruction for this visit has already been saved, you may load this reconstruction or create a new one.</li>
    </ol>"""
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

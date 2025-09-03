from PyQt6 import uic
from utils.path_utils import resource_path
from PyQt6.QtWidgets import QDialog


class InfoWindow(QDialog):
    """Shows info text"""

    def __init__(self):
        """
        init InfoWindow
        """
        super().__init__()
        self.ui = uic.loadUi(resource_path('ui-files/info_window_design.ui'), self)

    def show_data_window_info(self):
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
    </ol>

    <h3>Downloads</h3>
    <ul>
        <li><strong>Download Data</strong>: Opens a dialog where you select which database tables to export (always includes <em>patients</em> and <em>visits</em>, plus any checked tables such as manometry, TBE, endoscopy, therapies, etc.).</li>
        <li><strong>Mass Download VTKHDF for ML/3d-Printing</strong>: Exports <em>all 3D reconstructions saved in the database</em> as <code>.vtkhdf</code> files into a chosen directory.<br style="margin:0; line-height:100%"/>
            Before export you can choose the pressure data mode:
            <ul style="margin:0; padding-left:18px;">
                <li><em>No vertex pressure</em> (geometry + metadata only),</li>
                <li><em>Per‑slice HRM pressure</em> (compact), or</li>
                <li><em>All per‑vertex HRM pressure</em> (complete).</li>
            </ul>
            Every file always includes the 3D geometry and rich metadata suitable for ML pipelines.
        </li>
    </ul>
    """
        self.ui.textEdit.setHtml(text)

    def show_xray_region_selection_info(self):
        text = """In this window, the shape of the esophagus is traced on the X-ray image as a polygon. <br><br> 
        The software initially attempts an automatic preselection. This must then be reviewed and corrected by the user. <br> 
        For small deviations, individual points can be moved to the correct position with the mouse. A right-click can remove a point. The last point can be deleted with the 'Delete last point' button. <br> 
        If the automatic selection deviates significantly, the shape should be manually traced after clicking 'Start New Selection'. 
        Clicking in the graphic will create a new point each time. <br>
        When manually tracing, it should be noted that the upper cross-section of the esophagus must be traced straight. <br>
        The selection is completed by clicking on the first point.
        If you want to save the shape of the oesophagus, spine and barium as masks, you have to click the corresponding checkboxes. <br>
        Draw each polygon, you want to save,  in the order of the checked boxes. The shapes can overlap. <br>
        If you are finished with one shape, you can draw the next with clicking the 'Next selection' button. <br>
        Continuing with 'Apply selection and proceed' will save all masks and original image to a directory named DataAchalasia in C:\ <br> 
        """
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
        Clicking on the graphic creates a new point each time. <br>The selection is completed by clicking on the first point.<br>
        To safe the cross-section mask and the original image in C:\DataAchalasia check the checkbox"""
        self.ui.textEdit.setHtml(text)

    def show_sensor_path_info(self):
        text = """This Window shows the calculated/assumed path way of the katheter (sensor_path). <br><br>
        LEGEND:<br>
        The RED path shows the assumed katheter (shortest path) through the esophagus. <br>
        Underneath the red path there is a BLUE path that shows the original calculated sensor path to compare the eventually adapted (red) path and the old (blue) path.<br><br>
        EMPLOYMENT:<br>
        It's MOVABLE points can be adapted an will be taken as the new katheter path. <br>
        With a RIGHT CLICK a point on the line can be deleted if necessary. <br><br>
        EXPLANATION:<br>
        The sensor path is used for three tasks: 1) Determine the centimeter to pixel ratio, 2) calculate the center path and 3) map the pressure as surface color. <br>
        1) <br>
        First the user given (blue and green point in the window before) sensor points are mapped on this calculated katheter path
        and calculating the distance between them in pixel.<br>
        Since the distance between these sensor points is also known in cm from the katheter now this distance in pixel 
        is also available in cm.<br>
        => CM to PX ratio
        2) and 3)<br>
        The exact process is described in related papers.<br>
        The calculated center path is shown and adaptable in the next window.<br><br>
        !!! ATTENTION !!! <br>
        The red path has the problem that the highest and lowest point have a connection line between them in the visualization. <br>
        This line obviously doesn't exist in reality and won't be included in the calculation."""
        self.ui.textEdit.setHtml(text)

    def show_sensor_center_path_info(self):
        text = """This Window shows the calculated central path way trough the esophagus. <br><br>
        LEGEND: <br>
        The RED path shows the calculated central path through the esophagus. <br>
        Underneath the red path there is a BLUE path that shows the original calculated center path to compare the eventually adapted (red) path and the old (blue) path. <br>
        The ORANGE path shows the used katheter path (sensor_path) on wich the calculation of the center path is based. <br><br>
        EMPLOYMENT:<br>
        It's MOVABLE points can be adapted an will be taken as the new central path. <br>
        With a RIGHT CLICK a point on the line can be deleted if necessary. <br>
        Use the adaptability if the path is not central. <br><br>
        USAGE:<br>
        The center path is used to 1) construct the final reconstruction shape and 2) calculate the exact length of the esophagus. <br>
        1) <br>
        Since the center path displays the central path through the esophagus this is used to base the reconstruction around it.<br>
        2) <br>
        Since the sensor path is the shortest path it doesn't estimate the length of the esophagus best. <br>
        But the center path gives a better estimation of the length.<br><br>
        !!! ATTENTION !!! <br>
        Should the path require mayor changes to be corrected, be aware of possible form errors in the final visualization. <br><br>
        !!! ATTENTION !!! <br>
        The red path has the problem that the highest and lowest point have a connection line between them in the visualization. <br>
        This line obviously doesn't exist in reality and won't be included in the calculation."""
        self.ui.textEdit.setHtml(text)

    def show_visualization_info(self):
        text = """    <h2>This window shows the 3D reconstructions you created.</h2>

    <h3>View and Adjust the Visualization</h3>
    <ul>
        <li><strong>Rotate</strong>: Click and drag the visualization with the mouse to rotate it.</li>
        <li><strong>Move</strong>: Hold the <strong>Ctrl</strong> key while dragging to move the visualization.</li>
        <li><strong>Resize</strong>: Use the mouse wheel to zoom in or out.</li>
    </ul>

    <h3>Animation</h3>
    <ul>
        <li><strong>Start Animation</strong>: Clicking this button animates the temporal evolution of the pressure values over time.</li>
        <li><strong>Timeline</strong>: You can manually select a specific time point using the timeline.</li>
    </ul>

    <h3>View Indices</h3>
    <ul>
        <li>The size of the esophagus (in centimeters) is displayed in the legend. If this deviates significantly from the expected size, it may indicate that sensor positions were entered incorrectly or inaccurately.</li>
        <li>The calculated metrics for the tubular esophagus section (Volume * Pressure) and the lower esophageal sphincter (Volume / Pressure) are shown over time.</li>
    </ul>

    <h3>EndoFLIP Data</h3>
    <ul>
        <li>If EndoFLIP data has been entered, an <strong>EndoFLIP screenshot</strong> will appear to the left of the 3D reconstruction, showing values from <strong>P16 to P1</strong>.</li>
        <li><strong>Select Aggregation Form</strong>: You can choose how the data is aggregated in the screenshot.</li>
        <li>A switch below the reconstruction allows you to choose which <strong>colors</strong> are projected onto the reconstruction.</li>
        <li>You can also select whether to display <strong>30ml or 40ml balloon volumes</strong> from EndoFLIP.</li>
    </ul>
    <p class="note">Note: EndoFLIP data processing has not been extensively tested. Always verify the results with the manufacturer’s visualization.</p>

    <h3>Compare and Manage Multiple Reconstructions</h3>
    <ul>
        <li><strong>Add Reconstruction(s)</strong>: Opens the main data window so you can pick additional data for the same patient/visit or another visit. The new reconstruction(s) will be added alongside the existing ones in this view.</li>
        <li><strong>Rearrange</strong>: Drag a visualization by its header to change the order.</li>
        <li><strong>Trash icon</strong>: Removes the selected reconstruction tile from this view (does not delete anything in the database).</li>
    </ul>

    <h3>Download and Save</h3>
    <ul>
        <li><strong>Download for Display</strong>: Exports the <em>currently shown</em> reconstruction(s) as HTML file(s) for viewing in a browser or embedding in slides.</li>
        <li><strong>CSV Metrics Download</strong>: Exports time‑dependent and overall metrics to CSV.</li>
        <li><strong>Download VTKHDF for ML/3d‑Printing</strong>: Exports the reconstruction(s) as <code>.vtkhdf</code> including geometry, metadata and optional HRM pressure attributes, suitable for ML pipelines and 3D printing tools that support VTKHDF.</li>
        <li><strong>Save Reconstruction in DB</strong>: Persists the current reconstruction(s) to the database. If a reconstruction for the visit already exists, you will be asked whether it should be updated.</li>
    </ul>
    <p>Once the download is complete, the program will provide confirmation for each download format.</p>

    <h3>Adjust Reconstructions</h3>
    <p>Use the menu entry <strong>"Adjust current Reconstruction(s)"</strong> to reopen the HRM (DCI) step and subsequently the X‑ray segmentation with the previously saved settings preloaded. This enables quick refinements without redoing the entire workflow. The current visualization window remains open.</p>

    <h3>Reset the Visualization Window</h3>
    <p>Use the <strong>Reset</strong> button to clear the input fields and load new files, allowing you to create a new visualization.</p>
        """
        self.ui.textEdit.setHtml(text)

    def show_dci_selection_info(self):
        text = """<h3>In this window, the area of interest for the calculation of the Esophageal Pressure Index (EPI) is selected.</h3> <br>
        <p> The main component of this window is the visualization of the esophageal pressure over time. In this plot, the area of interest for the EPI is selected (red rectangle) as well as the position of the lower end of the UES and the upper and lower end of the LES (red lines with respective label). The position of the UES and LES can be adjusted by dragging the respective lines. The area of interest for the EPI can be adjusted by dragging the red rectangle. <br>
        <p> On the right hand of the plot, the sensor positions are displayed. The calculated sensor positions can be adjusted in the right column of the window. The right column also contains other parameters of interest such as the height of the tubular esophagus, the length of the LES, and the EPI. Furthermore, it can be selected whether the threshold for the EPI calculation should be 20 mmHg (standard value) or 0 mmHg (for patients without peristalsis). It is also possible to decouple the EPI selector from the lower UES and upper LES positions. <br>
        <p> To continue with the next step, simply click "Apply selection and proceed". <br>
        """
        self.ui.textEdit.setHtml(text)

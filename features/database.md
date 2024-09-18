# Database Features

## Patients Tab

### Managing Patients
- **Adding Patients**:
  - Patients are added via an input form with basic validation checks.
  - Missing optional fields trigger a notification.
  - Missing mandatory fields must be corrected before upload in the database.
- **Patient List**:
  - A list of all patients (along with all their attributes) is displayed.
  - Patients can be selected by clicking on their ID.
  - Patients can be sorted and filtered by any attribute.
- **Searching Patients**:
  - A search function with autocomplete (by ID) is available.
- **Selecting a Patient**:
  - Patients can be selected by clicking on their ID in the Patients List.
  - Attributes of the selected patient will be displayed in the GUI (Patients Tab, Visits Tab and Diagnostics & Therapy Tab) for reference.
  - When a patient is selected the Visits Tab is unlocked for data entry.
  - Visits of the selected patient are loaded in the Visits Tab.
- **Updating Patients**:
  - Patient data can be updated by entering new data for the same ID.
  - A warning appears to prevent accidental changes.
- **Deleting Patients**:
  - Selected patients can be deleted, along with all associated data (e.g., visits, therapies).
  - A warning appears before deletions to prevent accidental losses.
  - When deleting a patient, all displayed data of that patient in the Patients Tab, the Visits Tab and the Diagnostics & Therapy Tab are removed from view.
  - Additionally, all displayed data of a potentially selected visit of that patient are also removed from view (see "Deleting Visits").

### Managing Previous Therapies
- **Adding Previous Therapies**:
  - Only available when a patient is selected; otherwise, the field remains inactive.
  - Previous Therapies are added via an input form with basic validation checks.
  - Missing optional fields trigger a notification.
  - Missing mandatory fields must be corrected before upload in the database.
- **Managing Existing Previous Therapies**:
  - Previously added therapies can be selected, viewed, or deleted.
  - Warnings appear when deleting a previous therapy to prevent accidental deletion.

---

## Visits Tab

### Managing Visits
- **Adding Visits**:
  - Visits can only be created when a patient is selected. Without a selected patient, the field remains inactive.
  - Visits are added via an input form with basic validation checks.
  - Missing optional fields trigger a notification.
  - Missing mandatory fields must be corrected before upload in the database.
- **Visit List**:
  - A list of all visits of the selected patients (along with all attributes of the visit) is displayed.
  - Visits can be selected by clicking on their ID.
- **Selecting a Visit**:
  - Attributes of the selected visit will be displayed in the GUI (Visits Tab and Diagnostics & Therapy Tab) for reference.
  - The fields **Eckardt Score**, **Gerd Score**, and **Medication** in the Visits Tab are unlocked for data entry.
  - Saved attributes of the Eckardt Score, Gerd Score and Medication are displayed in the Visits Tab for reference.
  - The Diagnostics & Therapy Tab is unlocked for data entry.
  - All Diagnostics & Therapy data that are associated with the current visit are displayed in the Diagnostics & Therapy Tab for reference:
    - Manometry data are displayed in the manometry section
    - TBE data and TBE images are displayed in the TBE section
    - EGD data and EGD images are displayed in the EGD section
    - EndoFlip data and EndoFlip images are displayed in the EndoFlip section
    - Endosonography images are displayed in the Endosonography section
    - If the Visit Type is "Therapy", Therapy and complication data are displayed (depending on the type of therapy) in the Therapy section.
- **Deleting Visits**:
  - Selected visits can be deleted, along with all associated data, though **the patient** remains.
  - Warnings appear before deleting a visit to prevent accidental loss.
  - When deleting a visit, displayed data of that visit in the Visits Tab and Diagnostics & Therapy Tab (see "Selecting a Visit") are removed from view.


### Eckardt Score
- **Data Entry**:
  - Can only be created when a visit is selected.
  - Validation ensures individual scores must match the total score.
  - Either the total score or individual scores must be filled in.
- **Reviewing Data**:
  - The stored Eckardt Score for the selected visit is displayed for reference.
- **Updating and Deleting**:
  - The Eckardt Score can be updated or deleted.
  - A warning appears before any change to prevent accidental data loss.


### Gerd Score
- **Data Entry**:
  - Can only be created when a visit is selected.
  - All Gerd Score fields are optional, with notifications for unfilled optional fields.
- **Reviewing Data**:
  - The stored Gerd Score for the selected visit is displayed for reference.
- **Updating and Deleting**:
  - The Gerd Score can be updated or deleted.
  - A warning appears before any change to prevent accidental data loss.


### Medication
- **Adding Medication**:
  - Medications can only be added when a visit is selected.
  - An unlimited number of medications can be stored for each visit.
- **Reviewing Data**:
  - All saved medications for the selected visit are displayed for reference.
- **Deleting Medication**:
  - The GUI does not currently allow individual medication deletions; all medications for a visit must be deleted and re-entered.
  - The GUI can be extended to support individual medication deletions in the future. The database does support individual deletions.


---

## Diagnostics & Therapy Tab

- **Activation**:
  - The fields in the tab become active only when a visit is selected. Without a selection, it they remain inactive.
- **Therapy Data**:
  - Therapy data is collected if the visit type is set to "Therapy".
  - Therapy types include:
    - Botox Injection
    - Pneumatic Dilation
    - POEM
    - LHM
  - The input form displayed for therapy will vary based on the selected therapy type (e.g., if the therapy type is "POEM," the corresponding form for POEM therapy is shown).
- **Diagnostic Data**:
  - Diagnostic data is always collected, regardless of the visit type.
  - Diagnostic procedures include:
    - Manometry
    - Timed Barium Esophagogram (TBE)
    - Esophagogastroduodenoscopy (EGD)
    - Impedance Planimetry (EndoFlip)
    - Endosonography
- **3D Reconstruction**:
  - These diagnostic and therapy data are optional and the software is functional without them.
  - For 3D esophagus reconstruction, the following files are mandatory:
    - TBE image(s) (.jpg or .png)
    - Manometry pressure file (.csv) 
  - Optional data (e.g., endoscopy images, EndoFlip .xlsx files) can also be uploaded to further support the reconstruction process.

### Manometry Data Management
- **Data Input Requirements**: 
  - Data entry is only possible if a visit is selected.  Without a selected visit, data upload is deactivated.
- **Data Handling**:
  - **Manometry Data**:
    - If incomplete, users are notified of missing fields.
    - Saved data is displayed for reference and can be updated by overwriting existing data.
    - Update and deletion warnings for data loss prevention.
  - **Manometry Pressure File**:
    - A .csv file (from 'Laborie stationary measurement & analysis software') can be uploaded and updated.
    - Update prompts a warning to prevent accidental file replacement.

### Timed Barium Esophagogram (TBE) Data Management
- **Data Input Requirements**: 
  - Data entry is only possible if a visit is selected.  Without a selected visit, data upload is deactivated.
- **Data Handling**:
  - **TBE Data**:
    - Incomplete uploads prompt a notification.
    - Saved data is displayed and can be updated by overwriting existing data.
    - Update and deletion warnings for data loss prevention.
  - **TBE Images**:
    - Images (.jpg, .png) are uploaded, with .png converted to .jpg for consistency.
    - Preview display with associated timepoints.
    - Image navigation using "previous" and "next" buttons.
    - Update and deletion warnings to prevent accidental data loss when replacing images.

### Esophagogastroduodenoscopy (EGD) Data Management
- **Data Input Requirements**: 
  - Data entry is only possible if a visit is selected.  Without a selected visit, data upload is deactivated.
- **Data Handling**:
  - **EGD Data**:
    - Incomplete uploads trigger a notification.
    - Saved data is displayed and can be updated by overwriting existing data.
    - Update and deletion warnings to prevent accidental data loss.
  - **EGD Images**:
    - Images (.jpg, .png) are uploaded, with .png converted to .jpg for consistency.
    - Preview display with image height for reference.
    - Image navigation with "previous" and "next" buttons.
    - Update and deletion warnings to prevent accidental data loss.

### Impedance Planimetry (EndoFlip) Data Management
- **Data Input Requirements**:  
  - Data entry is only possible if a visit is selected.  Without a selected visit, data upload is deactivated.
- **Data Handling**:
  - **EndoFlip Data**:
    - Incomplete uploads trigger a notification.
    - Saved data is displayed and can be updated by overwriting existing data.
    - Update and deletion warnings for accidental data loss prevention.
  - **EndoFlip Images**:
    - Images (.jpg, .png) can be uploaded, with .png converted to .jpg for consistency.
    - Preview display with image timepoints ("before", "during", "after") for reference.
    - Image navigation with "previous" and "next" buttons.
    - Update and deletion warnings to prevent accidental data loss.
  - **EndoFlip Files**:
    - .xlsx files with measurement data (before, during, after) can be uploaded.
    - Update and deletion warnings to prevent accidental data loss when replacing files.

### Endosonography Data Management
- **Data Input Requirements**: 
  - Data entry is only possible if a visit is selected.  Without a selected visit, data upload is deactivated.
- **Data Handling**:
  - **Endosonography Images**:
    - Images (.jpg, .png) can be uploaded, with .png converted to .jpg for consistency.
    - Preview display with image height for reference.
    - Image navigation using "previous" and "next" buttons.
    - Update and deletion warnings to prevent accidental data loss.
  - **Endosonography Videos**:
    - Videos can be uploaded and later downloaded via the user interface.
    - Update and deletion warnings to prevent accidental data loss.

### Botox Injection Data Management
- **Data Input Requirements**:
  - Data entry is only possible if a visit is selected. 
  - Botox injection data can only be input if the visit type is set to "Therapy" and the therapy type is "Botox Injection". Otherwise, the input form is not shown.
- **Data Handling**:
  - Multiple injections can be associated with a single visit to form a "Botox Therapy".
  - Saved Botox therapy data is displayed for easy reference.
  - Complications related to the Botox Therapy can be uploaded and displayed next to the input box.
- **Updating and Deleting**:
  - Both, Botox therapy data and complication data can be deleted not be updated (without prior deletion) over the GUI. (It is possible to extend the GUI to support updates. The database supports updates.)
  - Warnings appear when deleting Botox Therapy data or Complication data to prevent accidental data loss.

### Pneumatic Dilation Data Management
- **Data Input Requirements**
  - Data entry is only possible if a visit is selected.
  - Pneumatic Dilation data can only be entered when the visit type is set to "Therapy" and the therapy type is "Pneumatic Dilation". Otherwise, the input form is not shown.
- **Data Handling**
  - Only one Pneumatic Dilation Therapy can be associated with each selected visit.
  - The saved Pneumatic Dilation Therapy data is displayed for easy reference in the interface.
  - Complications related to the Pneumatic Dilation Therapy are automatically saved along with the therapy.
  - Complications are also displayed in the interface for easy reference.
- **Updating and Deleting**:
  - Both the Pneumatic Dilation Therapy and associated complications can be updated or deleted.
  - Warnings appear when updating or deleting data to prevent accidental loss.

### Pneumatic Dilation Data Management
- **Data Input Requirements**
  - Data entry is only possible if a visit is selected.
  - Pneumatic Dilation data can only be entered when the visit type is set to "Therapy" and the therapy type is "Pneumatic Dilation". Otherwise, the input form is not shown.
- **Data Handling**
  - Only one Pneumatic Dilation Therapy can be associated with each selected visit.
  - The saved Pneumatic Dilation Therapy data is displayed for easy reference in the interface.
  - Complications related to the Pneumatic Dilation Therapy are automatically saved along with the therapy.
  - Complications are also displayed in the interface for easy reference.
- **Updating and Deleting**:
  - Both the Pneumatic Dilation Therapy and associated complications can be updated or deleted.
  - Warnings appear when updating or deleting data to prevent accidental loss.

### LHM Data Management
- **Data Input Requirements**
  - Data entry is only possible if a visit is selected.
  - LHM data can only be entered when the visit type is set to "Therapy" and the therapy type is "LHM". Otherwise, the input form is not shown.
- **Data Handling**
  - Only one LHM Therapy can be associated with each selected visit.
  - The saved LHM Therapy data is displayed for easy reference in the interface.
  - Complications related to the LHM Therapy are automatically saved along with the therapy.
  - Complications are also displayed in the interface for easy reference.
- **Updating and Deleting**:
  - Both the LHM Therapy and associated complications can be updated or deleted.
  - Warnings appear when updating or deleting data to prevent accidental loss.

### POEM Data Management
- **Data Input Requirements**
  - Data entry is only possible if a visit is selected.
  - POEM data can only be entered when the visit type is set to "Therapy" and the therapy type is "POEM". Otherwise, the input form is not shown.
- **Data Handling**
  - Only one POEM Therapy can be associated with each selected visit.
  - The saved POEM Therapy data is displayed for easy reference in the interface.
  - Complications related to the POEM Therapy are automatically saved along with the therapy.
  - Complications are also displayed in the interface for easy reference.
- **Updating and Deleting**:
  - Both the POEM Therapy and associated complications can be updated or deleted.
  - Warnings appear when updating or deleting data to prevent accidental loss.

---

## Creating a 3D reconstruction


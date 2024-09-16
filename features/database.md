# Database Features

## Patients Tab

### Managing Patients
- **Adding Patients**:
  - Patients are added via an input form with basic validation checks.
  - Missing optional fields trigger a notification.
  - Missing mandatory fields must be corrected before saving.
- **Patient List**:
  - Patients can be selected by clicking on their ID.
  - Patients can be sorted and filtered by any attribute.
  - A search function with autocomplete (by ID) is available.
- **Updating Patients**:
  - Patient data can be updated by entering new data for the same ID.
- **Deleting Patients**:
  - Patients can be deleted, along with all associated data (e.g., visits, therapies).
  - A warning appears before deletion or updates to prevent accidental changes.

### Managing Previous Therapies
- **Adding Previous Therapies**:
  - Only available when a patient is selected; otherwise, the field remains inactive.
  - Missing optional or mandatory fields trigger notifications to ensure proper data entry.
- **Managing Existing Therapies**:
  - Previously added therapies can be selected, viewed, or deleted.
  - Warnings appear when deleting a previous therapy to prevent accidental deletion.

---

## Visits Tab

### Managing Visits
- **Adding Visits**:
  - Visits can only be created when a patient is selected. Without a patient, the field remains inactive.
  - Missing mandatory fields must be corrected before saving.
- **Visit List**:
  - Visits can be selected by clicking on their ID.
  - Selected visits can be deleted, along with all associated data, though the patient remains.
  - Warnings appear before deleting a visit to prevent accidental loss.

### Selecting a Visit
  - When a visit is selected for the visits list, the fields **Eckardt Score**, **Gerd Score**, and **Medication** are unlocked for data entry.

### Eckardt Score
- **Data Entry**:
  - Can only be created when a visit is selected.
  - Validation ensures individual scores must match the total score.
  - Either the total score or individual scores must be filled in.
- **Updating and Deleting**:
  - The Eckardt Score can be updated or deleted.
  - A warning appears before any change to prevent accidental data loss.
- **Reviewing Data**:
  - The stored Eckardt Score for the selected visit is displayed for reference.

### Gerd Score
- **Data Entry**:
  - Can only be created when a visit is selected.
  - All Gerd Score fields are optional, with notifications for unfilled optional fields.
- **Updating and Deleting**:
  - The Gerd Score can be updated or deleted.
  - A warning appears before any change to prevent accidental data loss.
- **Reviewing Data**:
  - The stored Gerd Score for the selected visit is displayed for reference.

### Medication
- **Adding Medication**:
  - Medications can only be added when a visit is selected.
  - An unlimited number of medications can be stored for each visit.
- **Reviewing Medication**:
  - All saved medications for the selected visit are displayed for review.
- **Deleting Medication**:
  - The GUI does not currently allow individual medication deletions; all medications for a visit must be deleted and re-entered.
  - The interface can be extended to support individual medication deletions in the future.

---

## Diagnostics & Therapy Tab

- **Activation**: The tab becomes active only when a visit is selected. Without a selection, it remains inactive.
- **Therapy Data**:
  - Therapy data is collected if the visit type is set to "Therapy."
  - Therapy types include:
    - Botox Injection
    - Pneumatic Dilation
    - POEM
    - LHM
- **Diagnostic Data**:
  - Diagnostic data is always collected, regardless of the visit type.
  - Diagnostic procedures include:
    - Manometry
    - Timed Barium Esophagogram (TBE)
    - Esophagogastroduodenoscopy (EGD)
    - Impedance Planimetry (EndoFlip)
    - Endosonography
- **3D Reconstruction**:
  - For 3D esophagus reconstruction, **TBE images** and a **Manometry .csv file** are mandatory.
  - Additional optional files (e.g., endoscopy images, EndoFlip data) can also be uploaded.

---


## Manometry Data Management
- **Data Input Requirements**: Only possible if a visit is selected. Without a selected visit, data upload is deactivated.
- **Data Handling**:
  - **Manometry Data**:
    - If incomplete, users are notified of missing fields.
    - Saved data is displayed for reference and can be updated by overwriting existing data.
    - Update and deletion warnings for data loss prevention.
  - **Manometry Pressure File**:
    - A .csv file (from 'Laborie stationary measurement & analysis software') can be uploaded and updated.
    - Update prompts a warning to prevent accidental file replacement.

---

## Timed Barium Esophagogram (TBE) Data Management
- **Data Input Requirements**: Only possible if a visit is selected. Without a selected visit, data upload is deactivated.
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

---

## Esophagogastroduodenoscopy (EGD) Data Management
- **Data Input Requirements**: Only possible if a visit is selected. Without a selected visit, data upload is deactivated.
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

---

## Impedance Planimetry (EndoFlip) Data Management
- **Data Input Requirements**: Only possible if a visit is selected. Without a selected visit, data upload is deactivated.
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

---

## Endosonography Data Management
- **Data Input Requirements**: Only possible if a visit is selected. Without a selected visit, data upload is deactivated.
- **Data Handling**:
  - **Endosonography Images**:
    - Images (.jpg, .png) can be uploaded, with .png converted to .jpg for consistency.
    - Preview display with image height for reference.
    - Image navigation using "previous" and "next" buttons.
    - Update and deletion warnings to prevent accidental data loss.
  - **Endosonography Videos**:
    - Videos can be uploaded and later downloaded via the user interface.
    - Update and deletion warnings to prevent accidental data loss.

---

## Botox Injection Data Management
- **Data Input Requirements**:
  - Only possible if a visit is selected.
  - Botox injection data can only be input if the visit type is "Therapy" and therapy type is "Botox Injection".
- **Data Handling**:
  - **Botox Injection Data**:
    - Multiple injections can be associated with a single visit to form a "Botox Therapy".
    - Saved Botox therapy data is displayed for easy reference.
    - Botox Therapy data can be deleted but not updated.
    - Deletion warnings to prevent accidental data loss.
  - **Complications**:
    - Complications associated with Botox therapy can be uploaded and displayed next to the input box.
    - Complications associated with a Botox therapy can be deleted but not updated (without previous deletion).
    - Deletion warnings when complications are removed.

---

## Pneumatic Dilation Data Management
- **Data Input Requirements**:
  - Only possible if a visit is selected.
  - Botox injection data can only be input if the visit type is "Therapy" and therapy type is "Botox Injection".


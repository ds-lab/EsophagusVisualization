# Database Features

## Patients Tab

### Managing Patients
- Patients can be stored in the database via the input form.
- Basic validation checks are performed when storing patient data in the database.
- If optional data fields are not filled in, the user will be notified.
- If mandatory data fields are not filled in, the user will be notified and must correct them.
- Patients can be selected from the patient list by clicking on their ID.
- Patients in the list can be sorted in ascending or descending order by all attributes.
- Patients can be filtered by all attributes.
- In the input form, patients can be searched using the autocomplete function by ID.
- Patient data can be updated when new data is entered for the same ID.
- Patients can be deleted from the database. When a patient is deleted, all associated data (i.e., their visits and all related data) will also be deleted.
- Warnings appear when deleting or updating a patient to prevent accidental deletion/updates.

### Managing Previous Therapies
- When a patient is selected in the Patients tab, previous therapies can be added for that patient. If no patient is selected, this is not possible. A message will appear prompting the user to select a patient, and the field for adding previous therapies will be inactive.
- If optional data fields (for previous therapies) are not filled in, the user will be notified.
- If mandatory data fields are not filled in, the user will be notified and must correct them.
- Previously added therapies can be selected from the list of previous therapies.
- Selected therapies can be deleted.
- Warnings appear when deleting a previous therapy to prevent accidental deletion.

## Visits Tab

### Managing Visits
- Visits can only be created when a patient is selected.
- If no patient is selected, a message will appear prompting the user to select a patient. Additionally, the fields for creating a visit (and related data) will be inactive.
- Basic validation checks are performed when storing visit data.
- If mandatory data fields are not filled in, the user will be notified and must correct them.
- Visits can be selected from the visit list by clicking on their ID.
- Selected visits can be deleted. When a visit is deleted, all associated data is also deleted. However, the patient to whom the visit belongs remains in the database.
- Warnings appear when deleting a visit to prevent accidental deletion.
- When a visit is selected, the following fields in the Visits tab are unlocked to store additional data related to the visit: Eckardt Score, Gerd Score, Medication. All of these additional data fields are optional and do not need to be filled in.

### Eckardt Score
- An Eckardt Score can only be created when a visit is selected.
- Basic validation checks are performed when storing Eckardt Score data: the individual scores must add up to the total score if all individual scores are filled in. If not all individual scores are filled, the individual scores cannot be greater than the total score.
- Either the total score or all individual scores are mandatory fields that must be filled in.
- If optional data fields are not filled in, the user will be notified.
- If mandatory data fields are not filled in, the user will be notified and must correct them.
- The Eckardt Score of a visit can be deleted or updated.
- Warnings appear when deleting or updating the Eckardt Score to prevent accidental deletion or updates.
- The currently stored Eckardt Score attributes for the selected visit is displayed in a text field below the input box.

### Gerd Score
- A Gerd Score can only be created when a visit is selected.
- All data fields of the Gerd Score are optional.
- If optional data fields are not filled in, the user will be notified.
- The Gerd Score of a visit can be deleted or updated.
- Warnings appear when deleting or updating the Gerd Score to prevent accidental deletion or updates.
- The currently stored Gerd Score for the selected visit is displayed in a text field below the input box.

### Medication
- Medication can only be added to a visit when a visit is selected.
- If optional data fields are not filled in, the user will be notified.
- If mandatory data fields are not filled in, the user will be notified and must correct them.
- An unlimited number of medications can be stored for a visit.
- The medications saved for a visit in the database are displayed in a text field below the input form for review.
- It is not possible to delete individual medications via the GUI. However, all medications associated with a visit can be deleted and re-entered.
- The GUI is extendable, for example, to add features for deleting individual medications from the history.

## Diagnostics & Therapy Tab

- The Diagnostics & Therapy tab can only be populated with data if a visit is selected. If no visit (or patient) is selected, a message will prompt the user to select one, and the tab will remain inactive.
- Therapy data is requested in the Diagnostics & Therapy tab only if the visit type is set to "Therapy". For other visit types, only diagnostic data is collected.
- If the visit type is "Therapy", the specific therapy data requested will depend on the therapy type selected, which can include:
  - Botox Injection
  - Pneumatic Dilation
  - POEM 
  - LHM
- Diagnostic data is always collected, regardless of the visit type. This includes:
  - Manometry
  - Timed Barium Esophagogram (TBE)
  - Esophagogastroduodenoscopy (EGD)
  - Impedance Planimetry (EndoFlip)
  - Endosonography
- Both therapy and diagnostic data entry are optional. However, for the 3D reconstruction of the esophagus, at least one or more TBE images and a manometry .csv file must be uploaded, as these are essential for the 3D reconstruction. Additionally, the algorithm can optionally process endoscopy images and EndoFlip data (.xlsx file).


### Manometry Data Management

- Manometry data:
  - Manometry data can only be uploaded if a visit is selected. If no visit is selected, the option to input and upload data will be deactivated.
  - Uploading manometry data is optional.
  - If optional data fields are not filled in, the user will be notified.
  - Manometry data saved for the currently selected visit are displayed next to the input form for easy reference.
  - Manometry data can be updated by overwriting the currently saved data.
  - When updating manometry data, the user will receive a warning to prevent accidental data loss.
  - When deleting manometry data, the user will be warned to avoid accidental data loss.
- Manometry pressure file:
  - Additionally, a .csv file of the Manometry measurements (from 'Laborie stationary measurement & analysis software' by Medical Measurement Systems B.V.) can be uploaded in the database.
  - This file can be updated by uploading a new file. In this case, the user will be warned, to prevent accidental data loss.

### Timed Barium Esophagogram (TBE) Data Management

- TBE data:
  - TBE data can only be uploaded if a visit is selected. If no visit is selected, the option to input and upload data will be deactivated.
  - Uploading TBE data is optional.
  - If optional data fields are not filled in, the user will be notified.
  - TBE data saved for the currently selected visit are displayed next to the input form for easy reference.
  - TBE data can be updated by overwriting the currently saved data.
  - When updating TBE data, the user will receive a warning to prevent accidental data loss.
  - When deleting TBE data, the user will be warned to avoid accidental data loss.
- TBE images:
  - TBE images (.jpg or .png) can be uploaded to the database. .png images are internally converted to .jpg for consistent file handling.
  - A preview of the uploaded TBE images is displayed in the TBE section.
  - The timepoint of each TBE image is shown above the image for reference.
  - The user can scroll through the TBE images using the "previous" and "next" buttons.
  - The user can update TBE images by uploading new versions.
  - When updating TBE images, the user will receive a warning to prevent accidental data loss.
  - When updating, the old images will be deleted (after user confirmation) and replaced with the newly uploaded files.

### Esophagogastroduodenoscopy (EGD) Data Management

- EGD data:
  - EGD data can only be uploaded if a visit is selected. If no visit is selected, the option to input and upload data will be deactivated.
  - Uploading EGD data is optional.
  - If optional data fields are not filled in, the user will be notified.
  - EGD data saved for the currently selected visit are displayed next to the input form for easy reference.
  - EGD data can be updated by overwriting the currently saved data.
  - When updating EGD data, the user will receive a warning to prevent accidental data loss.
  - When deleting EGD data, the user will be warned to avoid accidental data loss.
- EGD images:
  - EGD images (.jpg or .png) can be uploaded to the database. .png images are internally converted to .jpg for consistent file handling.
  - A preview of the uploaded EGD images is displayed in the EGD section.
  - The height of each EGD image is shown above the image for reference.
  - The user can scroll through the EGD images using the "previous" and "next" buttons.
  - The user can update EGD images by uploading new versions.
  - When updating EGD images, the user will receive a warning to prevent accidental data loss.
  - When updating, the old images will be deleted (after user confirmation) and replaced with the newly uploaded files.

### Impedance Planimetry (EndoFlip) Data Management

- EndoFlip data:
  - EndoFlip data can only be uploaded if a visit is selected. If no visit is selected, the option to input and upload data will be deactivated.
  - Uploading EndoFlip data is optional.
  - If optional data fields are not filled in, the user will be notified.
  - EndoFlip data saved for the currently selected visit are displayed next to the input form for easy reference.
  - EndoFlip data can be updated by overwriting the currently saved data.
  - When updating EndoFlip data, the user will receive a warning to prevent accidental data loss.
  - When deleting EndoFlip data, the user will be warned to avoid accidental data loss.
- EndoFlip images:
  - EndoFlip images (.jpg or .png) can be uploaded to the database. .png images are internally converted to .jpg for consistent file handling.
  - A preview of the uploaded EndoFlip images is displayed in the EGD section.
  - The timepoint ("before", "during" or "after") of each EndoFlip image is shown above the image for reference.
  - The user can scroll through the EGD images using the "previous" and "next" buttons.
  - The user can update EGD images by uploading new versions.
  - When updating TBE images, the user will receive a warning to prevent accidental data loss.
  - When updating, the old images will be deleted (after user confirmation) and replaced with the newly uploaded files.
- EndoFlip Files:
  - .xlsx files containing EndoFlip measurements (before, during, and after the procedure) can be uploaded to the database.
  - These files can be updated by uploading new versions. The user will receive a warning to prevent accidental data loss.
  - When updating, the old files will be deleted (after user confirmation) and replaced with the newly uploaded files.

### Endosonography Data Management

- Endosonography images:
  - Endosonography images (.jpg or .png) can be uploaded to the database. .png images are internally converted to .jpg for consistent file handling.
  - A preview of the uploaded Endosonography images is displayed in the Endosonography section.
  - The height of each Endosonography image is shown above the image for reference.
  - The user can scroll through the Endosonography images using the "previous" and "next" buttons.
  - The user can update Endosonography images by uploading new versions.
  - When updating Endosonography images, the user will receive a warning to prevent accidental data loss.
  - When updating, the old images will be deleted (after user confirmation) and replaced with the newly uploaded files.
- Endosonography videos:
  - Endosonography videos can be uploaded to the database.
  - Endosonography videos currently saved in the database can be downloaded to the computer of the user via the user-interface.
  - The user can update Endosonography videos by uploading new versions.
  - When updating Endosonography videos, the user will receive a warning to prevent accidental data loss.
  - When updating, the old videos will be deleted (after user confirmation) and replaced with the newly uploaded files.


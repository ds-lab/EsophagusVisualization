# The Diagnostics & Therapy Tab

After selecting a patient and a visit, this tab allows you to input diagnostic data and therapy details.

![Diagnostics_and_Therapy_Tab](/manual_images/diagnostics_and_therapy_tab.jpg)

In the upper right corner, you can enter therapy data if the visit type is set to "Therapy". Otherwise, this field will remain empty.

In the lower half of the window, you can input diagnostic data related to manometry, timed barium esophagogram (TBE or barium swallow), esophagogastroduodenoscopy (EGD), impedance planimetry (EndoFLIP), endosonography, and upload any related files.


## Diagnostic Data

For most diagnostic procedures, you can input relevant data as well as upload recorded files (obtained from the diagnostic instruments) or related images or video recordings. When entering data, fill in all the fields you can or wish to, and leave the others at their default values (e.g., -1 or ---). These will be marked as "unknown" in the database.

The data you save will be displayed in a small window on the right-hand side.

If you notice an error, you can update the data by making corrections and clicking the "Add/Update" button.

## Manometry

![Manometry](/manual_images/manometry.jpg)

In addition to entering attributes related to the manometry measurement, you can upload a manometry file to the database. 

**File Format**: This file should be a .csv file obtained from the 'Laborie stationary measurement & analysis software' by Medical Measurement Systems B.V. (or a .csv file organized in the same format).

If you upload an incorrect .csv file, simply repeat the upload process to upload the correct file.

## Timed Barium Esophagogram (TBE)

![TBE](/manual_images/TBE.jpg)

Along with attributes related to the barium swallow, you can upload multiple TBE (Barium Swallow) images. 

- **Image Format**: Images must be in .jpg or .png format.
- **File Naming**: The filenames should be formatted as follows: X.jpg or X.png, where X represents the time in minutes when the X-ray image was taken.

All images must be uploaded simultaneously (just select all the images you wish to upload). 

If you upload the wrong images, simply repeat the upload process.

The image viewer on the right will display a preview of the images you uploaded.

## Esophagogastroduodenoscopy (EGD)

![EGD](/manual_images/EGD.jpg)

Similarly, you can upload EGD images. 

- **Image Format**: Images must be in .jpg or .png format.
- **File Naming**: The filenames should end with Xcm.jpg or Xcm.png, where X represents the height in the esophagus where the image was taken.

All images must be uploaded simultaneously (just select all the images you wish to upload). 

If you upload the wrong images, simply repeat the upload process.

## Impedance Planimetry (EndoFLIP)

![EndoFlip](/manual_images/Endoflip.jpg)

For impedance planimetry (EndoFLIP), you can enter specific attributes and upload related files. These files can include impedance planimetry data in .xlsx format (Excel) and images (screenshots from the diagnostic instrument).

- **Image Format**: Images must be in .jpg or .png format.
- **File Naming**: Filenames should be labeled as "before," "during," or "after," depending on the time point. The Excel files should also follow this naming convention.

When uploading multiple files or images (e.g., for all three time points: before, during, and after), you must upload them simultaneously.

If you mistakenly upload incorrect images or files, simply repeat the upload process to correct it.

## Endosonography

![Endosonography](/manual_images/Endosonography.jpg)

For endosonography, you can upload both videos and images:

- **Video Format**: Videos must be in .avi format.
- **Image Format**: Images must be in .png or .jpg format.
- **File Naming**: Image filenames should indicate the position (height) at which they were taken. For example, the filename should end with "Xcm.jpg" or "Xcm.png," where "X" represents the height in the esophagus.

When uploading multiple videos or images, they must be uploaded simultaneously.

The image viewer on the right will show previews of the images you uploaded. To view the videos, you will need to download them using the download button.

If you upload incorrect images or videos, simply repeat the upload process to correct it.

## Therapy Data

If "Therapy" is selected as the visit type, you can enter data for the chosen therapy (Botox, Pneumatic Dilation, LHM, or POEM) in the field located in the upper right corner of the Diagnostics & Therapy Tab. If "Initial Diagnostics" or "Follow-Up Diagnostics" is selected as the visit type, this field will remain empty.

**General Instructions**: Fill out all the therapy data you are able or wish to provide, along with any complications associated with the therapy. Once complete, click the "Add Therapy" button.

## Botox

![Botox](/manual_images/botox.jpg)

A patient can receive multiple Botox injections at different heights during a single visit. Therefore, it is possible to add multiple Botox injections, including their Botox units and injection heights, to a single "Botox Therapy."

**Note**: After adding all the Botox injections, click the "Add Botox Therapy" button to save the selected complications (if any) along with the therapy.

To delete all Botox injections and the associated complications in case of erroneous data entry, use the "Delete Botox Therapy" button.

## Pneumatic Dilation

![Pneumatic Dilation](/manual_images/pneumatic_dilation.jpg)

Provide all the relevant attributes for Pneumatic Dilation and any complications associated with this therapy.   
When finished, click the "Add / Update Pneumatic Dilation" button. This button can also be used to update any incorrect data.

## LHM

![LHM](/manual_images/lhm.jpg)

Provide all the relevant attributes for LHM and any complications associated with this therapy.  
The operation duration is entered in hh:mm format but is converted to minutes in the database.  
When finished, click the "Add / Update LHM" button. This button can also be used to update any incorrect data.

## POEM

![POEM](/manual_images/poem.jpg)

Enter all relevant attributes for POEM and any complications associated with this therapy.  
The procedure duration is entered in hh:mm format but is converted to minutes in the database.  
When finished, click the "Add / Update POEM" button. This button can also be used to update any incorrect data.


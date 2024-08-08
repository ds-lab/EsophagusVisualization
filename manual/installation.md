# Installation

By following these instructions, you will have a complete setup of the Esophagus Visualization and Data Management Software, with a PostgreSQL database managed via Docker and pgAdmin, and regular backups configured to ensure data integrity.

## Setup Docker
1. **Install Docker Desktop**: 
    - If you don't already have Docker Desktop installed, download and install it from the [Docker website](https://www.docker.com/products/docker-desktop). 

2. **Run Docker Compose**:
    - Ensure you are in the directory containing the `docker-compose.yml` and `init.sql` files.
    - Open a terminal (or command prompt) in this directory and execute the following command to start the containers:
      ```sh
      docker-compose up -d
      ```
    - This command will build and start the containers.


3. **Access pgAdmin (optional)**:
    - Once the containers are up and running, you can access pgAdmin to manage the PostgreSQL database of this app.
    - Open your web browser and go to `http://localhost:8080`.
    - Use the following credentials to log in:
      - **Username**: `admin@admin.com`
      - **Password**: `123+qwe`
    - Register a new Server:
      - Right-click on "Servers" and select "Register" -> "Server":
        - Tab "General":
          - **Name**: `3drekonstruktionspeiseroehre`
        - Tab "Connection":
          - **Host/name address**: `db`
          - **Port**: `5432`
          - **Maintainance db**: `postgres`
      - Click "Save". You should now see `3drekonstruktionspeiseroehre` listed under "Servers".
      - The database `3drekonstruktion` contains the data schema for this application (initially empty).

## Install the Software

Run `EsophagusVisualizationSetup.exe` and follow the installation instructions.  

**Note**: You might need to temporarily disable your antivirus software during the installation process.  
Afterwards, add EsophagusVisualization to your antivirus whitelist.

## Create Backups of the Database

1. **Update Paths in the Backup Script**:
    - Open the `postgres_backup.bat` file with a text editor and update the path to where you want to store your backups.


2. **Schedule the Backup Execution**:
    - Open the Windows Task Scheduler ("Aufgabenplanung") and import the task ("Aufgabe importieren") using the `Postgres_Backup.xml` file.
    - Double-click the imported task to open it and adjust the settings to your system:
      - Under "Allgemein", change the user.
      - Under "Aktionen", adjust the path to the `.bat` file.


3. **Create Redundant Backups**:
    - Download and install [Duplicati](https://duplicati.com/).
    - Duplicati allows the creation of encrypted backups based on a schedule.
    - The backups are stored incrementally to save storage space.
    - Click "Add Backup" and import the configuration file `Postgres_Backup-duplicati-config.json`.
    - Adjust the paths for the backup. Ideally, the backup should be stored in a different location than the original data and the initial backup.
    - Optionally, change the password for encryption.


### Stopping the Backup Processes

If you need to stop backups, follow these steps:

1. **Disable the original backups**:
    - Open the Windows Task Scheduler ("Aufgabenplanung").
    - Find the task named "Postgres_Backup".
    - Click "Disable" ("Deaktivieren") to stop the task or "Delete" ("Löschen") to remove it (you can re-import the task later if needed).


2. **Stop the creation of redundant backups**:
    - Open Duplicati.
    - Navigate to `Home -> Postgres_Backup`.
    - Click "Delete" ("Löschen") to remove the backup configuration (you can re-import the configuration file later if necessary).

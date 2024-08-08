## Restore Database

If you have created backups as described in the installation instructions, you can restore the database in case it becomes corrupted. However, keep in mind that backups are created periodically (e.g., every 15 minutes), so some data loss might occur. Follow these steps to restore the database:

1. **Navigate to Your Backup Folder**:
   - This folder contains your backups, named like `backup_2024-08-06_16-21-20.sql`, and a `docker-compose.yml` file.


2. **Adjust Paths and Run Commands**:
   - Open a terminal in the directory containing your backup files.
   - Ensure the paths in the commands below match the location of your backup files.


3. **Execute the Restore Commands**:

* Start the Docker Containers:
     ```sh
     docker-compose up -d
     ```

* Copy the Backup File into the Docker Container:  
     Adjust the source path (`C:/path/to/your/backup_2024-08-06_16-21-20.sql`) to match the actual location of your backup file.
     ```sh
     docker cp C:/path/to/your/backup_2024-08-06_16-21-20.sql postgres:/backup.sql
     ```

* Access the PostgreSQL Container:
     ```sh
     docker exec -it postgres bash
     ```
     This opens an interactive terminal inside the container.

* Restore the Database:  
     Once inside the container, restore the database:
     ```sh
     psql -U admin -d 3drekonstruktion -f /backup.sql
     ```
    This command connects to the `3drekonstruktion` database as the user `admin` and restores the database using the specified backup file.

## What to do if your backup-file got lost or corrupted?

If your backup files are lost or corrupted, you can restore from Duplicati backups:

1. **Open Duplicati**


2. **Navigate to the Restore Option**:
   - Go to `Home` -> `Postgres Backup` -> `Restore data`.


3. **Select a Backup to Restore**:
   - Choose the backup you want to restore from the available list.
   - Follow the prompts to restore the backup.


4. **Restore the Database Using the Restored Backup File**:
   - Once the backup is restored to your system, follow the same steps as described above to copy the backup file into the Docker container and restore the database.



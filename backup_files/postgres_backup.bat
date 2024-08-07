@echo off

REM Get date and time
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "dateTime=%%I"
set "year=%dateTime:~0,4%"
set "month=%dateTime:~4,2%"
set "day=%dateTime:~6,2%"
set "hour=%dateTime:~8,2%"
set "minute=%dateTime:~10,2%"
set "second=%dateTime:~12,2%"
set "timestamp=%year%-%month%-%day%_%hour%-%minute%-%second%"

REM Create a backup in a Docker container
docker exec -it postgres bash -c "pg_dump -U admin -d 3drekonstruktion > /backup.sql"

REM Copy and rename a backup from a Docker container to a Windows system
REM Adjust paths to paths of your system
docker cp postgres:/backup.sql "C:/Users/piasc/Documents/Studium/Projekt-Achalasie/Postgres-Backup/backup_%timestamp%.sql"

REM Clean up old backups
REM Adjust paths to paths of your system
cd "C:/Users/piasc/Documents/Studium/Projekt-Achalasie/Postgres-Backup/"
for /f "skip=5 delims=" %%F in ('dir /b /o-d backup_*.sql') do (
    del "%%F"
)




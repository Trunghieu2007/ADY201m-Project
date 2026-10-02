/* Optional bootstrap. Run while connected to master in SSMS. */
IF DB_ID(N'ADY201m') IS NULL
BEGIN
    CREATE DATABASE ADY201m;
END
GO

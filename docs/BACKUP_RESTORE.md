# Backup and restore
Use managed PostgreSQL backups plus periodic logical dumps stored outside the web service. Cloudinary is the media system of record; keep public IDs in PostgreSQL. Test a restore into staging at least quarterly. A deployment is not a backup. Record RPO/RTO targets before launch and verify restores rather than only backup creation.

#!/bin/bash
# exit on errors
set -e

#This is a simple rotating backup script for the rpmfind databases

BACKUP_DIR=/army/rpmprivate/centos/rpmfind_backups

# make directories 0 - 7, (if they don't exist)
/bin/mkdir -p $BACKUP_DIR/backup.{0..7}

#remove oldest backup
/bin/rm -rf $BACKUP_DIR/backup.7/

#rotate the rest of the backups
for i in {7..1}; do
    # move from (i-1) to (i)
    /bin/mv $BACKUP_DIR/backup.$[${i}-1] $BACKUP_DIR/backup.${i}
done

# After the move, we need to make backup.0 again for the newest backup
/bin/mkdir -p $BACKUP_DIR/backup.0

# dump MySQL databases into newest backup (index 0)
 mysqldump -uroji -pyellow rpmfind_centos6 > $BACKUP_DIR/backup.0/rpmfind_centos6.sql
 mysqldump -uroji -pyellow rpmfind > $BACKUP_DIR/backup.0/rpmfind.sql



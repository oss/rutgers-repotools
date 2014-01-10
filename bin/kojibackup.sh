#!/bin/bash

# Dump Koji DB to local disk
sudo -u koji pg_dump -C koji > /tmp/koji_dbdump.sql

# rsync to rpmprivate so that backups are made
rsync --archive --sparse --delete /army/centos/koji/packages/ /army/rpmprivate/centos/koji_backups/packages/
rsync --archive /tmp/koji_dbdump.sql /army/rpmprivate/centos/koji_backups/

# Clean up
rm -f /tmp/koji_dbdump

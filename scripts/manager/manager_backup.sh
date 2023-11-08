#!/bin/bash
set -ex
# create backup folder if it not already exists
mkdir -p /var/backups/asa-server

archive_name=(date +"%Y-%m-%d %T")

tar -czf /var/backups/asa-server/backup_${archive_name}.tar.gz -C /opt/arkserver/ShooterGame Saved

# count and output existing backups

count=$(ls /var/backups/asa-server/ | wc -l)
echo $count
#!/bin/bash
set -e
# create backup folder if it not already exists
mkdir -p /var/backups/asa-server

archive_name=$(date +"%Y-%m-%d_%H-%M-%S")

tar -czf /var/backups/asa-server/backup_${archive_name}.tar.gz -C /opt/arkserver/ShooterGame Saved

# count and output existing backups

count=$(ls /var/backups/asa-server/ | wc -l)

echo "Number of backups in path: ${count}"
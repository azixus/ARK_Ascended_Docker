#!/bin/bash
set -e
# create backup folder if it not already exists
path="/var/backups/asa-server"
mkdir -p 

archive_name=$(date +"%Y-%m-%d_%H-%M-%S")

tar -czf $path/backup_${archive_name}.tar.gz -C /opt/arkserver/ShooterGame Saved

# count and output existing backups

count=$(ls $path | wc -l)

echo "Number of backups in path: ${count}"
echo "Size of Backup folder: $(du -hs $path)
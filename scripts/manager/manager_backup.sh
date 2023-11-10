#!/bin/bash
set -e
# create backup folder if it not already exists
path="/var/backups/asa-server"
copyPath="/opt/arkserver/tmp/backup"

mkdir -p $path
mkdir -p $copyPath

archive_name=$(date +"%Y-%m-%d_%H-%M-%S")

# copy live path to another folder so tar doesnt get any write on read fails
echo "copying save folder"
cp -r -R /opt/arkserver/ShooterGame/Saved $copyPath

# tar.gz from the copy path
echo "creating archive"
tar -cvzf $path/backup_${archive_name}.tar.gz -C $copyPath Saved

rm -R $copyPath/*
# count and output existing backups

count=$(ls $path | wc -l)

echo "Number of backups in path: ${count}"
echo "Size of Backup folder: $(du -hs $path)"

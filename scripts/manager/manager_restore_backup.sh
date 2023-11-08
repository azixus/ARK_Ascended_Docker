#!/bin/bash

set -ex

i=1
echo "Here is a list of all your backup files: "

# list all files with a counter
for datei in $(ls /var/backups/asa-server); do
   echo "$i - - - - - Datei: $datei"
   i=$((i + 1))
done

echo "which file do you want to choose? (select a number from above according to the backup you want to recover)"
read num

archive=$(ls /var/backups/asa-server | sed -n "${num}p")

echo "You've choosen $archive"
echo "$archive gets restored...."

tar -xzf /var/backups/asa-server/$archive -C /opt/arkserver/ShooterGame/

res=$?

if [[ $res == 0 ]]; then
    echo "backup restored successfully!"
else
    echo "restoring failed."
fi
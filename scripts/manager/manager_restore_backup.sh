#!/bin/bash
set -e
i=1
echo "Here is a list of all your backup archives: "
path="/var/backups/asa-server"
# list all files with a counter
for datei in $(ls $path); do
   echo "$i - - - - - File: $datei"
   i=$((i + 1))
done

echo "Please input the number of the archive you want to restore."
read num

if [[ ! $num =~ ^[0-9]+$ ]] || [[ $num -ge $i ]]; then
    echo "Invalid input. Please enter a valid number."
    exit 1
fi
archive=$(ls $path | sed -n "${num}p")

echo "$archive is getting restored ..."

tar -xzf $path/$archive -C /opt/arkserver/ShooterGame/

res=$?

if [[ $res == 0 ]]; then
    echo "Backup restored successfully!"
else
    echo "An Error occured. Restoring failed."
fi
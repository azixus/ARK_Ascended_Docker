# ARK Survival Ascended Docker Server

This project relies on GloriousEggroll's Proton-GE in order to run the ARK Survival Ascended Server in a docker container under Linux.

## Usage
First, edit the [.env](./.env) file to modify the server configuration. You can start the ASA server as follows:
```bash
$ git clone git@github.com:AziXus/ASA_Server_Docker.git
$ cd ASA_Server_Docker
$ sudo docker compose up --build
asa_server  | [2023.10.30-20.37.00:460][  0]Log file open, 10/30/23 20:37:00
asa_server  | [2023.10.30-20.37.00:460][  0]LogMemory: Platform Memory Stats for WindowsServer
asa_server  | [2023.10.30-20.37.00:460][  0]LogMemory: Process Physical Memory: 333.11 MB used, 336.48 MB peak
asa_server  | [2023.10.30-20.37.00:460][  0]LogMemory: Process Virtual Memory: 304.26 MB used, 304.26 MB peak
asa_server  | [2023.10.30-20.37.00:460][  0]LogMemory: Physical Memory: 20491.50 MB used,  43678.80 MB free, 64170.30 MB total
asa_server  | [2023.10.30-20.37.00:460][  0]LogMemory: Virtual Memory: 33422.79 MB used,  63482.51 MB free, 96905.30 MB total
asa_server  | [2023.10.30-20.37.00:940][  0]ARK Version: 25.41
asa_server  | [2023.10.30-20.37.01:420][  0]Primal Game Data Took 0.34 seconds
asa_server  | [2023.10.30-20.37.38:196][  0]Server: "My Awesome ASA Server" has successfully started!
asa_server  | [2023.10.30-20.37.39:412][  0]Commandline:  TheIsland_WP?listen?SessionName="My Awesome ASA Server"?Port=7790?MaxPlayers=10?ServerPassword=MyServerPassword?ServerAdminPassword="MyArkAdminPassword"?RCONEnabled=True?RCONPort=32330?ServerCrosshair=true?OverrideOfficialDifficulty=5?ShowFloatingDamageText=true?AllowFlyerCarryPvE=true -log -NoBattlEye -WinLiveMaxPlayers=10 -ForceAllowCaveFlyers -ForceRespawnDinos -AllowRaidDinoFeeding=true -ActiveEvent=Summer
asa_server  | [2023.10.30-20.37.39:412][  0]Full Startup: 39.78 seconds
asa_server  | [2023.10.30-20.37.39:412][  0]Number of cores 6
asa_server  | [2023.10.30-20.37.43:587][  2]wp.Runtime.HLOD = "1"
```

After a few minutes, the server should appear on ASA's server browser.


### Useful commands
**Stopping the server gracefully**
```bash
$ docker compose exec -it asa_server sh -c 'rcon -a 127.0.0.1:${RCON_PORT} -p ${ARK_ADMIN_PASSWORD} DoExit'
Exiting...
```

**Saving the world**
```bash
$ docker compose exec -it asa_server sh -c 'rcon -a 127.0.0.1:${RCON_PORT} -p ${ARK_ADMIN_PASSWORD} SaveWorld'
Exiting...
```

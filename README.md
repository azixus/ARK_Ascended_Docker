# ARK Survival Ascended Docker Server
<meta name="google-site-verification" content="QcozzwjcfofcdaURG_OopEP3uyGmWzcL56iMC2i9MnU" />
This project relies on GloriousEggroll's Proton-GE in order to run the ARK Survival Ascended Server inside a docker container under Linux. This allows to run the ASA Windows server binaries on Linux easily.

### Configuration
The main server configuration is done through the [.env](./.env) file. This allows you to change the server name, port, passwords etc.

The server files are stored in a mounted volume in the [ark_data](./ark_data/) folder. The additional configuration files are found in this folder: [Game.ini](./ark_data/ShooterGame/Saved/Config/WindowsServer/Game.ini), [GameUserSettings.ini](./ark_data/ShooterGame/Saved/Config/WindowsServer/GameUserSettings.ini).

Unlike ARK Survival Evolved, only one port must be exposed to the internet, namely the `SERVER_PORT`. It is not necessary to expose the `RCON_PORT`.

### Usage
Download the container by cloning the repo and setting permissions:
```bash
$ git clone https://github.com/AziXus/ASA_Server_Docker.git
$ cd ASA_Server_Docker
$ sudo chown -R 1000:1000 ./ark_data
```

Before starting the container, edit the [.env](./.env) file to customize the starting parameters of the server. You may also edit [Game.ini](./ark_data/ShooterGame/Saved/Config/WindowsServer/Game.ini) and [GameUserSettings.ini](./ark_data/ShooterGame/Saved/Config/WindowsServer/GameUserSettings.ini) for additional settings. Once this is done, start the container as follow:
```
$ docker compose up --build -d
```

During the startup of the container, the ASA server is automatically downloaded with `steamcmd` and subsequently started. You can monitor the progress with the following command:
```bash
$ docker compose logs -f
asa_server  |[2023.10.31-17.06.19:714][  0]Log file open, 10/31/23 17:06:19
asa_server  |[2023.10.31-17.06.19:715][  0]LogMemory: Platform Memory Stats for WindowsServer
asa_server  |[2023.10.31-17.06.19:715][  0]LogMemory: Process Physical Memory: 319.32 MB used, 323.19 MB peak
asa_server  |[2023.10.31-17.06.19:715][  0]LogMemory: Process Virtual Memory: 269.09 MB used, 269.09 MB peak
asa_server  |[2023.10.31-17.06.19:715][  0]LogMemory: Physical Memory: 20649.80 MB used,  43520.50 MB free, 64170.30 MB total
asa_server  |[2023.10.31-17.06.19:715][  0]LogMemory: Virtual Memory: 33667.16 MB used,  63238.14 MB free, 96905.30 MB total
asa_server  |[2023.10.31-17.06.20:506][  0]ARK Version: 25.49
asa_server  |[2023.10.31-17.06.21:004][  0]Primal Game Data Took 0.35 seconds
asa_server  |[2023.10.31-17.06.58:846][  0]Server: "My Awesome ASA Server" has successfully started!
asa_server  |[2023.10.31-17.06.59:188][  0]Commandline:  TheIsland_WP?listen?SessionName="My Awesome ASA Server"?Port=7790?MaxPlayers=10?ServerPassword=MyServerPassword?ServerAdminPassword="MyArkAdminPassword"?RCONEnabled=True?RCONPort=32330?ServerCrosshair=true?OverrideStructurePlatformPrevention=true?OverrideOfficialDifficulty=5.0?ShowFloatingDamageText=true?AllowFlyerCarryPvE=true -log -NoBattlEye -WinLiveMaxPlayers=10 -ForceAllowCaveFlyers -ForceRespawnDinos -AllowRaidDinoFeeding=true -ActiveEvent=Summer
asa_server  |[2023.10.31-17.06.59:188][  0]Full Startup: 40.73 seconds
asa_server  |[2023.10.31-17.06.59:188][  0]Number of cores 6
asa_server  |[2023.10.31-17.07.03:329][  2]wp.Runtime.HLOD = "1"
```

### Manager commands
The manager script supports several commands that we highlight below. 

**Server start**
```bash
$ ./manager.sh start
Starting server on port 7790
Server should be up in a few minutes
```

**Server stop**
```bash
$ ./manager.sh stop
Stopping server gracefully...
Waiting 30s for the server to stop
Done
```

**Server restart**
```bash
$ ./manager.sh restart
Stopping server gracefully...
Waiting 30s for the server to stop
Done
Starting server on port 7790
Server should be up in a few minutes
```

**Server status**
```bash
$ ./manager.sh status
Server PID 124
Server listening on port 7790
Server is up
0 players connected
```

**Saving the world**
```bash
$ ./manager.sh saveworld
Saving world...
Success!
```

**Server update**
```bash
$ ./manager.sh update
Updating ARK Ascended Server
Saving world...
Success!
Stopping server gracefully...
Waiting 30s for the server to stop
Done
[  0%] Checking for available updates...
[----] Verifying installation...
Steam Console Client (c) Valve Corporation - version 1698262904
 Update state (0x5) verifying install, progress: 94.34 (8987745741 / 9527248082)
Success! App '2430930' fully installed.
Update completed
Starting server on port 7790
Server should be up in a few minutes
```

**RCON commands**
```bash
$ ./manager.sh rcon "Broadcast Hello World"   
Server received, But no response!!
```

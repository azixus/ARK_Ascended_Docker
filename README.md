# ARK Survival Ascended Docker Server

This project relies on GloriousEggroll's Proton-GE in order to run the ARK Survival Ascended Server inside a docker container under Linux. This allows to run the ASA Windows server binaries on Linux easily.

### Configuration
The main server configuration is done through the [.env](./.env) file. This allows you to change the server name, port, passwords etc.

The server files are stored in a mounted volume in the [ShooterGame](./ShooterGame/) folder. The additional configuration files are found in this folder: [Game.ini](./ShooterGame/Saved/Config/WindowsServer/Game.ini), [GameUserSettings.ini](./ShooterGame/Saved/Config/WindowsServer/GameUserSettings.ini).

Unlike ARK Survival Evolved, only one port must be exposed to the internet, namely the `SERVER_PORT`. It is not necessary to expose the `RCON_PORT`.

### Usage
Start the container by cloning the repo and executing `docker-compose up`:
```bash
$ git clone https://github.com/AziXus/ASA_Server_Docker.git
$ cd ASA_Server_Docker
$ sudo chown -R 1000:1000 ./ShooterGame
$ docker compose up --build -d
```

During the startup of the container, the ASA server is automatically downloaded with `steamcmd`, *but not started*. You can monitor the progress with the following command:
```bash
$ docker compose logs -f
[...]
asa_server  | 2023-10-31T17:05:40.314967005Z Success! App '2430930' fully installed.
```

Once you see `Success!`, the server may be manually started by executing `docker compose exec asa_server manager start`.

### Manager commands
The manager script supports several commands that we highlight below. 

**Server start**
```bash
$ docker compose exec -it asa_server manager start
Starting server on port 7790
Server should be up in a few minutes
```

**Server stop**
```bash
$ docker compose exec asa_server manager stop
Stopping server gracefully...
Waiting 30s for the server to stop
Done
```

**Server restart**
```bash
$ docker compose exec asa_server manager restart
Stopping server gracefully...
Waiting 30s for the server to stop
Done
Starting server on port 7790
Server should be up in a few minutes
```

**Server status**
```bash
$ docker compose exec asa_server manager status
Server PID 124
Server listening on port 7790
Server is up
0 players connected
```

**Saving the world**
```bash
$ docker compose exec asa_server manager saveworld
Saving world...
Success!
```

**Server update**
```bash
$ docker compose exec asa_server manager update
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
$ docker compose exec -it asa_server manager rcon "Broadcast Hello World"   
Server received, But no response!!
```

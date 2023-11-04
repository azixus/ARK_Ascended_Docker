# Based on ghcr.io/parkervcp/steamcmd:proton
# MIT License
#
# Copyright (c) 2020 Matthew Penner
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

FROM        debian:bullseye-slim

RUN         useradd -d /home/arkuser -m arkuser
RUN         mkdir /opt/arkserver

RUN         set -ex; \
            dpkg --add-architecture i386; \
            apt update; \
            apt install -y --no-install-recommends wget iproute2 gnupg2 software-properties-common libntlm0 winbind xvfb xauth libncurses5-dev:i386 libncurses6 dbus libgdiplus lib32gcc-s1; \
            apt install -y alsa-tools libpulse0 pulseaudio libpulse-dev libasound2 libao-common gnutls-bin gnupg locales numactl cabextract curl python3 python3-pip python3-setuptools sudo procps

# Download steamcmd
RUN         set -ex; \
            mkdir -p /opt/steamcmd; \
            cd /opt/steamcmd; \
            curl "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf -

# Download Proton GE
RUN         set -ex; \
            curl -sLOJ "$(curl -s https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest | grep browser_download_url | cut -d\" -f4 | egrep .tar.gz)"; \
            tar -xzf GE-Proton*.tar.gz -C /usr/local/bin/ --strip-components=1; \
            rm GE-Proton*.*

# Proton Fix machine-id
RUN         set -ex; \
            rm -f /etc/machine-id; \
            dbus-uuidgen --ensure=/etc/machine-id; \
            rm /var/lib/dbus/machine-id; \
            dbus-uuidgen --ensure

## install rcon
RUN         set -ex; \
            cd /tmp/; \
            curl -sSL https://github.com/gorcon/rcon-cli/releases/download/v0.10.3/rcon-0.10.3-amd64_linux.tar.gz > rcon.tar.gz; \
            tar xvf rcon.tar.gz; \
            mv rcon-0.10.3-amd64_linux/rcon /usr/local/bin/

# Set permissions
RUN         set -ex; \
            chown -R arkuser:arkuser /opt/arkserver; \
            chown -R arkuser:arkuser /opt/steamcmd

USER        arkuser
WORKDIR     /opt/arkserver/

COPY --chown=arkuser --chmod=755 ./scripts/manager.sh /usr/local/bin/manager
COPY --chown=arkuser --chmod=755 ./scripts/start.sh /opt/start.sh

#on startup enter start.sh script
ENTRYPOINT /opt/start.sh
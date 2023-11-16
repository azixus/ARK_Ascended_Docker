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

FROM        debian:bookworm-slim

# Arguments defining arkuser's uid and gid
ARG         PUID
ARG         PGID

RUN         groupadd -g $PGID arkuser && useradd -d /home/arkuser -u $PUID -g $PGID -m arkuser
RUN         mkdir /opt/arkserver

RUN         set -ex; \
            dpkg --add-architecture i386; \
            apt update; \
            apt install -y --no-install-recommends wget curl jq sudo iproute2 procps software-properties-common dbus lib32gcc-s1 locales locales-all python3-pip

# Set locale
ENV         LC_ALL en_US.UTF-8
ENV         LANG en_US.UTF-8
ENV         LANGUAGE en_US.UTF-8

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

# Install tini
ARG         TINI_VERSION
ADD         https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN         chmod +x /tini

# Set permissions
RUN         set -ex; \
            chown -R arkuser:arkuser /opt/arkserver; \
            chown -R arkuser:arkuser /opt/steamcmd; \
			mkdir -p /opt/proton/compatdata; \
			chown -R arkuser:arkuser /opt/proton

# Install python dependencies
COPY --chown=arkuser --chmod=755 ./scripts/manager/requirements.txt /opt/manager/requirements.txt
RUN         python3 -m pip install -r /opt/manager/requirements.txt --break-system-packages

# Copy manager files
COPY --chown=arkuser --chmod=755 ./scripts/start.sh /opt/start.sh
COPY --chown=arkuser --chmod=755 ./scripts/manager /opt/manager

# Add manager to bin
RUN         ln -s /opt/manager/manager.py /usr/local/bin/manager

USER        arkuser
WORKDIR     /opt/arkserver/

#on startup enter start.sh script
ENTRYPOINT ["/tini", "--", "/opt/start.sh"]

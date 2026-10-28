#!/bin/bash
set -e

if [ -f /var/log/startup_already_done ]; then
    exit 0
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y python3-pip python3-dev git default-libmysqlclient-dev pkg-config
pip3 install --break-system-packages flask google-cloud-storage pymysql

mkdir -p /opt/webserver
cd /opt/webserver

curl -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/attributes/webserver-app" -o /opt/webserver/server.py

cat << 'SERVICE_EOF' > /etc/systemd/system/hw5-webserver.service
[Unit]
Description=CS528 HW5 Flask Web Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/webserver
ExecStart=/usr/bin/python3 /opt/webserver/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable hw5-webserver.service
systemctl start hw5-webserver.service

touch /var/log/startup_already_done

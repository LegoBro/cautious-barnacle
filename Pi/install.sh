
# Install Flask Webserver
sudo apt install python3-flask


cd /etc/systemd/system/

sudo cat <<EOF > bird-gpio-listener.service
[Unit]
Description=Bird Feeder GPIO Listener
After=multi-user.target

[Service]
User=root
WorkingDirectory=/home/pi/birdfeeder
ExecStart=/usr/bin/python3 $HOME/birdfeeder/gpio_listener.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target

EOF

sudo cat <<EOF > bird-web.service
[Unit]
Description=Bird Feeder Web Server
After=network-online.target
Wants=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/birdfeeder
ExecStart=/usr/bin/python3 $HOME/birdfeeder/webserver.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

EOF


sudo systemctl daemon-reexec

systemctl start bird-gpio-listener.service
systemctl enable bird-gpio-listener.service

systemctl start bird-web.service
systemctl enable bird-web.service
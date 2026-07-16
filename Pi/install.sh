
# Install Flask Webserver
sudo apt install python3-flask


cd /etc/systemd/system/

# Detect current user and home directory
USER_NAME=$(whoami)
USER_HOME=$(eval echo "~$USER_NAME")

sudo tee /etc/systemd/system/bird-gpio-listener.service > /dev/null <<EOF
[Unit]
Description=Bird Feeder GPIO Listener
After=multi-user.target

[Service]
User=$USER_NAME
WorkingDirectory=$USER_HOME/birdfeeder
ExecStart=/usr/bin/python3 $USER_HOME/birdfeeder/gpio_listener.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/bird-web.service > /dev/null <<EOF
[Unit]
Description=Bird Feeder Web Server
After=network-online.target
Wants=network-online.target

[Service]
User=$USER_NAME
WorkingDirectory=$USER_HOME/birdfeeder
ExecStart=/usr/bin/python3 $USER_HOME/birdfeeder/webserver.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now bird-gpio-listener.service
sudo systemctl enable --now bird-web.service
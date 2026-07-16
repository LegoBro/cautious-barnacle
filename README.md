# cautious-barnacle
Secret Project

# Setting up the ESP

# Setting up the Raspberry Pi

Image
Install flask

bash <(curl -s https://raw.githubusercontent.com/LegoBro/cautious-barnacle/main/pi_install.sh)


`sudo apt install python3-flask`

setting up a systemd file:
```
cd /etc/systemd/system/
(create file)
sudo systemctl daemon-reexec
systemctl start (service)
systemctl enable (service)
```
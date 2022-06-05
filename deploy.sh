#!/bin/bash
#This assumes spinsave.lol already points to this server's IP
apt update
apt full-upgrade -y
apt install python3-venv python3-pip gunicorn certbot python3-certbot-nginx nginx -y
cd /root/
git clone https://github.com/kylefmohr/SpinSave.lol.git
cd SpinSave.lol/
python3 -m venv .
source bin/activate
pip install -r requirements.txt
mkdir /var/log/gunicorn

cat <<EOF > /etc/systemd/system/gunicorn.service
[Unit]
Description=Gunicorn
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/SpinSave.lol
ExecStart=/root/SpinSave.lol/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/log/gunicorn/app.sock app:app

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl start gunicorn
sudo systemctl enable gunicorn

cat <<EOF > /etc/nginx/sites-available/spinsave
server {
                listen 80;
        server_name spinsave.lol www.spinsave.lol;

        location / {
                include proxy_params;
                proxy_pass http://unix://var/log/gunicorn/app.sock;
        }
}
EOF

ln -s /etc/nginx/sites-available/spinsave /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
certbot --nginx -d spinsave.lol -d www.spinsave.lol

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
ExecStart=/root/SpinSave.lol/bin/gunicorn --access-logfile - --workers 3 --timeout 600 --bind unix:/var/log/gunicorn/app.sock app:app

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
rm /etc/nginx/nginx.conf

#This is just the default nginx.conf with "client_max_body_size 64M;" added to prevent 413 error
cat <<EOF > /etc/nginx/nginx.conf
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
        worker_connections 768;
        # multi_accept on;
}

http {
        client_max_body_size 64M;
        ##
        # Basic Settings
        ##

        sendfile on;
        tcp_nopush on;
        types_hash_max_size 2048;
        # server_tokens off;

        # server_names_hash_bucket_size 64;
        # server_name_in_redirect off;

        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        ##
        # SSL Settings
        ##

        ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3; # Dropping SSLv3, ref: POODLE
        ssl_prefer_server_ciphers on;

        ##
        # Logging Settings
        ##

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        ##
        # Gzip Settings
        ##

        gzip on;

        # gzip_vary on;
        # gzip_proxied any;
        # gzip_comp_level 6;
        # gzip_buffers 16 8k;
        # gzip_http_version 1.1;
        # gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

        ##
        # Virtual Host Configs
        ##

        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
}
EOF

systemctl restart nginx
certbot --nginx -d spinsave.lol -d www.spinsave.lol

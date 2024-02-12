#!/bin/bash

dominio=$1
version=$2
dominio_publico=''

read -r -d '' CONFIG <<EOF
server {
    listen 80;
    server_name $dominio www.$dominio;
    # Redirige HTTP a HTTPS
    return 301 https://\$host\$request_uri;
}
server {
    listen 443 ssl;
    server_name $dominio;
    ssl_certificate /etc/letsencrypt/live/luchosuarez.shop/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/luchosuarez.shop/privkey.pem; # managed by Certbot
    return 301 https://www.$dominio\$request_uri;
}
server {
    listen 443 ssl;
    server_name www.$dominio;
    ssl_certificate /etc/letsencrypt/live/luchosuarez.shop/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/luchosuarez.shop/privkey.pem; # managed by Certbot
    include /etc/nginx/sites-available/aaa-master-aws-sami$version;
}
EOF



if [ $version == 5 ]
then
    echo "$dominio-sami5.conf"
    dominio_publico=$dominio-sami5.conf
    echo "$CONFIG" > $dominio-sami5.conf
elif [ $version == 3 ]
then
    echo "$dominio.conf"
    dominio_publico=$dominio.conf
    echo "$CONFIG" > $dominio.conf
fi

echo $dominio_publico

ln -s /etc/nginx/sites-available/$dominio_publico ../sites-enabled/

sudo nginx -t 
sleep 60

sudo certbot --nginx -d $dominio -d www.$dominio
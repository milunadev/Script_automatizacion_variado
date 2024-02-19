#!/bin/bash

# Directorio donde están los certificados SSL de Let's Encrypt
SSL_DIR="/etc/letsencrypt/live"

# Log file
LOG_FILE="/var/log/nginx/ssl_renewal.log"

# Verifica si el directorio de logs existe, si no, lo crea
if [ ! -d "$(dirname "$LOG_FILE")" ]; then
    mkdir -p "$(dirname "$LOG_FILE")"
fi

# Itera sobre los dominios en el directorio de Let's Encrypt
for domain_dir in $SSL_DIR/*/; do
    domain=$(basename "$domain_dir")
    cert_file="$domain_dir/fullchain.pem"
    key_file="$domain_dir/privkey.pem"

    # Verifica si los archivos de certificado existen
    if [ -f "$cert_file" ] && [ -f "$key_file" ]; then
        expiry_date=$(openssl x509 -noout -enddate -in "$cert_file" | awk -F'=' '{print $2}')
        expiry_epoch=$(date -d "$expiry_date" +%s)
        current_epoch=$(date +%s)
        threshold=$((30 * 24 * 3600)) # Umbral de 30 días antes del vencimiento

        # Si el certificado está a punto de vencer, renovarlo
        if [ $(($expiry_epoch - $current_epoch)) -lt $threshold ]; then
            echo "Renovando certificado para el dominio: $domain" | tee -a "$LOG_FILE"
            # Comando para renovar el certificado usando Certbot
            certbot renew >> "$LOG_FILE" 2>&1
            # Recargar Nginx después de la renovación (puede variar dependiendo de tu sistema)
            systemctl reload nginx
        fi
    else
        echo "No se encontraron archivos de certificado para el dominio: $domain" | tee -a "$LOG_FILE"
    fi
done

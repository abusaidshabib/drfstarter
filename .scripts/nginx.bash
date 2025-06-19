#!/bin/bash

source /root/carshowroomdrf/.env.dev

# === Target Path ===
NGINX_CONF="/etc/nginx/sites-available/${DJ_PROJECT_NAME}"

# === Create NGINX Config ===
sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name ${DJ_URL};

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias ${DJ_APP_DIR}/staticfiles/;
    }

    location /media/ {
        alias ${DJ_APP_DIR}/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/${DJ_PROJECT_NAME}.sock;
    }
}
EOF

echo "$NGINX_CONF created successfully."

# === Suggest symbolic link and reload NGINX ===
echo "To enable this site:"
echo "  sudo ln -s /etc/nginx/sites-available/${DJ_PROJECT_NAME} /etc/nginx/sites-enabled/${DJ_PROJECT_NAME}"
echo "  sudo nginx -t && sudo systemctl reload nginx"

# Auto-enable
if [ ! -e "/etc/nginx/sites-enabled/${DJ_PROJECT_NAME}" ]; then
    echo "🔗 Enabling Nginx site..."
    sudo ln -s "/etc/nginx/sites-available/${DJ_PROJECT_NAME}" "/etc/nginx/sites-enabled/${DJ_PROJECT_NAME}"
fi

# Test and reload
echo "🚦 Testing Nginx config..."
sudo nginx -t
if [ $? -eq 0 ]; then
    echo "♻️ Reloading Nginx..."
    sudo systemctl reload nginx
else
    echo "❌ Nginx config test failed. Not reloading."
fi


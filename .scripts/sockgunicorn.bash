#!/bin/bash

# Load environment variables
source /root/carshowroomdrf/.env.dev

# === Validations ===
: "${DJ_PROJECT_NAME:?Project name not set}"
: "${DJ_APP_DIR:?App directory not set}"
: "${DJ_VENV_NAME:?Virtualenv name not set}"
: "${HOST_USERNAME:?Host user not set}"

# === Paths ===
SOCKET_FILE="/etc/systemd/system/${DJ_PROJECT_NAME}.socket"
SERVICE_FILE="/etc/systemd/system/${DJ_PROJECT_NAME}.service"

# === Create Gunicorn Socket ===
sudo tee "$SOCKET_FILE" > /dev/null <<EOF
[Unit]
Description=${DJ_PROJECT_NAME} socket

[Socket]
ListenStream=/run/${DJ_PROJECT_NAME}.sock

[Install]
WantedBy=sockets.target
EOF

echo "[✓] Socket file created at $SOCKET_FILE"

# === Create Gunicorn Service ===
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=${DJ_PROJECT_NAME} service
Requires=${DJ_PROJECT_NAME}.socket
After=network.target

[Service]
User=${HOST_USERNAME}
Group=www-data
WorkingDirectory=${DJ_APP_DIR}
ExecStart=${DJ_APP_DIR}/${DJ_VENV_NAME}/bin/gunicorn \\
          --access-logfile - \\
          --workers 3 \\
          --bind unix:/run/${DJ_PROJECT_NAME}.sock \\
          ${DJ_WSGI}.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

echo "[✓] Service file created at $SERVICE_FILE"

# === Reload, Enable & Start Services ===
sudo systemctl daemon-reload
sudo systemctl enable "${DJ_PROJECT_NAME}.socket"
sudo systemctl start "${DJ_PROJECT_NAME}.socket"
sudo systemctl enable "${DJ_PROJECT_NAME}.service"
sudo systemctl start "${DJ_PROJECT_NAME}.service"

echo "[✓] Gunicorn socket and service started and enabled"

# === Check Status ===
echo "-----------------------------"
sudo systemctl status "${DJ_PROJECT_NAME}.socket" --no-pager
echo "-----------------------------"
sudo systemctl status "${DJ_PROJECT_NAME}.service" --no-pager

# === Test Socket (Optional) ===
echo "-----------------------------"
echo "[i] Checking socket file..."
file "/run/${DJ_PROJECT_NAME}.sock"

echo "-----------------------------"
echo "[i] Curl test to socket..."
curl --unix-socket "/run/${DJ_PROJECT_NAME}.sock" localhost || echo "Curl may fail if app is not yet responding."

# === Logs ===
echo "-----------------------------"
echo "[i] Logs:"
sudo journalctl -u "${DJ_PROJECT_NAME}.service" -n 20 --no-pager

echo "✅ Setup completed."

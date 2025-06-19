#!/bin/bash
source /root/carshowroomdrf/.env.dev

echo "Creating Database......";

# Run PostgreSQL commands as the postgres user
sudo -u postgres psql -p $DJ_DB_PORT <<EOF
-- Create database and user
CREATE DATABASE $DJ_DB_NAME;
CREATE USER $DJ_DB_USER WITH PASSWORD '$DJ_DB_PASSWORD';

-- Grant privileges and configure role
GRANT ALL PRIVILEGES ON DATABASE $DJ_DB_NAME TO $DJ_DB_USER;
ALTER ROLE $DJ_DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DJ_DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DJ_DB_USER SET timezone TO 'UTC';

-- Set schema privileges
\connect $DJ_DB_NAME
GRANT USAGE ON SCHEMA public TO $DJ_DB_USER;
GRANT CREATE ON SCHEMA public TO $DJ_DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DJ_DB_USER;
EOF

echo "✅ Database Created"

# Navigate to app directory
cd $DJ_APP_DIR || { echo "❌ Directory $DJ_APP_DIR not found"; exit 1; }

echo "📦 Creating virtual environment: $DJ_VENV_NAME"
python -m venv "$DJ_APP_DIR/$DJ_VENV_NAME"
echo "✅ Virtual environment created"

# Activate virtual environment
echo "⚙️ Activating virtual environment"
source "$DJ_APP_DIR/$DJ_VENV_NAME/bin/activate"

# Install dependencies
echo "📦 Installing dependencies from requirements.txt"
pip install --upgrade pip
pip install django gunicorn psycopg2-binary
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Run migrations
echo "📂 Running Django migrations"
python manage.py makemigrations
python manage.py migrate
echo "✅ Migrations complete"

echo "🎉 Setup complete!"

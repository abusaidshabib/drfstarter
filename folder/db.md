# access db using cmd
psql -U postgres

# Create Database with password
CREATE USER carshowroom WITH PASSWORD '123456';
CREATE DATABASE carshowroom OWNER carshowroom;
GRANT ALL PRIVILEGES ON DATABASE carshowroom TO carshowroom;
\q
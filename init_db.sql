CREATE USER warehouse WITH PASSWORD 'warehouse';
CREATE DATABASE warehouse_db OWNER warehouse;
GRANT ALL PRIVILEGES ON DATABASE warehouse_db TO warehouse;

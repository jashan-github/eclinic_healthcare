-- Grant permissions so pgAdmin can see tables
-- Run this as eclinic_user (if it has ALTER privileges) or as superuser

-- Grant schema usage to everyone
GRANT USAGE ON SCHEMA public TO PUBLIC;

-- Grant privileges on all existing tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO PUBLIC;

-- Grant privileges on all sequences
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO PUBLIC;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO PUBLIC;


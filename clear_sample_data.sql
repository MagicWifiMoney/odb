-- Clear Sample Data from ODB Database
-- Run this in your Supabase SQL Editor

-- 1. Clear all opportunities (sample data)
DELETE FROM opportunities;

-- 2. Clear all data sources (sample entries)
DELETE FROM data_sources;

-- 3. Clear all sync logs (sample entries)
DELETE FROM sync_logs;

-- 4. Reset auto-increment sequences (optional, for clean IDs)
ALTER SEQUENCE IF EXISTS opportunities_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS data_sources_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS sync_logs_id_seq RESTART WITH 1;

-- 5. Verify data is cleared
SELECT 'opportunities' as table_name, COUNT(*) as record_count FROM opportunities
UNION ALL
SELECT 'data_sources' as table_name, COUNT(*) as record_count FROM data_sources
UNION ALL
SELECT 'sync_logs' as table_name, COUNT(*) as record_count FROM sync_logs; 
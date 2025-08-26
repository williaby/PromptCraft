-- PostgreSQL Validation Queries
-- Run these after migration to validate data integrity

-- Validation for ab_testing database
-- Expected: 90 rows
SELECT 'ab_experiments' as table_name, COUNT(*) as actual_count, 90 as expected_count,
       CASE WHEN COUNT(*) = 90 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM ab_experiments;

-- Expected: 2 rows
SELECT 'ab_user_assignments' as table_name, COUNT(*) as actual_count, 2 as expected_count,
       CASE WHEN COUNT(*) = 2 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM ab_user_assignments;

-- Expected: 0 rows
SELECT 'ab_metric_events' as table_name, COUNT(*) as actual_count, 0 as expected_count,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM ab_metric_events;

-- Validation for analytics database
-- Expected: 12808 rows
SELECT 'usage_events' as table_name, COUNT(*) as actual_count, 12808 as expected_count,
       CASE WHEN COUNT(*) = 12808 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM usage_events;

-- Expected: 1 rows
SELECT 'sqlite_sequence' as table_name, COUNT(*) as actual_count, 1 as expected_count,
       CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM sqlite_sequence;

-- Expected: 0 rows
SELECT 'session_metrics' as table_name, COUNT(*) as actual_count, 0 as expected_count,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM session_metrics;

-- Validation for metrics database
-- Expected: 0 rows
SELECT 'metric_points' as table_name, COUNT(*) as actual_count, 0 as expected_count,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM metric_points;

-- Expected: 0 rows
SELECT 'sqlite_sequence' as table_name, COUNT(*) as actual_count, 0 as expected_count,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM sqlite_sequence;

-- Expected: 0 rows
SELECT 'aggregated_metrics' as table_name, COUNT(*) as actual_count, 0 as expected_count,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM aggregated_metrics;

-- Expected: 0 rows
SELECT 'validation_results' as table_name, COUNT(*) as actual_count, 0 as expected_count,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM validation_results;

-- Validation for security_events database
-- Expected: 0 rows
SELECT 'security_events' as table_name, COUNT(*) as actual_count, 0 as expected_count,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as validation_status
FROM security_events;

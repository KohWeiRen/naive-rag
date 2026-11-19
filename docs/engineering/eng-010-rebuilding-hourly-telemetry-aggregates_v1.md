# Rebuilding hourly telemetry aggregates

Company: Ternwell Systems
Document ID: ENG-010
Type: Runbook
Owner: Data Engineering
Issued: 2026-09-28
Status: Current

Select a tenant, region, and bounded UTC time window. Confirm that the raw readings are still within the 90-day retention window. Run the dry-run planner and save the predicted row count. Acquire the per-tenant aggregation lock before replacing any bucket.

## Validation

Compare the first and last bucket with raw sample counts and verify that observed_at controls the bucket. Roll back through the previous snapshot if an hour is missing or record counts exceed the expected range. The reconciliation report includes affected bucket IDs and the planned next run.

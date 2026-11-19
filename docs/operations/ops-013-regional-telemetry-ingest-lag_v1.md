# Regional telemetry ingest lag

Company: Ternwell Systems
Document ID: OPS-013
Type: Runbook
Owner: Site Reliability
Issued: 2026-10-11
Status: Current

Look for increased received_at minus observed_at across multiple tenants. Separate gateway clock drift from a regional queue delay by comparing received_at with worker processing time. Validate a recent synthetic reading using the same region endpoint as the affected tenant.

## Response

For an isolated site, contact Fleet Operations and check its uplink. For a region-wide delay, inspect the ingest worker, recent deploys, and database write latency. Record backlog recovery separately from incoming batch acceptance.

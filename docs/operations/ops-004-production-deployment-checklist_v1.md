# Production deployment checklist

Company: Ternwell Systems
Document ID: OPS-004
Type: Checklist
Owner: Site Reliability
Issued: 2026-10-07
Status: Current

## Before the change

Link the change request and verify the rollback action. Confirm the release is compatible with existing event schemas. Review database migration locks if the release writes to a shared table. Use a staffed window for elevated-risk changes.

## During the change

Deploy to a canary tenant. Check ingest acceptance, query latency, delivery queue age, and error rate for 15 minutes. Compare against a control tenant in the same region. A failing canary stops the rollout and starts the rollback review.

## After the change

Verify the active version in each region and the error budget dashboard. Record metrics and any deviations in the change ticket. Leave the incident contact in the release channel until the final observation window closes.

# Transferring a gateway between sites

Company: Ternwell Systems
Document ID: ENG-016
Type: Runbook
Owner: Fleet Engineering
Issued: 2026-09-26
Status: Current

Before transferring, confirm the destination belongs to the same tenant and region. Export current assignment metadata and record the time of the last accepted reading. Remove the gateway from the old site after the last scheduled shipment closes.

## Re-enrollment

Generate a new registration code, attach the gateway to the destination site, and verify one signed telemetry batch. Registration codes expire after 24 hours. Replace any expired code with a new one and keep the old request as part of the audit trail.

## Cross-tenant requests

Escalate a cross-tenant transfer to Fleet Engineering and Customer Enablement. Historical readings stay with the original tenant under the retention policy.

# Handling telemetry duplicates

Company: Ternwell Systems
Document ID: ENG-013
Type: Design note
Owner: Data Engineering
Issued: 2026-10-02
Status: Current

The natural deduplication key is tenant_id, device_id, and event_id. A retry with the same key and payload is acknowledged as a duplicate and does not create an additional row. A repeat key with a different payload is recorded as a conflict for investigation.

## Reasons for duplicates

Gateways retry after timeouts and may not know whether the server accepted the first attempt. Restored workers can also process messages already accepted before a restart. Both paths should converge on the same durable record.

## Diagnostics

Track duplicate counters by tenant, firmware, and region. If the duplicate rate grows without corresponding timeouts, compare generated event IDs across firmware versions.

# Fleet Console gateway health panel

Company: Ternwell Systems
Document ID: PRD-001
Type: Product requirements
Owner: Product
Issued: 2026-10-05
Status: Current

## User problem

Installers need to distinguish between a reachable gateway and a sensor that has stopped sending samples. The current online indicator can stay green while a probe is unplugged. Support frequently asks customers to compare timestamps manually.

## Scope

Show last heartbeat and last accepted reading separately for each gateway. A stale-sample hint appears after twice the configured sample interval. Operators can expand the hint for suggested checks. The dashboard records the user's timezone while the diagnostic drawer exposes UTC.

## Acceptance

During an uplink outage both timestamps can age. During a probe failure the heartbeat stays recent. During planned maintenance the stale hint remains visible but the panel adds a maintenance label. Test the feature in the Bracken Dairy pilot before enabling it for all tenants. ENG-017 records the measurement plan.

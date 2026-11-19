# Responding to a webhook delivery backlog

Company: Ternwell Systems
Document ID: OPS-002
Type: Runbook
Owner: Site Reliability
Issued: 2026-10-02
Status: Current

## Trigger

Page the delivery on-call when oldest pending delivery age exceeds five minutes for 10 consecutive minutes. Compare the age and depth by region, endpoint, and response code. Check ingest lag separately. A healthy ingestion queue does not confirm timely webhook delivery.

## Investigation

Inspect worker concurrency, retry volume, and request latency. Group failures by endpoint. If one endpoint is returning widespread 429, throttle that endpoint before scaling all workers. For a recent dispatcher rollout, compare canary and control and capture the release ID. Use the current log search to find a delayed delivery ID and confirm whether its last request received an acknowledgment.

## Mitigation

Pause further rollout if queue age increased on the canary. Restore the previous dispatcher configuration when it is known healthy. Preserve delivery IDs during replay and confirm the receiver's deduplication behavior using ENG-004. If a customer asks to replay historical events, coordinate scope with Support.

## Verification

Check queue age below two minutes for 15 minutes, then validate one synthetic webhook in each affected region. Compare the count of unacknowledged jobs with the pending queue. Close the incident only after the commander has confirmed residual impact and set an owner for any delayed deliveries.

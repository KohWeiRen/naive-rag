# October core telemetry restore exercise

Company: Ternwell Systems
Document ID: OPS-014
Type: Exercise report
Owner: Site Reliability
Issued: 2026-10-29
Status: Current

The team restored an isolated Singapore telemetry copy from the 07:50 UTC recovery point on 29 October. The exercise began at 08:00. Synthetic writes and reads were verified at 10:17. Time to verified service was two hours and 17 minutes. The observed recovery gap was 10 minutes.

## Observations

The permission reconciliation checklist was accurate, but the synthetic alert test depended on a stale receiver endpoint. The observer replaced the endpoint in the sandbox and verified delivery at 10:17. Add a receiver health check to the preparation phase before the next exercise.

## Actions

Samir Teo will update the drill checklist by 12 November. The service owner will compare the November exercise against the same RTO and RPO targets in OPS-006.

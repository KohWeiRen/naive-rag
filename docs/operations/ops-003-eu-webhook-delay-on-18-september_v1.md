# EU webhook delay on 18 September

Company: Ternwell Systems
Document ID: OPS-003
Type: Postmortem
Owner: Site Reliability
Issued: 2026-09-23
Status: Current

## Summary

Incident TW-INC-026 delayed EU webhook delivery for 38 tenants. Eleven tenants experienced a delay of more than 15 minutes. Ingest and chart updates stayed healthy. The team found no lost telemetry or webhook jobs during reconciliation. The incident ran from 02:14 to 03:22 UTC on 18 September 2026.

## Timeline

At 02:14, the EU delivery queue age began increasing after a dispatcher configuration rollout. At 02:21, the on-call acknowledged the queue age alert. At 02:29, the commander declared S2 and Support posted an advisory. At 02:42, the team restored the prior dispatcher configuration. At 03:03, queue age dropped below two minutes. At 03:22, on-call confirmed the backlog had cleared and closed customer impact.

## Cause

The rollout lowered the effective per-worker concurrency limit for EU webhook jobs. The queue accepted new jobs at the normal rate while the dispatcher processed fewer jobs in parallel. Synthetic checks confirmed delivery eventually but did not alert when it took several minutes. Device readings remained separate from the delivery worker.

## Decisions during response

The technical lead chose to restore the previous configuration before manually replaying jobs. Delivery IDs remained unchanged. The team let the existing retry loop drain the backlog and compared final acknowledgment counts with the queued jobs. Support told affected customers to use Fleet Console for current alerts while webhook messages caught up.

## Follow-up

Site Reliability will gate deployments on oldest-job age by 2 October. Platform Engineering will assert the concurrency limit in deployment smoke checks by 9 October. Support will update the EU incident template by 30 September. OPS-011 records the release gate change and OPS-015 records the follow-up review.

## Impact details

The affected cohort contained tenants with EU webhook endpoints that were active during the incident window. A tenant was counted once even if more than one endpoint was delayed. Support reconciled the cohort against dispatcher logs and customer cases. The 11 tenants in the greater-than-15-minute group are a subset of the 38 affected tenants. The incident record lists the affected delivery IDs in restricted evidence rather than reproducing them here.

No Singapore tenants were included. The raw observation store received accepted events during the rollout. Fleet Console could still display current readings and alert records. Notification lag made some downstream workflows appear stale until the receiver handled the delayed job. Support treated delivery delay as distinct from missing telemetry when communicating scope.

## Investigative notes

At first, the depth panel suggested a single receiver was holding jobs. Grouping by endpoint showed growth across unrelated receivers, and the latest response codes were spread across successful responses and routine retries. The deployment metadata showed that the growth began during the dispatcher canary. The duty engineer compared the prior and new configuration and found that a default value differed by region.

The team avoided forcing historical replay during recovery. That could have increased queue pressure and made it harder to tell whether an original attempt was still in flight. The restored worker configuration let ordinary retry scheduling continue. One synthetic endpoint received a signed test message before the team proceeded to reconciliation.

## Follow-up verification plan

The on-call dashboard now separates queue age from depth and shows the configured worker concurrency beside both. The next change exercise should introduce a slow endpoint under sandbox load, verify that it stays isolated, and watch new jobs from a healthy tenant progress. Another exercise should simulate a worker restart immediately after a receiver acknowledges a request. Product and Support can use both exercises to review how the delivery history represents a retry.

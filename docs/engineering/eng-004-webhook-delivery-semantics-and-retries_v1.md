# Webhook delivery semantics and retries

Company: Ternwell Systems
Document ID: ENG-004
Type: Technical reference
Owner: Platform Engineering
Issued: 2026-10-03
Status: Current

## Delivery contract

Wayline webhook delivery is at least once. Receivers acknowledge accepted requests with HTTP 2xx and must deduplicate using the delivery ID. The dispatcher generates a delivery ID for the original alert endpoint pair and retains it during every automatic retry. Replays requested through support preserve the delivery ID while incrementing the attempt counter. A receiver should record the ID before running an operation that creates an external side effect.

## Retry schedule

Retryable status codes include 408, 429, and 5xx, plus connection and TLS timeouts. Wait 1, 5, 15, and 60 minutes after successive failures, then retry every 4 hours until 24 hours after the original attempt. Use Retry-After when present on 429, subject to the 24-hour ceiling. Other 4xx responses are terminal and are recorded in the delivery log for support review.

## Ordering and backpressure

Different endpoint jobs run concurrently. Delivery order can differ from observation order after a retry. Order readings by observed_at when the application needs a historical sequence. Do not queue all tenants behind a slow consumer. The worker limits concurrency per endpoint and returns excess jobs to the regional queue without changing their delivery IDs.

## Signature verification

Read the raw body before parsing. Verify the signature and timestamp according to SEC-008. Use a small skew allowance and verify both keys during the scheduled rotation overlap. Treat signature failures as terminal for the request and preserve delivery ID and timestamp for support.

## Operating the queue

OPS-002 describes the backlog response. A sustained rise in oldest-message age indicates the queue is not draining within its objective. Compare affected endpoints before replaying any job. If the original attempt was acknowledged, resending can trigger duplicate downstream actions even if Wayline's queue appears healthy.

## Example

A receiver returns 503 at 12:00 UTC. The first retry can run at 12:01. If that attempt returns 429 with Retry-After of 120 seconds, the dispatcher respects the requested delay and records the response for the endpoint. The customer's idempotency key remains the delivery ID from the original attempt.

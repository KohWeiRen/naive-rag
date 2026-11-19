# Interpreting missing readings in Fleet Console

Company: Ternwell Systems
Document ID: CS-010
Type: Guide
Owner: Customer Enablement
Issued: 2026-10-24
Status: Current

Open the device page and compare the last heartbeat with the last accepted reading. A recent heartbeat with stale samples can indicate a probe issue. A stale heartbeat and stale readings suggest a gateway or uplink problem.

## Check the timeline

Look for recent device maintenance or a link change. Compare observed_at and received_at after reconnect. Queued readings can appear later while retaining their original timestamps. For site-wide issues, include one affected device and one healthy comparison device in the support case.

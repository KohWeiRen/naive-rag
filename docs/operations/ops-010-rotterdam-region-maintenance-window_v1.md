# Rotterdam region maintenance window

Company: Ternwell Systems
Document ID: OPS-010
Type: Checklist
Owner: Site Reliability
Issued: 2026-10-13
Status: Current

Verify the maintenance ticket, current component health, and the escalation contact. Notify Customer Enablement three working days ahead for planned work that affects a customer tenant. Stage a synthetic device and webhook receiver before beginning.

## During maintenance

Watch queue depth, oldest job, and last accepted reading. Pause the next change if a region cannot complete a synthetic read and write. The incident commander may reopen the window after the underlying issue is resolved.

## Closure

Record start and end timestamps in UTC, customer-facing impact, and follow-up ownership. Attach the final dashboard screenshot to the change record.

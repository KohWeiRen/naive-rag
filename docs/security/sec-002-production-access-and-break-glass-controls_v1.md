# Production access and break-glass controls

Company: Ternwell Systems
Document ID: SEC-002
Type: Policy
Owner: Security
Issued: 2026-10-05
Status: Current

## Standard access

Engineers enter production through role-based, time-limited grants. A request includes environment, service, intended operation, and linked ticket. Read-only grants expire after eight hours. Write grants expire after two hours and require approval from the service owner or duty incident commander.

## Break glass

An active incident with customer impact may justify emergency access. The incident commander records why normal access is unavailable, requests the narrowest emergency role, and ends the grant as soon as mitigation completes. Security reviews emergency grants on the next working day.

## Evidence

All grant events are sent to the audit log. Record the ticket ID, grant ID, scope, actor, and time window. Avoid pasting unredacted command output into incident notes. Remove elevated access after handover or role transfer.

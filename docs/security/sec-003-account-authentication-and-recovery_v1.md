# Account authentication and recovery

Company: Ternwell Systems
Document ID: SEC-003
Type: Standard
Owner: Security
Issued: 2026-08-14
Status: Current

Passkeys are the default MFA method for staff accounts. Keep a backup enrolled on an approved device. The help desk verifies identity through the recorded recovery method before replacing a factor. Corporate login links are sent from the identity portal or internal help desk.

## Service accounts

Use workload identity where supported. Bind each identity to one service and environment. Service identity owners review scopes during deployment changes and at least quarterly. Report keys found in chat, notebooks, or commit history under SEC-007.

## Response

If a device or factor is lost, ask IT to revoke the relevant session and begin recovery. The help desk opens a restricted case, records verification, and confirms when the new factor is active.

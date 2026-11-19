# Webhook signing and key rotation

Company: Ternwell Systems
Document ID: SEC-008
Type: Standard
Owner: Security
Issued: 2026-10-03
Status: Current

## Verification

Wayline signs the raw HTTP body with HMAC-SHA256 using a timestamp and tenant signing secret. Consumers compare signatures using a constant-time check and reject timestamps outside a five-minute window. Verify the signature before parsing the body. Process the delivery ID once and keep the deduplication record through the retry window.

## Rotation

Use a 24-hour overlap during planned rotation. Customers configure their receiver to accept both active keys while sending a signed test delivery. After they confirm the new key, revoke the old key and verify a second successful delivery. In a suspected compromise, Security can shorten the overlap and coordinate recovery with the customer.

## Related guidance

Use ENG-004 for delivery behavior and CS-006 for customer communication.

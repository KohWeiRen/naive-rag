# Tenant API authentication and pagination

Company: Ternwell Systems
Document ID: ENG-002
Type: API reference
Owner: Platform Engineering
Issued: 2026-10-01
Status: Current

## Authentication

API requests present a tenant credential in the Authorization bearer header. Create a credential through Fleet Console using a Tenant Admin account. Select a region and only the scopes needed. Never place a credential in a query parameter or customer ticket. A revoked credential stops accepting new requests after the current authorization cache window, which is normally under two minutes.

## Pagination

List endpoints accept limit and cursor. The default page size is 100 and the maximum is 250. Treat cursors as opaque. Continue until next_cursor is absent. A client that changes its filters or sort order starts again without the old cursor.

## Errors

A 401 response indicates missing or invalid credentials. A 403 indicates the credential is valid but lacks permission. For 429, honor Retry-After and retain the cursor until the same request succeeds. ENG-008 defines quota details.

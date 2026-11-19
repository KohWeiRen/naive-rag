# Local integration test environment

Company: Ternwell Systems
Document ID: ENG-011
Type: Engineering guide
Owner: Platform Engineering
Issued: 2026-09-25
Status: Current

Run the sandbox stack with the provided integration configuration. Use a synthetic tenant and fixtures from the test-data repository. Mock outbound email and webhook delivery unless you are testing an isolated receiver.

## Test scenarios

Exercise duplicate event IDs, late readings, 429 handling, and an invalid signature. A test that uses a shared sandbox should clean up only the test tenant it created. Set the clock explicitly when testing retry intervals and five-minute signature validity.

## Failure output

Print request IDs and test tenant names for debugging. Redact credentials and real production identifiers. Record failures as isolated issues with steps to reproduce.

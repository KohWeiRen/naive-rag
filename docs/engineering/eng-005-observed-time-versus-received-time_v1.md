# Observed time versus received time

Company: Ternwell Systems
Document ID: ENG-005
Type: Design note
Owner: Data Engineering
Issued: 2026-08-24
Status: Current

Observed_at is the device's timestamp for the physical reading. Received_at records when ingest accepted it. The operator dashboard shows both times for diagnostics. Charts group by observed_at, while ingestion lag is computed as received_at minus observed_at.

## Clock drift

If a reading appears more than five minutes in the future, preserve the raw value, mark the record as clock_suspect, and exclude it from real-time threshold evaluation. Recheck the gateway clock after firmware updates. Late readings are valid and should be retained when they fall within the raw telemetry window.

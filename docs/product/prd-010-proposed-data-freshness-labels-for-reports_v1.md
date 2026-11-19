# Proposed data freshness labels for reports

Company: Ternwell Systems
Document ID: PRD-010
Type: Product memo
Owner: Product
Issued: 2026-10-30
Status: Current

Label reports with the latest accepted sample time and the time the export completed. A current completion timestamp does not imply that every gateway contributed a recent sample. Customers need both values to determine whether a report reflects the full shipment window.

## Edge cases

For an empty report, display the selected window and the message No accepted samples for this interval. For a report with partial delayed data, keep the job successful and link to site diagnostics. Product will review label wording with Customer Enablement before updating the export template.

# Temperature excursion alert behavior

Company: Ternwell Systems
Document ID: PRD-004
Type: Specification
Owner: Product
Issued: 2026-09-29
Status: Current

An excursion starts when two consecutive accepted samples are outside the configured band. The evaluator uses observed_at and ignores readings marked clock_suspect for real-time threshold evaluation. Recovery is shown after three consecutive in-band samples. The earliest accepted out-of-band reading becomes the alert start time.

## Notifications

Use the tenant's configured notification target. Repeated out-of-band samples update the excursion record without creating a new alert. A webhook receiver can see repeated attempts for the same delivery ID if acknowledgments fail.

## Example

A profile samples every five minutes. Readings at 10:05 and 10:10 UTC cross the threshold. One alert is opened at the second accepted sample and shows an excursion start of 10:05.

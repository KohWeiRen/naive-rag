# Saved report templates

Company: Ternwell Systems
Document ID: PRD-006
Type: Product requirements
Owner: Product
Issued: 2026-10-12
Status: Current

## User problem

Operators export the same site and date filters each Monday. They want to reuse a report definition without copying or reuploading the previous export.

## Proposal

A report template stores selected sites, metrics, display timezone, and a relative date range. It contains no reading values. The user selects Run to create a separate export job. Permissions are rechecked when a shared template runs.

## Acceptance

A manager can share a template with an operations role. An operator who loses access to one site sees a permission error for that site and may rerun with an authorized subset. The job follows the same concurrency quota as manual exports in ENG-008.

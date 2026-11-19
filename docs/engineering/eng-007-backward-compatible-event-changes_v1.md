# Backward-compatible event changes

Company: Ternwell Systems
Document ID: ENG-007
Type: Standard
Owner: Platform Engineering
Issued: 2026-09-18
Status: Current

## Change process

Add optional fields before making producers emit them. Consumers should accept additional fields and must reject a missing required field with a clear validation result. Changes to a field's meaning or type require a new schema revision.

## Migration

Deploy readers that accept both schema revisions. Turn on writers for a sandbox tenant, compare accepted counts and duplicate rates, and ramp through canary tenants. Leave the compatibility reader enabled for at least 30 days and announce the removal date in the engineering release channel.

## Active transition

The telemetry.v2 field sample_time remains an alias for observed_at through 30 November 2026. Data Engineering monitors use by firmware version and reports any device cohort that cannot switch before removal.

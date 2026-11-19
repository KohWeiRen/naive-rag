# Reducing stale device status

Company: Ternwell Systems
Document ID: ENG-017
Type: Engineering memo
Owner: Data Engineering
Issued: 2026-10-19
Status: Current

A device can look connected even when a sensor stopped reporting. The existing dashboard shows the last gateway heartbeat, which confirms connectivity rather than sensor health. The proposed indicator shows last accepted sample time and flags missing samples after twice the configured interval.

## Trial

Apply the new indicator to the Bracken Dairy test tenant and compare support cases for three weeks. Keep the gateway status visible for installers. Product will review alert wording before extending the indicator to the default view.

## Success measures

Measure support requests tagged stale status, cases resolved without Engineering, and false positives during known maintenance windows.

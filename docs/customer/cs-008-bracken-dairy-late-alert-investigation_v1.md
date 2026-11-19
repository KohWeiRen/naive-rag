# Bracken Dairy late alert investigation

Company: Ternwell Systems
Document ID: CS-008
Type: Case note
Owner: Customer Enablement
Issued: 2026-09-25
Status: Current

Case CSQ-593 concerns alerts from Bay 4 that arrived later than the operator expected. The EU dispatcher showed no queue age increase. Fleet Engineering found that the gateway was offline for 12 minutes and then backfilled readings. The accepted samples retained their original observed_at values.

## Customer reply

Fleet Console shows both sample time and receipt time. The chart can show an event earlier than the time the gateway reconnected. The site will check the cellular antenna and review the last accepted sample indicator in the pilot described by ENG-017.

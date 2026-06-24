# CommerceMind VoiceCare AI — Backend Schema
### Data Model & Auth Architecture

Items neither source document actually specifies are marked 📌 — open decisions, not facts.

---

15 tables across three clusters.

### Cluster: Customer & Catalog

**users**
| Field | Description |
|---|---|
| user_id | Unique customer ID |
| name | Customer name |
| phone | Customer phone number |
| city | Customer city |
| preferred_language | Hindi / Malayalam / Tamil / English / etc. |
| customer_segment | Regular / Premium / New |
| created_at | Account creation date |

**products** 📌 *(fields not specified in source — suggested starting point)*
product_id, name, category, price, sku, created_at

**orders** 📌 *(suggested)*
order_id, user_id (FK → users), order_date, status (Placed/Shipped/Delivered/Cancelled), total_amount, created_at

**order_items** 📌 *(suggested)*
order_item_id, order_id (FK → orders), product_id (FK → products), quantity, price_at_purchase

### Cluster: Fulfillment & Payments

**shipments** 📌 *(suggested)*
shipment_id, order_id (FK → orders), courier_partner, shipment_status, expected_delivery_date, actual_delivery_date, tracking_number

**returns** 📌 *(suggested)*
return_id, order_id (FK → orders), reason, status (Requested/Approved/Rejected/Completed), requested_at, eligibility_window_days

**refunds** 📌 *(suggested)*
refund_id, return_id (FK → returns, nullable for non-return refunds e.g. payment failure), amount, status (Pending/Approved/Credited), credited_at

**payments** 📌 *(suggested)*
payment_id, order_id (FK → orders), amount, status (Success/Failed/Refunded), payment_method, transaction_date

### Cluster: Support & AI

**voice_sessions**
| Field | Description |
|---|---|
| session_id | Unique voice session ID |
| user_id | Customer ID |
| language_detected | Language detected from speech |
| audio_file_path | Stored audio file path (optional) |
| transcript_original | Original transcript |
| transcript_english | English translation (optional) |
| started_at | Session start time |
| ended_at | Session end time |

**support_tickets**
| Field | Description |
|---|---|
| ticket_id | Unique ticket ID |
| user_id | Customer ID |
| order_id | Related order |
| ticket_type | Delay / Refund / Return / Payment / Complaint |
| priority | Low / Medium / High / Critical |
| status | Open / In Progress / Resolved / Escalated |
| language | Customer language |
| sentiment | Neutral / Negative / Angry |
| created_at | Ticket creation time |
| resolved_at | Resolution time |

**support_messages**
| Field | Description |
|---|---|
| message_id | Unique message ID |
| ticket_id | Linked ticket |
| session_id | Linked voice session |
| sender_type | Customer / AI / Human |
| message_text | Transcript or response text |
| language | Message language |
| timestamp | Message time |

**support_resolutions**
| Field | Description |
|---|---|
| resolution_id | Unique resolution ID |
| ticket_id | Linked ticket |
| recommended_action | Inform / Refund / Replace / Escalate / Reject |
| policy_reference | Retrieved policy section |
| final_response_text | Customer-facing response |
| final_response_audio | TTS audio path (optional) |
| internal_note | Staff-facing note |
| confidence_score | AI confidence |

**policy_documents** 📌 *(suggested)*
policy_id, title, category (Shipping/Return/Refund/Cancellation/Replacement/Warranty/Compensation/Escalation SOP/Payment Failure SOP), content, embedding_ref (Chroma vector id), version, updated_at

**escalation_rules** 📌 *(suggested)*
rule_id, condition_description, trigger_type, priority_level, created_at — the original concept's candidate trigger pool was High-value order / Angry customer / Refund delayed beyond SLA / Payment deducted but order not created / Repeated complaint / Damaged expensive product / Policy exception required / Low AI confidence (8 conditions); the finalized blueprint compresses the escalation check to exactly 5 deterministic rule conditions, but doesn't say which 5 — narrow this list down before Week 1.

**customer_sentiment** 📌 *(suggested)*
sentiment_id, ticket_id (FK → support_tickets), sentiment_label (Calm/Confused/Dissatisfied/Angry/Very angry/High-risk escalation), confidence_score, recorded_at

### Relationships
- A user has many orders
- An order has one optional return, which has one optional refund
- Every voice session produces messages tied to a ticket
- Every ticket produces exactly one resolution, which references the specific policy document used — this is what makes every AI answer traceable back to a real policy rather than a guess

### Auth Provider
📌 Not specified — see the TRD document.

### Row Level Security
📌 Not specified. Given Postgres on Neon/Supabase, a reasonable default: customers can only read/write rows where `user_id` matches their own; support managers get broader read access across tickets.

### User Roles
Customer (own data only); Support Manager / Admin (full dashboard + ticket access). No finer-grained roles specified.

### File Storage
`voice_sessions.audio_file_path` and `support_resolutions.final_response_audio` are both explicitly optional in the spec — provider/location 📌 not specified (Supabase Storage or a Railway/Render volume would both work).

### Sensitive Fields
- `users.phone` — confirm it's demo/fictional data, per the management sign-off requirement, before any public sharing
- Payment details — `payments` should store transaction status only; never store raw payment instrument data

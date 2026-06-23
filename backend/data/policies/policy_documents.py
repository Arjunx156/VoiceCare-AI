"""
CommerceMind VoiceCare AI — Fictional Policy Documents
12 policy documents with concrete, quotable numbers for strong RAG retrieval.
All content is entirely fictional — no real company policy.
"""

POLICY_DOCUMENTS = [
    {
        "id": "policy-shipping-001",
        "title": "Standard Shipping Policy",
        "category": "Shipping",
        "content": """STANDARD SHIPPING POLICY — ShopEase India

1. DELIVERY TIMELINES
- Metro cities (Delhi, Mumbai, Bangalore, Chennai, Hyderabad, Kolkata): 3-5 business days
- Tier-2 cities: 5-7 business days
- Remote/rural areas: 7-12 business days
- Express delivery (additional ₹99): 1-2 business days for metro cities only

2. TRACKING
- Tracking number is generated within 24 hours of order confirmation
- Customers receive SMS and email updates at each shipment milestone
- Real-time tracking available on the app and website

3. DELIVERY ATTEMPTS
- Maximum 3 delivery attempts will be made
- If all 3 attempts fail, the order is returned to warehouse (RTO)
- RTO refund is processed within 5-7 business days

4. DELAYS
- If delivery exceeds the estimated date by more than 3 days, customer is eligible for ₹50 shipping credit
- Delays due to natural disasters, strikes, or government restrictions are exempt from compensation
- Customer can request cancellation with full refund if order is delayed beyond 15 days"""
    },
    {
        "id": "policy-return-001",
        "title": "Return & Exchange Policy",
        "category": "Return",
        "content": """RETURN & EXCHANGE POLICY — ShopEase India

1. RETURN WINDOW
- Standard return window: 7 days from delivery date
- Electronics: 7 days (unopened/unused only)
- Fashion/Apparel: 15 days (with tags attached)
- Perishables/Groceries: Non-returnable
- Customized/personalized items: Non-returnable

2. ELIGIBILITY
- Item must be unused, unworn, and in original packaging
- All tags, labels, and accessories must be intact
- Customer must provide proof of purchase (order ID)

3. PROCESS
- Return request submitted via app, website, or customer support
- Pickup scheduled within 2 business days of approval
- Item inspected at warehouse within 3 business days of pickup
- If inspection passes: refund initiated within 2 business days
- If inspection fails: item returned to customer with explanation

4. EXCHANGE
- Exchanges processed as return + new order
- Size exchanges for fashion items: free shipping on replacement
- Different product exchanges: customer pays any price difference"""
    },
    {
        "id": "policy-refund-001",
        "title": "Refund Policy",
        "category": "Refund",
        "content": """REFUND POLICY — ShopEase India

1. REFUND METHODS
- Original payment method: 5-7 business days
- ShopEase Wallet credit: instant (within 2 hours)
- Bank account (NEFT): 3-5 business days
- UPI refund: 2-4 business days

2. REFUND AMOUNTS
- Full refund: cancelled orders, defective items, wrong items delivered
- Partial refund: items returned with minor damage (up to 20% deduction)
- Shipping charges: refunded only if return is due to seller error or defective product

3. REFUND SLA
- Refund must be initiated within 48 hours of return inspection completion
- If refund is delayed beyond 10 business days from initiation, customer receives additional ₹100 compensation
- Refund status updates sent via SMS at each stage

4. NON-REFUNDABLE
- Gift cards and vouchers
- Downloaded digital content
- Items marked "Final Sale"
- Service charges and convenience fees"""
    },
    {
        "id": "policy-cancellation-001",
        "title": "Order Cancellation Policy",
        "category": "Cancellation",
        "content": """ORDER CANCELLATION POLICY — ShopEase India

1. CANCELLATION WINDOW
- Before shipment: free cancellation, full refund within 24 hours
- After shipment but before delivery: cancellation allowed, but ₹50 reverse logistics fee applies
- After delivery: not a cancellation — use Return Policy instead

2. PARTIAL CANCELLATION
- Individual items in a multi-item order can be cancelled separately
- Shipping charges recalculated based on remaining items

3. SELLER CANCELLATION
- If seller cancels due to stock unavailability: full refund + ₹50 ShopEase credit as apology
- Customer notified immediately via SMS and push notification

4. AUTO-CANCELLATION
- Orders not confirmed by seller within 48 hours are auto-cancelled
- Payment authorization hold released within 24 hours of auto-cancellation"""
    },
    {
        "id": "policy-replacement-001",
        "title": "Replacement Policy",
        "category": "Replacement",
        "content": """REPLACEMENT POLICY — ShopEase India

1. ELIGIBILITY
- Defective product received: free replacement within 7 days
- Wrong product delivered: free replacement within 7 days
- Missing items in order: free replacement within 3 days
- Damaged during transit: free replacement with photo proof within 48 hours

2. PROCESS
- Customer reports issue with photos via app or support
- Replacement approved within 4 hours for clear defect/damage cases
- Replacement item shipped within 24 hours of approval
- Original item picked up at same time as replacement delivery (exchange pickup)

3. NO REPLACEMENT AVAILABLE
- If replacement stock is unavailable: full refund processed automatically
- Customer may choose ShopEase Wallet credit for instant refund + ₹75 bonus

4. LIMITS
- Maximum 2 replacements per order
- If issue persists after 2 replacements: full refund + ₹200 compensation"""
    },
    {
        "id": "policy-warranty-001",
        "title": "Warranty Policy",
        "category": "Warranty",
        "content": """WARRANTY POLICY — ShopEase India

1. SHOPEASE WARRANTY
- All electronics: 6-month ShopEase warranty (in addition to manufacturer warranty)
- Fashion/Lifestyle: no warranty
- Home & Kitchen: 3-month ShopEase warranty on appliances

2. CLAIM PROCESS
- Customer contacts support with order ID and issue description
- For electronics: diagnostic check arranged within 3 business days
- Repair turnaround: 7-14 business days
- If repair not possible: replacement or refund at ShopEase discretion

3. WARRANTY EXCLUSIONS
- Physical damage by customer
- Water/liquid damage
- Unauthorized modifications
- Normal wear and tear

4. EXTENDED WARRANTY
- Available for purchase within 15 days of delivery
- 1-year extension: ₹299 for items up to ₹5,000; ₹599 for items ₹5,000-₹20,000"""
    },
    {
        "id": "policy-compensation-001",
        "title": "Customer Compensation Guidelines",
        "category": "Compensation",
        "content": """CUSTOMER COMPENSATION GUIDELINES — ShopEase India

1. AUTOMATIC COMPENSATION
- Delivery delayed >3 days beyond estimate: ₹50 shipping credit
- Refund delayed >10 business days: ₹100 additional compensation
- 2+ failed replacements: ₹200 compensation
- Seller cancellation: ₹50 ShopEase credit

2. DISCRETIONARY COMPENSATION (requires manager approval)
- Severe inconvenience: up to ₹500 ShopEase credit
- Repeated issues (3+ complaints in 30 days): up to ₹1,000 credit + priority support status
- Premium customers: 2x standard compensation

3. COMPENSATION LIMITS
- Maximum ₹2,000 in compensation credits per customer per quarter
- Credits valid for 90 days from issue date
- Credits non-transferable and cannot be converted to cash

4. ESCALATION FOR COMPENSATION
- Requests exceeding ₹500: escalate to senior support manager
- Requests exceeding ₹1,000: escalate to customer experience head"""
    },
    {
        "id": "policy-escalation-sop-001",
        "title": "Escalation Standard Operating Procedure",
        "category": "Escalation SOP",
        "content": """ESCALATION SOP — ShopEase India

1. AUTOMATIC ESCALATION TRIGGERS
- Customer sentiment: Angry or Very Angry
- High-value order (>₹5,000) with complaint
- Refund pending beyond SLA (>10 business days)
- Payment deducted but order not created
- AI confidence score below 0.6

2. ESCALATION LEVELS
- Level 1 (AI → Senior Agent): all automatic triggers
- Level 2 (Senior Agent → Team Lead): unresolved after 24 hours
- Level 3 (Team Lead → Manager): unresolved after 48 hours, or compensation >₹500

3. HANDOFF REQUIREMENTS
- AI must generate a complete handoff note including:
  * Customer name, language preference, sentiment assessment
  * Full conversation transcript
  * AI's attempted resolution and policy referenced
  * Reason for escalation
  * Recommended next steps for human agent

4. SLA FOR ESCALATED TICKETS
- Level 1: human agent must respond within 2 hours
- Level 2: team lead review within 4 hours
- Level 3: manager resolution within 24 hours"""
    },
    {
        "id": "policy-payment-failure-sop-001",
        "title": "Payment Failure Standard Operating Procedure",
        "category": "Payment Failure SOP",
        "content": """PAYMENT FAILURE SOP — ShopEase India

1. PAYMENT DEDUCTED, ORDER NOT CONFIRMED
- This is a CRITICAL priority issue — escalate immediately
- Customer's bank shows deduction but ShopEase shows failed/no order
- Resolution: verify with payment gateway within 1 hour
- If confirmed failed: refund initiated immediately, credited within 24-48 hours
- Customer receives SMS confirmation of refund initiation

2. DOUBLE PAYMENT
- Customer charged twice for same order
- Resolution: second charge refunded within 48 hours
- Compensation: ₹100 ShopEase credit for inconvenience

3. PAYMENT METHOD ISSUES
- UPI timeout: retry after 5 minutes, or use alternate payment method
- Card declined: suggest alternate card or UPI/net banking
- COD not available: area may not be COD-eligible; suggest prepaid options

4. REFUND FOR FAILED PAYMENT
- Auto-refund for gateway failures: 3-5 business days
- Manual refund for disputed transactions: 7-10 business days
- Customer should contact bank if refund not received within stated timeline"""
    },
    {
        "id": "policy-damaged-product-001",
        "title": "Damaged Product Handling Policy",
        "category": "Return",
        "content": """DAMAGED PRODUCT HANDLING — ShopEase India

1. REPORTING
- Customer must report damage within 48 hours of delivery
- Photos required: at least 2 photos showing damage clearly
- Unboxing video (if available) strengthens the claim

2. RESOLUTION OPTIONS
- Option A: Free replacement (delivered within 3-5 business days)
- Option B: Full refund to original payment method
- Option C: ShopEase Wallet credit (instant) + ₹75 bonus

3. HIGH-VALUE DAMAGED ITEMS (>₹5,000)
- Escalate to senior support for verification
- May require physical inspection before replacement/refund
- Resolution within 72 hours of report

4. TRANSIT DAMAGE vs MANUFACTURING DEFECT
- Transit damage: handled by ShopEase, free return and replacement
- Manufacturing defect: covered under warranty, contact manufacturer or ShopEase warranty support"""
    },
    {
        "id": "policy-wrong-product-001",
        "title": "Wrong Product Delivered Policy",
        "category": "Return",
        "content": """WRONG PRODUCT DELIVERED — ShopEase India

1. DEFINITION
- Product received does not match the ordered item (different product, size, color, or variant)

2. RESOLUTION
- Immediate free pickup of wrong item scheduled (within 2 business days)
- Correct item shipped on priority (1-3 business days for metro, 3-5 for others)
- If correct item not in stock: full refund + ₹100 ShopEase credit

3. CUSTOMER RESPONSIBILITY
- Wrong item must be returned in original condition
- If wrong item is used/damaged by customer: 50% refund deduction

4. SELLER ACCOUNTABILITY
- Seller charged a ₹200 penalty for wrong shipment
- Repeated offenses (3+ in a month): seller account review"""
    },
    {
        "id": "policy-customer-communication-001",
        "title": "Customer Communication Guidelines",
        "category": "Escalation SOP",
        "content": """CUSTOMER COMMUNICATION GUIDELINES — ShopEase India

1. TONE & LANGUAGE
- Always empathetic and professional
- Acknowledge the customer's frustration before providing solutions
- Use the customer's preferred language when possible
- Avoid technical jargon — speak in simple, clear terms

2. RESPONSE STRUCTURE
- Greet by name if available
- Acknowledge the issue
- Explain what happened (if known)
- State the resolution clearly with specific timelines
- Offer additional help

3. THINGS TO NEVER SAY
- "That's not our problem" — everything is our problem
- "You should have..." — never blame the customer
- "I don't know" — say "Let me find out for you"
- Generic responses without referencing the specific issue

4. MULTILINGUAL SUPPORT
- Support available in Hindi, English, Tamil, Telugu, Malayalam, Kannada, Bengali, Marathi
- Customer's language preference stored in profile
- If agent doesn't speak the language: use AI translation, never refuse service"""
    },
]


def get_all_policies() -> list:
    """Return all fictional policy documents."""
    return POLICY_DOCUMENTS

"""
CommerceMind VoiceCare AI — Fictional Seed Data
All data is entirely fictional — no real customer names, phone numbers, or addresses.
"""

from datetime import datetime, timedelta
import uuid

# Fixed UUIDs for demo reproducibility
USER_IDS = [uuid.UUID(f"00000000-0000-0000-0000-00000000000{i}") for i in range(1, 9)]
PRODUCT_IDS = [uuid.UUID(f"10000000-0000-0000-0000-00000000000{i}") for i in range(1, 9)]
ORDER_IDS = [uuid.UUID(f"20000000-0000-0000-0000-00000000000{i}") for i in range(1, 9)]

SEED_USERS = [
    {"user_id": USER_IDS[0], "name": "Rajesh Kumar", "phone": "9876543210", "city": "Delhi", "preferred_language": "Hindi", "customer_segment": "Premium"},
    {"user_id": USER_IDS[1], "name": "Priya Nair", "phone": "9876543211", "city": "Kochi", "preferred_language": "Malayalam", "customer_segment": "Regular"},
    {"user_id": USER_IDS[2], "name": "Muthu Selvam", "phone": "9876543212", "city": "Chennai", "preferred_language": "Tamil", "customer_segment": "Regular"},
    {"user_id": USER_IDS[3], "name": "Ananya Reddy", "phone": "9876543213", "city": "Hyderabad", "preferred_language": "Telugu", "customer_segment": "Premium"},
    {"user_id": USER_IDS[4], "name": "Kavitha Shetty", "phone": "9876543214", "city": "Bangalore", "preferred_language": "Kannada", "customer_segment": "New"},
    {"user_id": USER_IDS[5], "name": "Sourav Das", "phone": "9876543215", "city": "Kolkata", "preferred_language": "Bengali", "customer_segment": "Regular"},
    {"user_id": USER_IDS[6], "name": "Sneha Patil", "phone": "9876543216", "city": "Pune", "preferred_language": "Marathi", "customer_segment": "Premium"},
    {"user_id": USER_IDS[7], "name": "Amit Sharma", "phone": "9876543217", "city": "Mumbai", "preferred_language": "Hinglish", "customer_segment": "Regular"},
]

now = datetime.utcnow()

SEED_PRODUCTS = [
    {"product_id": PRODUCT_IDS[0], "name": "Samsung Galaxy M15 5G", "category": "Electronics", "price": 12999.00, "sku": "ELEC-SAM-M15"},
    {"product_id": PRODUCT_IDS[1], "name": "Nike Air Max Running Shoes", "category": "Fashion", "price": 8495.00, "sku": "FASH-NIKE-AM1"},
    {"product_id": PRODUCT_IDS[2], "name": "Prestige Induction Cooktop", "category": "Home & Kitchen", "price": 2899.00, "sku": "HOME-PRES-IC1"},
    {"product_id": PRODUCT_IDS[3], "name": "boAt Airdopes 141 Earbuds", "category": "Electronics", "price": 1299.00, "sku": "ELEC-BOAT-141"},
    {"product_id": PRODUCT_IDS[4], "name": "Levi's 511 Slim Fit Jeans", "category": "Fashion", "price": 2799.00, "sku": "FASH-LEVI-511"},
    {"product_id": PRODUCT_IDS[5], "name": "Milton Thermosteel Flask 1L", "category": "Home & Kitchen", "price": 899.00, "sku": "HOME-MILT-TS1"},
    {"product_id": PRODUCT_IDS[6], "name": "Apple AirPods Pro 2", "category": "Electronics", "price": 24900.00, "sku": "ELEC-APPL-AP2"},
    {"product_id": PRODUCT_IDS[7], "name": "Wildcraft Backpack 35L", "category": "Fashion", "price": 1899.00, "sku": "FASH-WILD-BP1"},
]

SEED_ORDERS = [
    # Order 1: Rajesh — delayed delivery (demo scenario 1)
    {"order_id": ORDER_IDS[0], "user_id": USER_IDS[0], "order_number": "ORD-RK24",
     "order_date": now - timedelta(days=10), "status": "Shipped", "total_amount": 12999.00},
    # Order 2: Priya — refund delay (demo scenario 2)
    {"order_id": ORDER_IDS[1], "user_id": USER_IDS[1], "order_number": "ORD-PN37",
     "order_date": now - timedelta(days=20), "status": "Delivered", "total_amount": 8495.00},
    # Order 3: Muthu — damaged product (demo scenario 3)
    {"order_id": ORDER_IDS[2], "user_id": USER_IDS[2], "order_number": "ORD-MS52",
     "order_date": now - timedelta(days=5), "status": "Delivered", "total_amount": 2899.00},
    # Order 4: Ananya — payment failed (demo scenario 4)
    {"order_id": ORDER_IDS[3], "user_id": USER_IDS[3], "order_number": "ORD-AR81",
     "order_date": now - timedelta(days=1), "status": "Cancelled", "total_amount": 24900.00},
    # Order 5: Amit — angry repeat complaint (demo scenario 5)
    {"order_id": ORDER_IDS[4], "user_id": USER_IDS[7], "order_number": "ORD-AS63",
     "order_date": now - timedelta(days=15), "status": "Delivered", "total_amount": 12999.00},
    # Additional orders
    {"order_id": ORDER_IDS[5], "user_id": USER_IDS[4], "order_number": "ORD-KS49",
     "order_date": now - timedelta(days=3), "status": "Placed", "total_amount": 2799.00},
    {"order_id": ORDER_IDS[6], "user_id": USER_IDS[5], "order_number": "ORD-SD75",
     "order_date": now - timedelta(days=7), "status": "Delivered", "total_amount": 899.00},
    {"order_id": ORDER_IDS[7], "user_id": USER_IDS[6], "order_number": "ORD-SP38",
     "order_date": now - timedelta(days=12), "status": "Shipped", "total_amount": 1899.00},
]

SEED_SHIPMENTS = [
    # Rajesh's order — delayed, expected 5 days ago
    {"order_id": ORDER_IDS[0], "courier_partner": "BlueDart Express",
     "shipment_status": "In Transit", "expected_delivery_date": now - timedelta(days=5),
     "actual_delivery_date": None, "tracking_number": "BD1234567890"},
    # Priya's order — delivered
    {"order_id": ORDER_IDS[1], "courier_partner": "Delhivery",
     "shipment_status": "Delivered", "expected_delivery_date": now - timedelta(days=15),
     "actual_delivery_date": now - timedelta(days=14), "tracking_number": "DL9876543210"},
    # Muthu's order — delivered (but damaged)
    {"order_id": ORDER_IDS[2], "courier_partner": "Ecom Express",
     "shipment_status": "Delivered", "expected_delivery_date": now - timedelta(days=3),
     "actual_delivery_date": now - timedelta(days=3), "tracking_number": "EC5555555555"},
    # Amit's order — delivered (wrong product)
    {"order_id": ORDER_IDS[4], "courier_partner": "DTDC",
     "shipment_status": "Delivered", "expected_delivery_date": now - timedelta(days=10),
     "actual_delivery_date": now - timedelta(days=10), "tracking_number": "DT7777777777"},
]

SEED_RETURNS = [
    # Priya's return — approved, refund pending
    {"order_id": ORDER_IDS[1], "reason": "Size does not fit, need exchange",
     "status": "Completed", "eligibility_window_days": 15},
    # Amit's return — wrong product
    {"order_id": ORDER_IDS[4], "reason": "Wrong product received — ordered Samsung phone, got earbuds",
     "status": "Approved", "eligibility_window_days": 7},
]

SEED_REFUNDS = [
    # Priya's refund — delayed beyond SLA (pending for 12 days)
    {"return_order_index": 0, "order_id": ORDER_IDS[1],
     "amount": 8495.00, "status": "Pending", "credited_at": None},
]

SEED_PAYMENTS = [
    {"order_id": ORDER_IDS[0], "amount": 12999.00, "status": "Success", "payment_method": "UPI"},
    {"order_id": ORDER_IDS[1], "amount": 8495.00, "status": "Success", "payment_method": "Credit Card"},
    {"order_id": ORDER_IDS[2], "amount": 2899.00, "status": "Success", "payment_method": "Debit Card"},
    # Ananya's payment — deducted but order cancelled (demo scenario 4)
    {"order_id": ORDER_IDS[3], "amount": 24900.00, "status": "Success", "payment_method": "UPI"},
    {"order_id": ORDER_IDS[3], "amount": 24900.00, "status": "Failed", "payment_method": "UPI"},
    {"order_id": ORDER_IDS[4], "amount": 12999.00, "status": "Success", "payment_method": "Net Banking"},
    {"order_id": ORDER_IDS[5], "amount": 2799.00, "status": "Success", "payment_method": "COD"},
    {"order_id": ORDER_IDS[6], "amount": 899.00, "status": "Success", "payment_method": "UPI"},
]

SEED_ESCALATION_RULES = [
    {"rule_name": "Angry Customer", "condition_description": "Customer sentiment is Angry or Very Angry",
     "trigger_type": "sentiment", "priority_level": "High"},
    {"rule_name": "High-Value Complaint", "condition_description": "Order value exceeds ₹5,000 with negative sentiment",
     "trigger_type": "order_value", "priority_level": "High"},
    {"rule_name": "Refund SLA Breach", "condition_description": "Refund pending beyond 10 business days SLA",
     "trigger_type": "refund_delay", "priority_level": "Critical"},
    {"rule_name": "Payment Anomaly", "condition_description": "Payment deducted but order not created or cancelled",
     "trigger_type": "payment_issue", "priority_level": "Critical"},
    {"rule_name": "Low AI Confidence", "condition_description": "AI confidence score below 0.6",
     "trigger_type": "confidence", "priority_level": "Medium"},
]

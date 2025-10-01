from flask import Flask, render_template, request, jsonify
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed, SalesforceMalformedRequest
import os
from datetime import date
import random
import string
import requests # Import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning # Import InsecureRequestWarning

# Disable SSL warnings (use with caution in production)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ---------- SALESFORCE CREDENTIALS ----------
SF_USERNAME = os.getenv("SF_USERNAME", "22691a3141147@agentforce.com")
SF_PASSWORD = os.getenv("SF_PASSWORD", "Habeeb@123")
SF_SECURITY_TOKEN = os.getenv("SF_SECURITY_TOKEN", "W1ZH5gciwLwD7i1m9NqY9ivTs")
# --------------------------------------------

app = Flask(__name__)

# Connect to Salesforce once at startup
try:
    # Create a session with SSL verification disabled
    session = requests.Session()
    session.verify = False

    sf = Salesforce(
        username=SF_USERNAME,
        password=SF_PASSWORD,
        security_token=SF_SECURITY_TOKEN,
        session=session # Pass the session with verify=False
    )
    print("✅ Connected to Salesforce successfully!")
except SalesforceAuthenticationFailed as e:
    print("❌ Salesforce authentication failed:", e)
    sf = None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/api/salesforce/order", methods=["POST"])
def create_order():
    if not sf:
        return jsonify({"error": "Salesforce connection not available"}), 500

    data = request.get_json(silent=True)
    required_fields = ["name", "email", "mobile", "items", "billing_address", "payment_method"]
    if not data or not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        print("DEBUG: Starting order creation process.")
        account_id = get_or_create_generic_account()
        print(f"DEBUG: Account ID: {account_id}")
        contact_id = get_or_create_contact(data['name'], data['email'], data['mobile'], account_id)
        print(f"DEBUG: Contact ID: {contact_id}")
        pricebook_id = get_standard_pricebook_id()
        print(f"DEBUG: Pricebook ID: {pricebook_id}")
        billing_address = data['billing_address']
        shipping_address = data.get('shipping_address', billing_address) # Default to billing if shipping not provided
        print(f"DEBUG: Billing Address: {billing_address}")
        print(f"DEBUG: Shipping Address: {shipping_address}")

        # Create a Salesforce Order
        order_data = {
            "AccountId": account_id,
            "BillToContactId": contact_id,
            "EffectiveDate": date.today().isoformat(),
            "Status": "Draft",
            "Pricebook2Id": pricebook_id,
            "BillingStreet": billing_address['street'],
            "BillingCity": billing_address['city'],
            "BillingState": billing_address.get('state'),
            "BillingPostalCode": billing_address['zip'],
            "BillingCountry": billing_address['country'],
            "ShippingStreet": shipping_address['street'],
            "ShippingCity": shipping_address['city'],
            "ShippingState": shipping_address.get('state'),
            "ShippingPostalCode": shipping_address['zip'],
            "ShippingCountry": shipping_address['country'],
            "Payment_Method__c": data['payment_method'], # Custom field for payment method
        }

        # Add payment details if available
        if data['payment_method'] == "Card" and 'card_details' in data:
            card_details = data['card_details']
            order_data["Payment_Details__c"] = f"Card: {card_details.get('card_number', '')}, Expiry: {card_details.get('expiry', '')}, CVC: {card_details.get('cvc', '')}"
        elif data['payment_method'] == "UPI" and 'upi_id' in data:
            order_data["Payment_Details__c"] = f"UPI ID: {data['upi_id']}"

        new_order = sf.Order.create(order_data)
        order_id = new_order['id']
        print(f"DEBUG: New Order ID: {order_id}")

        # Optimize fetching product and pricebook entry IDs
        product_names = list(set(item['name'] for item in data['items']))
        product_ids_map = get_product_ids_by_names(product_names)
        
        all_product_ids = list(product_ids_map.values())
        pricebook_entries_map = get_pricebook_entries_for_products(all_product_ids, pricebook_id)

        order_items = []
        for item in data['items']:
            product_id = product_ids_map.get(item['name'])
            if product_id:
                print(f"DEBUG: Found Product ID {product_id} for product: {item['name']}")
                pricebook_entry_id = pricebook_entries_map.get(product_id)
                if pricebook_entry_id:
                    print(f"DEBUG: Found Pricebook Entry ID {pricebook_entry_id} for product: {item['name']}")
                    order_items.append({
                        "OrderId": order_id,
                        "Product2Id": product_id,
                        "Quantity": item['qty'],
                        "UnitPrice": item['price'],
                        "PricebookEntryId": pricebook_entry_id,
                        "Description": f"Product: {item['name']}, Price: {item['price']}"
                    })
                else:
                    print(f"DEBUG: Pricebook Entry not found for Product ID {product_id} and Pricebook ID {pricebook_id} for product: {item['name']}")
            else:
                print(f"DEBUG: Product ID not found for product: {item['name']}")

        if order_items:
            sf.bulk.OrderItem.insert(order_items)
            print(f"DEBUG: Inserted {len(order_items)} order items.")
        else:
            print("DEBUG: No order items to insert.")

        print("DEBUG: Order created successfully.")
        return jsonify({"status": "ok", "order_id": order_id})

    except SalesforceMalformedRequest as e:
        print(f"ERROR: Salesforce request error: {e}")
        return jsonify({"error": f"Salesforce request error: {e}"}), 502
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        return jsonify({"error": str(e)}), 500



def get_product_ids_by_names(product_names):
    """Gets a map of product names to IDs for a list of product names."""
    if not product_names:
        return {}
    
    # Escape single quotes in product names and wrap each in single quotes for SOQL query
    quoted_names = ["'" + name.replace("'", "\\'") + "'" for name in product_names]
    
    query = f"SELECT Id, Name FROM Product2 WHERE Name IN ({', '.join(quoted_names)})"
    result = sf.query(query)
    return {record['Name']: record['Id'] for record in result['records']}

def get_pricebook_entries_for_products(product_ids, pricebook_id):
    """Gets a map of product IDs to PricebookEntry IDs for a list of product IDs and a pricebook."""
    if not product_ids:
        return {}
    
    # Escape single quotes in product IDs and wrap each in single quotes for SOQL query
    quoted_ids = ["'" + pid.replace("'", "\\'") + "'" for pid in product_ids]

    query = f"SELECT Id, Product2Id FROM PricebookEntry WHERE Product2Id IN ({', '.join(quoted_ids)}) AND Pricebook2Id = '{pricebook_id}'"
    result = sf.query(query)
    return {record['Product2Id']: record['Id'] for record in result['records']}


def get_or_create_generic_account():
    """Gets the ID of a generic 'Web Orders' account, or creates it."""
    query = "SELECT Id FROM Account WHERE Name = 'Web Orders' LIMIT 1"
    result = sf.query(query)

    if result['totalSize'] > 0:
        return result['records'][0]['Id']
    else:
        new_account = sf.Account.create({'Name': 'Web Orders'})
        return new_account['id']


def get_or_create_contact(name, email, mobile, account_id):
    """Finds a contact by email or creates a new one."""
    query = f"SELECT Id FROM Contact WHERE Email = '{email}' LIMIT 1"
    result = sf.query(query)

    if result['totalSize'] > 0:
        # Update contact details if they have changed
        contact_id = result['records'][0]['Id']
        last_name = name.split(" ")[-1] if " " in name else name
        first_name = name.replace(f" {last_name}", "") if " " in name else ""
        sf.Contact.update(contact_id, {
            'FirstName': first_name,
            'LastName': last_name,
            'MobilePhone': mobile
        })
        return contact_id
    else:
        last_name = name.split(" ")[-1] if " " in name else name
        first_name = name.replace(f" {last_name}", "") if " " in name else ""
        new_contact = sf.Contact.create({
            'FirstName': first_name,
            'LastName': last_name,
            'Email': email,
            'MobilePhone': mobile,
            'AccountId': account_id
        })
        return new_contact['id']


def get_standard_pricebook_id():
    """Gets the ID of the standard price book."""
    query = "SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1"
    result = sf.query(query)
    if result['totalSize'] > 0:
        return result['records'][0]['Id']
    return None


if __name__ == "__main__":
    # Use host='0.0.0.0' for deployment
    app.run(debug=True)

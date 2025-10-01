from simple_salesforce import Salesforce, SalesforceMalformedRequest, SalesforceAuthenticationFailed

# ---------- SET THESE VALUES ----------
USERNAME = '22691a3141147@agentforce.com'
PASSWORD = 'Habeeb@123'
SECURITY_TOKEN = 'W1ZH5gciwLwD7i1m9NqY9ivTs'
# --------------------------------------

try:
    # Connect to Salesforce
    sf = Salesforce(
        username=USERNAME,
        password=PASSWORD,
        security_token=SECURITY_TOKEN
    )
    print("✅ Connected to Salesforce successfully!")

    # --- Test 1: Query existing Leads ---
    print("\n--- Existing Leads ---")
    leads = sf.query("SELECT Id, LastName, Email FROM Lead LIMIT 5")
    for lead in leads['records']:
        print(f"{lead['Id']} | {lead['LastName']} | {lead['Email']}")

    # --- Test 2: Create a new Lead ---
    print("\n--- Creating a Test Lead ---")
    new_lead = sf.Lead.create({
        'LastName': 'Test User',
        'Company': 'Test Company',
        'Email': 'testuser@example.com'
    })
    print("Created Lead ID:", new_lead['id'])

    # --- Test 3: Delete the test Lead (optional cleanup) ---
    print("\n--- Deleting the Test Lead ---")
    sf.Lead.delete(new_lead['id'])
    print("Deleted Test Lead successfully!")

except SalesforceAuthenticationFailed as auth_err:
    print("❌ Authentication failed:", auth_err)
except SalesforceMalformedRequest as req_err:
    print("❌ Malformed request:", req_err)
except Exception as e:
    print("❌ Other error:", e)

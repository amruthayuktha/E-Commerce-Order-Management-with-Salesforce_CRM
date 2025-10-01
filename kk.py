from simple_salesforce import Salesforce, SalesforceMalformedRequest, SalesforceAuthenticationFailed

# ---------- SET THESE VALUES ----------
USERNAME = '22691a3141147@agentforce.com'
PASSWORD = 'Habeeb@123'
SECURITY_TOKEN = 'W1ZH5gciwLwD7i1m9NqY9ivTs'
# --------------------------------------
# Connect to Salesforce
sf = Salesforce(
        username=USERNAME,
        password=PASSWORD,
        security_token=SECURITY_TOKEN
    )
print(sf.query("SELECT Id, LastName, Email FROM Lead LIMIT 5"))

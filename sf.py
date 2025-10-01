from simple_salesforce import Salesforce

# ---------- SET THESE VALUES ----------
USERNAME='22691a3141147@agentforce.com'
PASSWORD='Habeeb@123'
SECURITY_TOKEN='W1ZH5gciwLwD7i1m9NqY9ivTs'
# --------------------------------------

sf = Salesforce(
    username=USERNAME,
    password=PASSWORD,
    security_token=SECURITY_TOKEN
)

print("Connected to Salesforce:", sf)

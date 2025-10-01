import requests
import json

url = "http://127.0.0.1:5000/api/salesforce/order"

payload = {
    "name": "Test User",
    "email": "test@example.com",
    "mobile": "1234567890",
    "items": [
        {
            "id": 1,
            "name": "Classic T-Shirt",
            "price": 499,
            "qty": 1
        }
    ],
    "billing_address": {
        "street": "123 Street",
        "city": "Hyderabad",
        "zip": "500001",
        "country": "India"
    }
}

headers = {
    'Content-Type': 'application/json'
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print(response.status_code)
print(response.json())

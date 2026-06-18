import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient

load_dotenv()

token_path = Path("generated") / "tokens" / "ads.json"
if not token_path.exists():
    raise FileNotFoundError(f"Token niet gevonden: {token_path}")

with token_path.open("r", encoding="utf-8") as fh:
    tok = json.load(fh)

config = {
    "developer_token": os.getenv("GOOGLE_ADS_DEV_TOKEN"),
    "client_id": tok["client_id"],
    "client_secret": tok["client_secret"],
    "refresh_token": tok["refresh_token"],
    "use_proto_plus": True,
}

login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
if login_customer_id:
    config["login_customer_id"] = login_customer_id.replace("-", "").strip()

client = GoogleAdsClient.load_from_dict(config)
ga_service = client.get_service("GoogleAdsService")

query = """
SELECT
  customer.id,
  customer.descriptive_name,
  customer.currency_code,
  customer.time_zone
FROM customer
LIMIT 1
"""

def test_customer(customer_id: str):
    customer_id = customer_id.replace("-", "").strip()
    print(f"\n=== TEST customer_id={customer_id} ===")
    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        found = False
        for row in response:
            found = True
            print("OK")
            print("customer.id =", row.customer.id)
            print("customer.descriptive_name =", row.customer.descriptive_name)
            print("customer.currency_code =", row.customer.currency_code)
            print("customer.time_zone =", row.customer.time_zone)
        if not found:
            print("GEEN RESULTATEN")
    except Exception as exc:
        print("FOUT")
        print(type(exc).__name__)
        print(str(exc))

test_customer("4899254293")
test_customer("8585726172")
import streamlit as st
from square.client import Client
import os
import urllib.parse
import subprocess

# had to use squareup==23.0.0.20221019 as the newer version didn't
# have square.client. This version doesn't have BearerAuthCredentials
# hence commenting out.

#from square.http.auth.o_auth_2 import BearerAuthCredentials

# --- Square setup ---
#ACCESS_TOKEN = "EAAAl8DSm1md8YXgsQA7HDRLxa6_W8t10fZGSnWWR_SGT2LjvV9fBilVVUZRMYSr"
ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN") or st.secrets.get("SQUARE_ACCESS_TOKEN")
LOCATION_ID = "LRV35JXF9C7QR"
#credentials = BearerAuthCredentials(access_token=ACCESS_TOKEN)

#client = Client(
#    bearer_auth_credentials=credentials,
#    environment="production"  # or "sandbox"
#)
client = Client(
    environment='production',  # or 'sandbox'
    access_token=ACCESS_TOKEN
)



st.set_page_config(page_title="Square POS", page_icon="💳", layout="centered")

st.title("💳 Square POS Web")

# ---------- Fetch Customers ----------
@st.cache_data(show_spinner="Loading customers from Square...")
def load_customers():
    customers = []
    cursor = None
    while True:
        result = client.customers.list_customers(cursor=cursor)
        if result.is_success():
            body = result.body
            for c in body.get("customers", []):
                name = f"{c.get('given_name', '')} {c.get('family_name', '')}".strip()
                if name:
                    customers.append(name)
            cursor = body.get("cursor")
            if not cursor:
                break
        else:
            st.error(f"Error loading customers: {result.errors}")
            break
    return sorted(customers) if customers else ["(no customers found)"]

customers = load_customers()

# ---------- UI ----------
selected_customer = st.selectbox("Select Customer", customers)
#amount_pounds = st.number_input("Amount (£)", min_value=0.0, step=0.01)

amount_str = st.text_input("Amount (£)", value="")
try:
    amount_pounds = float(amount_str) if amount_str else 0.0
except ValueError:
    amount_pounds = 0.0
if amount_str and amount_pounds <= 0:
    st.warning("Please enter a valid amount greater than 0.")

# ---------- Payment Simulation ----------
#if st.button("Send to Square POS"):
#    if "(no customers" in selected_customer or "(Error" in selected_customer:
#        st.warning("Please select a valid customer.")
#    elif amount_pounds <= 0:
#        st.warning("Please enter a valid amount.")
#    else:
#        amount_pennies = int(amount_pounds * 100)
#        st.success(f"✅ Would launch Square POS for {selected_customer} - £{amount_pounds:.2f}")
#        st.info(f"(Intent URI would be generated for Android launch.)")
# ---------- Payment Handling ----------

ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN") or st.secrets.get("SQUARE_ACCESS_TOKEN")

if st.button("Send to Square POS"):
    if "(no customers" in selected_customer or "(Error" in selected_customer:
        st.warning("Please select a valid customer.")
    elif amount_pounds <= 0:
        st.warning("Please enter a valid amount greater than 0.")
    else:
        amount_pennies = int(amount_pounds * 100)

        # Build the Square POS intent URI
        intent_uri = (
            f"intent:#Intent;"
            f"action=com.squareup.pos.action.CHARGE;"
            f"package=com.squareup;"
            f"S.com.squareup.pos.CLIENT_ID={ACCESS_TOKEN};"
            f"S.com.squareup.pos.REQUEST_METADATA={selected_customer};"
            f"S.com.squareup.pos.NOTE=Invoice payment;"
            f"i.com.squareup.pos.TOTAL_AMOUNT={amount_pennies};"
            f"S.com.squareup.pos.CURRENCY_CODE=GBP;"
            f"end"
        )

        # Try launching Square POS (will only work on Android)
#        try:
#            subprocess.run(
#                ["am", "start", "-a", "android.intent.action.VIEW", "-d", intent_uri],
#                check=True,
#            )
#            st.success(f"💳 Launched Square POS for {selected_customer} - £{amount_pounds:.2f}")
#        except Exception as e:
#            # If not on Android or any error occurs
#            #st.info(f"Would launch Square POS for {selected_customer} - £{amount_pounds:.2f}")
#            #st.warning(f"(Simulated mode only — Android intent not available here.)")
#            st.success(f"✅ Would launch Square POS for {selected_customer} - £{amount_pounds:.2f}")
#            st.text_area("Intent URI (for debugging / Android use):", intent_uri, height=120)
#            st.warning("(Simulated mode only — Android intent not available here.)")
        import firebase_admin
        from firebase_admin import credentials, firestore
        import time

        # Initialize Firebase (only once)
        if not firebase_admin._apps:
            cred = credentials.Certificate("firebase-key.json")  # path to your service account JSON
            firebase_admin.initialize_app(cred)

        db = firestore.client()

        # Instead of trying to launch directly, log the intent for Android to process
        transaction = {
            "member": selected_customer,
            "amount": float(amount_pounds),
            "intent_uri": intent_uri,
            "timestamp": time.time(),
            "pending": True,
        }
        db.collection("transactions").add(transaction)

        st.success(f"📡 Sent transaction for {selected_customer} - £{amount_pounds:.2f}")
        st.text_area("Intent URI (for debugging):", intent_uri, height=120)
        st.warning("Awaiting Android listener to launch Square POS.")

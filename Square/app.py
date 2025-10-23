import streamlit as st
from square.client import Client
import streamlit as st

# had to use squareup==23.0.0.20221019 as the newer version didn't
# have square.client. This version doesn't have BearerAuthCredentials
# hence commenting out.

#from square.http.auth.o_auth_2 import BearerAuthCredentials

# --- Square setup ---
#ACCESS_TOKEN = "My access"
#LOCATION_ID = "My location"
#credentials = BearerAuthCredentials(access_token=ACCESS_TOKEN)

#client = Client(
#    bearer_auth_credentials=credentials,
#    environment="production"  # or "sandbox"
#)

ACCESS_TOKEN = st.secrets["SQUARE_ACCESS_TOKEN"]
LOCATION_ID = st.secrets["SQUARE_LOCATION_ID"]

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
if st.button("Send to Square POS"):
    if "(no customers" in selected_customer or "(Error" in selected_customer:
        st.warning("Please select a valid customer.")
    elif amount_pounds <= 0:
        st.warning("Please enter a valid amount.")
    else:
        amount_pennies = int(amount_pounds * 100)
        st.success(f"✅ Would launch Square POS for {selected_customer} - £{amount_pounds:.2f}")
        st.info(f"(Intent URI would be generated for Android launch.)")

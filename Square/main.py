from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton
from kivy.properties import StringProperty, ListProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.utils import platform as kivy_platform
from square.client import Client
from square.http.auth.o_auth_2 import BearerAuthCredentials
import threading
import subprocess

'''
got errors since the last chatGPT suggestion
If you’re still seeing that Invalid class name, could you paste the first ~15 
lines and the last 15 lines of your .kv file? That will confirm whether the issue is timing or syntax.
'''


KV_FILE = "square_pos.kv"

# --- Square setup ---
ACCESS_TOKEN = "My token"
LOCATION_ID = "My id"
credentials = BearerAuthCredentials(access_token=ACCESS_TOKEN)

client = Client(
    bearer_auth_credentials=credentials,
    environment="production"  # or "sandbox"
)


class POSLayout(MDBoxLayout):
    selected_customer = StringProperty("")
    customers = ListProperty(["(Loading customers...)"])
    amount_pounds = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.load_customers_async, 0.5)

    # ---------- Fetch Customers ----------
    def load_customers_async(self, *args):
        threading.Thread(target=self.fetch_customers, daemon=True).start()

    def fetch_customers(self):
        customers = []
        cursor = None
        while True:
            result = client.customers.list_customers(cursor=cursor)
            if result.is_success():
                body = result.body
                for c in body.get("customers", []):
                    name = f"{c.get('given_name', '')} {c.get('family_name', '')}".strip()
                    if name:
                        customers.append(name)`
                cursor = body.get("cursor")
                if not cursor:
                    break
            else:
                customers = ["(Error loading customers)"]
                print(result.errors)
                break

        customers = sorted(customers) if customers else ["(no customers found)"]
        Clock.schedule_once(lambda dt: self.update_customer_list(customers))

    def update_customer_list(self, customers):
        self.customers = customers
        self.populate_customer_list()

    # ---------- UI ----------
    def populate_customer_list(self, *args):
        self.ids.customer_list.data = [
            {
                "text": name,
                "md_bg_color": (0.2, 0.6, 1, 1)
                if name == self.selected_customer
                else (0.2, 0.2, 0.2, 1),
                "on_release": lambda name=name: self.set_customer(name),
            }
            for name in self.customers
        ]

    def set_customer(self, name):
        self.selected_customer = name
        #print(f"✅ Selected: {name}")
        self.populate_customer_list()
        #toast(f"Selected: {name}") #added along with toast import to give the output to screen

    # ---------- Payment ----------
    def show_popup(self, title, message):
        dialog = MDDialog(
            title=title,
            type="simple",
            items=[MDLabel(text=message)],
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def take_payment(self):
        if not self.selected_customer:
            self.show_popup("No customer", "Please select a customer first.")
            return

        try:
            amount = int(float(self.amount_pounds) * 100)
        except ValueError:
            self.show_popup("Invalid amount", "Amount must be a valid number.")
            return

        intent_uri = (
            f"intent:#Intent;"
            f"action=com.squareup.pos.action.CHARGE;"
            f"package=com.squareup;"
            f"S.com.squareup.pos.CLIENT_ID={ACCESS_TOKEN};"
            f"S.com.squareup.pos.REQUEST_METADATA={self.selected_customer};"
            f"S.com.squareup.pos.NOTE=Invoice payment;" 
            f"i.com.squareup.pos.TOTAL_AMOUNT={amount};"
            f"S.com.squareup.pos.CURRENCY_CODE=GBP;"
            f"end"
        )

        if kivy_platform == "android":
            try:
                subprocess.run(
                    ["am", "start", "-a", "android.intent.action.VIEW", "-d", intent_uri],
                    check=True,
                )
                print(f"💳 Launched Square POS for {self.selected_customer} - £{amount/100:.2f}")
                toast(f"💳 Launched Square POS for {self.selected_customer} - £{amount / 100:.2f}")
            except Exception as e:
                self.show_popup("Error launching POS", str(e))
        else:
            # Desktop simulation

            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            from kivy.uix.boxlayout import BoxLayout

            # Build the popup content in a layout (safer than passing Label directly)
            box = BoxLayout(orientation="vertical", padding=20, spacing=10)
            message = (
                f"Would launch Square POS for:\n\n"
                f"[b]{self.selected_customer}[/b]\n"
                f"Amount: £{amount / 100:.2f}\n"
                f"Item: 'Invoice payment"
            )
            label = Label(text=message, markup=True, halign="center", valign="middle")
            box.add_widget(label)

            popup = Popup(
                title="Simulated Charge",
                content=box,
                size_hint=(0.8, 0.4),
                auto_dismiss=True,
            )
            popup.open()

class SquarePOSApp(MDApp):
    def build(self):
        self.title = "Square POS"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark"

        Builder.load_file(KV_FILE)
        return POSLayout()


if __name__ == "__main__":
    SquarePOSApp().run()

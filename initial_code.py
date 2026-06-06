import os
from email.mime.text import MIMEText

import stripe
from dotenv import load_dotenv
from stripe import StripeError

load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

stripe.api_key = STRIPE_SECRET_KEY

class PaymentProcessor:
    def process_transaction(self, customer_data, payment_data):
        if not customer_data.get("name"):
            print("Invalid customer data: missing name")
            return
        if not customer_data.get("contact_info"):
            print("Invalid customer data: missing contact info")
            return
        if not payment_data.get("source"):
            print("Invalid payment data: missing source")
            return

        print("Validación exitosa: todos los datos son correctos")

        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=payment_data["amount"],
                currency="usd",
                payment_method=payment_data["source"],
                confirm=True,
                description=f"Pago de {customer_data['name']}",
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )
            print("💰 Pago exitoso con PaymentIntent!")
            print("🧾 ID del pago:", payment_intent.id)
            print("📦 Estado:", payment_intent.status)

        except StripeError as e:
            print("Payment failed", e)
            with open("transactions.log", "a") as log_file:
                log_file.write(f"{customer_data['name']} payment failed: {e}\n")
            return

        if "email" in customer_data["contact_info"]:
            # import smtplib

            msg = MIMEText("Thank you for your payment.")
            msg["Subject"] = "Payment Confirmation"
            msg["From"] = "no-reply@example.com"
            msg["To"] = customer_data["contact_info"]["email"]

            # server = smtplib.SMTP("localhost")
            # server.send_message(msg)
            # server.quit()
            print("Email sent to", customer_data["contact_info"]["email"])

        elif "phone" in customer_data["contact_info"]:
            phone_number = customer_data["contact_info"]["phone"]
            sms_gateway = "the custom SMS Gateway"
            print(
                f"send the sms using {sms_gateway}: SMS sent to {phone_number}: Thank you for your payment."
            )

        else:
            print("No valid contact information for notification")
            return

        with open("transactions.log", "a") as log_file:
            log_file.write(f"{customer_data['name']} paid {payment_data['amount']}\n")
            log_file.write(f"Payment status: {payment_intent.status}\n")


if __name__ == "__main__":
    processor = PaymentProcessor()

    customer_data_with_email = {
        "name": "John Doe",
        "contact_info": {"email": "e@mail.com"},
    }
    customer_data_with_phone = {
        "name": "Platzi Python",
        "contact_info": {"phone": "1234567890"},
    }

    payment_data = {"amount": 500, "source": "pm_card_mastercard", "cvv": 123}

    processor.process_transaction(customer_data_with_email, payment_data)

    processor.process_transaction(customer_data_with_phone, payment_data)

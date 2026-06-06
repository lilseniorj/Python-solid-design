"""
Refactor aplicando SRP (Single Responsibility Principle).

Idea: cada clase tiene UNA sola responsabilidad = UN solo motivo para cambiar.
El monolito `PaymentProcessor` de initial_code.py se parte en especialistas,
y un "orquestador" (PaymentService) los coordina sin hacer el trabajo él mismo.
"""

import os
from email.mime.text import MIMEText

import stripe
from dotenv import load_dotenv
from stripe import StripeError

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# ── Responsabilidad 1: VALIDAR ────────────────────────────────────────────────
# Su único motivo para cambiar: que cambien las reglas de validación.
class CustomerValidator:
    def validate(self, customer_data):
        if not customer_data.get("name"):
            raise ValueError("Invalid customer data: missing name")
        if not customer_data.get("contact_info"):
            raise ValueError("Invalid customer data: missing contact info")


class PaymentDataValidator:
    def validate(self, payment_data):
        if not payment_data.get("source"):
            raise ValueError("Invalid payment data: missing source")


# ── Responsabilidad 2: COBRAR ─────────────────────────────────────────────────
# Su único motivo para cambiar: que cambie cómo cobramos con Stripe.
class StripePaymentProcessor:
    def process(self, customer_data, payment_data):
        return stripe.PaymentIntent.create(
            amount=payment_data["amount"],
            currency="usd",
            payment_method=payment_data["source"],
            confirm=True,
            description=f"Pago de {customer_data['name']}",
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        )


# ── Responsabilidad 3: NOTIFICAR ──────────────────────────────────────────────
# Su único motivo para cambiar: que cambie cómo avisamos al cliente.
class Notifier:
    def send_confirmation(self, customer_data):
        contact = customer_data["contact_info"]
        if "email" in contact:
            msg = MIMEText("Thank you for your payment.")
            msg["Subject"] = "Payment Confirmation"
            msg["From"] = "no-reply@example.com"
            msg["To"] = contact["email"]
            print("Email sent to", contact["email"])
        elif "phone" in contact:
            print(f"SMS sent to {contact['phone']}: Thank you for your payment.")
        else:
            print("No valid contact information for notification")


# ── Responsabilidad 4: REGISTRAR ──────────────────────────────────────────────
# Su único motivo para cambiar: que cambie dónde/cómo guardamos el log.
class TransactionLogger:
    def log(self, customer_data, payment_data, payment_intent):
        with open("transactions.log", "a") as log_file:
            log_file.write(f"{customer_data['name']} paid {payment_data['amount']}\n")
            log_file.write(f"Payment status: {payment_intent.status}\n")


# ── El ORQUESTADOR ────────────────────────────────────────────────────────────
# No valida, no cobra, no notifica, no loguea. Solo COORDINA a los especialistas.
# Su único motivo para cambiar: que cambien los PASOS del proceso de pago.
class PaymentService:
    def __init__(self):
        self.customer_validator = CustomerValidator()
        self.payment_validator = PaymentDataValidator()
        self.payment_processor = StripePaymentProcessor()
        self.notifier = Notifier()
        self.logger = TransactionLogger()

    def process_transaction(self, customer_data, payment_data):
        self.customer_validator.validate(customer_data)
        self.payment_validator.validate(payment_data)

        payment_intent = self.payment_processor.process(customer_data, payment_data)

        self.notifier.send_confirmation(customer_data)
        self.logger.log(customer_data, payment_data, payment_intent)
        return payment_intent


if __name__ == "__main__":
    service = PaymentService()

    customer_data_with_email = {
        "name": "John Doe",
        "contact_info": {"email": "e@mail.com"},
    }
    payment_data = {"amount": 500, "source": "pm_card_mastercard", "cvv": 123}

    try:
        service.process_transaction(customer_data_with_email, payment_data)
    except ValueError as e:
        print("Validación falló:", e)
    except StripeError as e:
        print("Pago falló:", e)

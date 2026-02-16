from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Payment, Transaction, Property, StudentProperty, PropertyRental, PropertyOwnership
import requests
from django.conf import settings
from dotenv import load_dotenv
import os
from pathlib import Path
from .models import PaymentAudit



# ───────────────────────────────────────────────
#  PROPERTY ADAPTER – unify Property types
# ───────────────────────────────────────────────

def log_audit(payment, event, source, payload=None, message=""):
    PaymentAudit.objects.create(
        payment=payment,
        event=event,
        source=source,
        raw_payload=payload,
        message=message
    )


class PropertyAdapter:

    @staticmethod
    def get_any(property_id):
        try:
            p = Property.objects.get(id=property_id)
            return p, "normal"
        except:
            pass

        try:
            p = StudentProperty.objects.get(id=property_id)
            return p, "student"
        except:
            pass

        return None, None


# ───────────────────────────────────────────────
#  FLUTTERWAVE SERVICE
# ───────────────────────────────────────────────

import datetime 



class FlutterwaveService:
    # SANDBOX_BASE_URL = "https://developersandbox-api.flutterwave.com"
    LIVE_BASE_URL = "https://api.flutterwave.com/v3"
    TOKEN_URL= "https://idp.flutterwave.com/realms/flutterwave/protocol/openid-connect/token"
    

    def __init__(self):
        self.expires_in= datetime.datetime.min
        self.base_url = self.LIVE_BASE_URL
        # self.base_url = (
        #     self.SANDBOX_BASE_URL
        #     if os.getenv("FLUTTERWAVE_ENV") == "sandbox"
        #     else self.LIVE_BASE_URL
        # )
        self.secret_key = (
            os.getenv("FLUTTERWAVE_SECRET_KEY")
        )

    def get_access_token(self):
        """Synchronously get access token (no async)."""
        if datetime.datetime.now() >= self.expires_in:
            payload = {
                "client_id": os.getenv("FLUTTERWAVE_CLIENT_ID"),
                "client_secret": os.getenv("FLUTTERWAVE_CLIENT_SECRET"),
                "grant_type": "client_credentials",
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            res = requests.post(self.TOKEN_URL, data=payload, headers=headers)
            res.raise_for_status()
            data = res.json()

            self.access_token = data["access_token"]
            self.token_type = data["token_type"]
            self.expires_in = datetime.datetime.now() + datetime.timedelta(
                seconds=data["expires_in"] - 60
            )

        return self.access_token, self.token_type

    def auth_headers(self):
        # token, type_ = self.get_access_token()
        key = os.getenv("FLUTTERWAVE_CLIENT_SECRET")
        print(key)
        return {
            "Authorization": f"Bearer {key}",
            # "Authorization": f"{type_} {token}",
            "Content-Type": "application/json"
        }

    def initialize(self, payment: Payment):
        """Initialize payment."""
        payload = {
            "tx_ref": f"{payment.purpose}_{payment.id}",
            "amount": float(payment.amount),
            "currency": "NGN",
            "redirect_url": settings.FLUTTERWAVE_REDIRECT_URL,
            "payment_options": "card,banktransfer,ussd",
            "customer": {
                "email": payment.user.email,
                "name": payment.user.get_full_name() or payment.user.username,
            },
            "meta": {"payment_id": payment.id},
            "customizations": {
                "title": "Property Payment",
                "description": payment.description
            }
        }

        res = requests.post(
            f"{self.base_url}/payments",
            json=payload,
            headers=self.auth_headers()
        )
        res.raise_for_status()
        return res.json()

    def verify(self, transaction_id):
        res = requests.get(
            f"{self.base_url}/transactions/{transaction_id}/verify",
            headers=self.auth_headers()
        )
        res.raise_for_status()
        return res.json()


# ───────────────────────────────────────────────
#  PAYMENT PROCESSOR
# ───────────────────────────────────────────────

from django.db import transaction


class PaymentProcessor:

    @staticmethod
    def create_payment(user, amount, description, property_id):
        return Payment.objects.create(
            user=user,
            amount=amount,
            currency="NGN",
            description=description,
            payment_provider="flutterwave",
            status="pending",
            metadata={"property_id": property_id}
        )


    @staticmethod
    @transaction.atomic
    def mark_completed(payment: Payment, tx_id):

        # ── Idempotency ──
        if payment.status == "completed":
            return payment

        payment.status = "completed"
        payment.paid_at = timezone.now()
        payment.external_payment_id = tx_id
        payment.save(update_fields=[
            "status", "paid_at", "external_payment_id"
        ])

        return payment


    @staticmethod
    @transaction.atomic
    def create_transactions_and_records(payment: Payment):

        meta = payment.metadata or {}
        property_id = meta.get("property_id")

        property_obj, ptype = PropertyAdapter.get_any(property_id)

        if not property_obj:
            raise Exception("Property not found for payment")

        # ─── Validate amount ───
        if Decimal(payment.amount) <= 0:
            raise Exception("Invalid payment amount")

        # ─── Create transaction ───
        Transaction.objects.create(
            user=payment.user,
            transaction_type="property_payment",
            amount=payment.amount,
            description=f"Payment for {property_obj.title}",
            related_property_title=property_obj.title,
            payment=payment,
            status="completed"
        )

        # ─── BUSINESS LOGIC ───

        if property_obj.purpose == "sale":

            PropertyOwnership.objects.create(
                property=property_obj,
                owner=payment.user,
                purchase_price=payment.amount
            )

            property_obj.status = "sold"

            if hasattr(property_obj, "sold_to"):
                property_obj.sold_to = payment.user
                property_obj.sold_at = timezone.now()

            property_obj.save()

        else:
            # ─── RENTAL ───

            months = getattr(property_obj, "rent_duration_months", 1) or 1

            start = timezone.now().date()
            end = start + timezone.timedelta(days=30 * months)

            PropertyRental.objects.create(
                property=property_obj,
                tenant=payment.user,
                total_amount=payment.amount,
                monthly_rent=payment.amount,
                start_date=start,
                end_date=end,
                deposit=Decimal("0.00"),
                is_active=True
            )

            property_obj.status = "rented"

            if hasattr(property_obj, "rented_to"):
                property_obj.rented_to = payment.user

            property_obj.save()

        return True




def validate_flutterwave_amount(payment: Payment, fw_data: dict):
    """Ensure no one changed amount client-side"""

    paid = Decimal(str(fw_data.get("amount")))
    currency = fw_data.get("currency")

    if currency != payment.currency:
        raise Exception("Currency mismatch")

    if paid != payment.amount:
        raise Exception(
            f"Amount mismatch. expected {payment.amount} got {paid}"
        )



class FlutterwaveWebhook:

    @staticmethod
    def verify_signature(request):
        secret_hash = settings.FLUTTERWAVE_WEBHOOK_HASH
        signature = request.headers.get("verif-hash")

        return bool(signature and signature == secret_hash)


    @staticmethod
    def handle_event(payload):

        event = payload.get("event")
        data = payload.get("data", {})

        if event != "charge.completed":
            return {"status": "ignored"}

        if data.get("status") != "successful":
            return {"status": "not_success"}

        tx_id = data.get("id")
        meta = data.get("meta", {})
        payment_id = meta.get("payment_id")

        try:
            payment = Payment.objects.select_for_update().get(id=payment_id)

            log_audit(payment, "webhook_received", "webhook", payload)

            # ─── SECURITY CHECKS ───
            validate_flutterwave_amount(payment, data)

            if payment.user.email != data.get("customer", {}).get("email"):
                raise Exception("User email mismatch")

            # ─── IDEMPOTENCY ───
            if payment.status == "completed":
                log_audit(payment, "duplicate", "webhook")
                return {"status": "already_processed"}

            PaymentProcessor.mark_completed(payment, tx_id)
            PaymentProcessor.create_transactions_and_records(payment)

            log_audit(payment, "completed", "webhook")

            return {"status": "processed"}

        except Payment.DoesNotExist:
            return {"status": "payment_not_found"}

        except Exception as e:
            if 'payment' in locals():
                log_audit(payment, "error", "webhook", payload, str(e))

            return {"status": "error", "message": str(e)}

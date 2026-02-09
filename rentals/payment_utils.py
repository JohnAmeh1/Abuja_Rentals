# payment_utils.py
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Payment, Transaction, Property, StudentProperty, PropertyRental, PropertyOwnership
import requests
from django.conf import settings


# ───────────────────────────────────────────────
#  PROPERTY ADAPTER – unify Property types
# ───────────────────────────────────────────────
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
class FlutterwaveService:

    BASE_URL = "https://api.flutterwave.com/v3"

    @staticmethod
    def headers():
        return {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def initialize(payment: Payment):
        payload = {
            "tx_ref": f"RENT_{payment.id}",
            "amount": float(payment.amount),
            "currency": "NGN",
            "redirect_url": settings.FLUTTERWAVE_REDIRECT_URL,

            "payment_options": "card,banktransfer,ussd",

            "customer": {
                "email": payment.user.email,
                "name": payment.user.get_full_name() or payment.user.username,
            },

            "meta": {
                "payment_id": payment.id
            },

            "customizations": {
                "title": "Property Payment",
                "description": payment.description
            }
        }

        res = requests.post(
            f"{FlutterwaveService.BASE_URL}/payments",
            json=payload,
            headers=FlutterwaveService.headers()
        )

        return res.json()

    @staticmethod
    def verify(transaction_id):
        res = requests.get(
            f"{FlutterwaveService.BASE_URL}/transactions/{transaction_id}/verify",
            headers=FlutterwaveService.headers()
        )
        return res.json()


# ───────────────────────────────────────────────
#  PAYMENT PROCESSOR
# ───────────────────────────────────────────────
class PaymentProcessor:

    @staticmethod
    def create_payment(user, amount, description, property_id):
        payment = Payment.objects.create(
            user=user,
            amount=amount,
            currency="NGN",
            description=description,
            payment_provider="flutterwave",
            status="pending",
            metadata={
                "property_id": property_id
            }
        )

        return payment


    @staticmethod
    def mark_completed(payment: Payment, tx_id):

        payment.status = "completed"
        payment.paid_at = timezone.now()
        payment.external_payment_id = tx_id
        payment.save()

        return payment


    @staticmethod
    def create_transactions_and_records(payment: Payment):

        meta = payment.metadata or {}
        property_id = meta.get("property_id")

        property_obj, ptype = PropertyAdapter.get_any(property_id)

        if not property_obj:
            raise Exception("Property not found for payment")

        # ─── Create transaction ─────────────────────
        Transaction.objects.create(
            user=payment.user,
            transaction_type="property_payment",
            amount=payment.amount,
            description=f"Payment for {property_obj.title}",
            related_property_title=property_obj.title,
            payment=payment,
            status="completed"
        )

        # ─── Business logic ─────────────────────────
        if property_obj.purpose == "sale":

            PropertyOwnership.objects.create(
                property=property_obj,
                owner=payment.user,
                purchase_price=payment.amount
            )

            property_obj.status = "sold"
            property_obj.sold_to = payment.user
            property_obj.sold_at = timezone.now()
            property_obj.save()

        else:
            # rental
            PropertyRental.objects.create(
                property=property_obj,
                tenant=payment.user,
                total_amount=payment.amount,
                monthly_rent=payment.amount,
                start_date=timezone.now().date(),
                end_date=timezone.now().date(),
                deposit=Decimal("0.00"),
                is_active=True
            )

            property_obj.status = "rented"
            property_obj.rented_to = payment.user
            property_obj.save()

        return True
    
    # ───────────────────────────────────────────────
#  FLUTTERWAVE WEBHOOK HANDLER
# ───────────────────────────────────────────────
class FlutterwaveWebhook:

    @staticmethod
    def verify_signature(request):
        """Verify Flutterwave request came from them"""

        secret_hash = settings.FLUTTERWAVE_WEBHOOK_HASH
        signature = request.headers.get("verif-hash")

        if not signature or signature != secret_hash:
            return False
        return True


    @staticmethod
    def handle_event(payload):

        event = payload.get("event")
        data = payload.get("data", {})

        # We care only about successful charge
        if event != "charge.completed":
            return {"status": "ignored"}

        status = data.get("status")
        tx_id = data.get("id")

        meta = data.get("meta", {})
        payment_id = meta.get("payment_id")

        if status != "successful":
            return {"status": "not_success"}

        try:
            payment = Payment.objects.get(id=payment_id)

            # ─── IDEMPOTENCY ─────────────────────
            if payment.status == "completed":
                return {"status": "already_processed"}

            # Mark completed
            PaymentProcessor.mark_completed(payment, tx_id)

            # Business logic
            PaymentProcessor.create_transactions_and_records(payment)

            return {"status": "processed"}

        except Payment.DoesNotExist:
            return {"status": "payment_not_found"}

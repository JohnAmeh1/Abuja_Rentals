# payment_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .models import Payment, Property, PaymentAudit
from .payment_utils import (
    PaymentProcessor,
    FlutterwaveService,
    PropertyAdapter
)
from decimal import Decimal

def log_audit(payment, event, source, payload=None, message=""):
    PaymentAudit.objects.create(
        payment=payment,
        event=event,
        source=source,
        raw_payload=payload,
        message=message
    )


@login_required
@require_http_methods(["POST", "GET"])
def process_property_payment(request, property_id):

    property_obj = get_object_or_404(Property, id=property_id)

    if not request.POST.get("terms"):
        messages.error(request, "Please accept terms")
        return redirect("property_detail", property_id=property_id)


    payment = Payment.objects.create(
        user=request.user,
        amount=property_obj.price,
        currency="NGN",
        purpose=property_obj.purpose.upper(),
        description=f"Payment for {property_obj.title}",
        payment_provider="flutterwave",
        related_property=property_obj,
        status="pending",
        metadata={
            "property_id": property_obj.id,
            "purpose": property_obj.purpose
        }
    )
    

    
    fw_service = FlutterwaveService()
    init = fw_service.initialize(payment)

    if init.get("status") != "success":
        messages.error(request, "Could not start payment")
        return redirect("property_detail", property_id=property_id)

    log_audit(payment, "redirect_verified", "redirect", init)
    validate_flutterwave_amount(payment, init["data"])
    return redirect(init["data"]["link"])


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


# ───────────────────────────────────────────────
#  VERIFY PAYMENT RETURN
# ───────────────────────────────────────────────
@login_required
def verify_payment(request):

    transaction_id = request.GET.get("transaction_id")

    if not transaction_id:
        messages.error(request, "Invalid payment reference")
        return redirect("home")

    payment_service = FlutterwaveService()
    data = payment_service.verify(transaction_id)

    if data.get("status") != "success":
        messages.error(request, "Payment verification failed")
        return redirect("home")

    meta = data["data"].get("meta", {})
    payment_id = meta.get("payment_id")

    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status == "completed":
        log_audit(payment, "duplicate", "redirect")
        messages.info(request, "Payment already processed")
        return redirect("payment_receipt", payment_id=payment.id)

    PaymentProcessor.mark_completed(payment, transaction_id)
    PaymentProcessor.create_transactions_and_records(payment)

    messages.success(request, "Payment successful!")
    return redirect("payment_receipt", payment_id=payment.id)



# ───────────────────────────────────────────────
#  RECEIPT
# ───────────────────────────────────────────────
@login_required
def payment_receipt(request, payment_id):

    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    return render(request, "payment/receipt.html", {
        "payment": payment
    })


from django.views.decorators.csrf import csrf_exempt
import json
from .payment_utils import FlutterwaveWebhook


# ───────────────────────────────────────────────
#  FLUTTERWAVE WEBHOOK ENDPOINT
# ───────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def flutterwave_webhook(request):

    # 1. Verify signature
    if not FlutterwaveWebhook.verify_signature(request):
        return JsonResponse({"error": "invalid signature"}, status=401)

    try:
        payload = json.loads(request.body)

        result = FlutterwaveWebhook.handle_event(payload)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def flutterwave_verify(request):

    tx_ref = request.GET.get("tx_ref")
    transaction_id = request.GET.get("transaction_id")

    if not tx_ref:
        messages.error(request, "Invalid payment response")
        return redirect("dashboard")

    result = FlutterwaveService.verify(transaction_id)

    if result.get("status") != "success":
        messages.error(request, "Payment verification failed")
        return redirect("dashboard")

    # ✅ Extract real ID from "rent_15"
    try:
        payment_id = tx_ref.split("_")[-1]
        payment = Payment.objects.get(id=payment_id)

        if payment.status != "completed":
            PaymentProcessor.mark_completed(payment, transaction_id)
            PaymentProcessor.create_transactions_and_records(payment)

        messages.success(request, "Payment successful!")

    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found")

    return redirect("dashboard")

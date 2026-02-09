# payment_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .models import Payment, Property
from .payment_utils import (
    PaymentProcessor,
    FlutterwaveService,
    PropertyAdapter
)


@login_required
@require_http_methods(["POST"])
def process_property_payment(request, property_id):

    property_obj = get_object_or_404(Property, id=property_id)

    if not request.POST.get("terms"):
        messages.error(request, "Please accept terms")
        return redirect("property_detail", property_id=property_id)

    # ─── CREATE INTERNAL PAYMENT ───
    payment = Payment.objects.create(
        user=request.user,
        amount=property_obj.price,
        currency="NGN",
        description=f"Payment for {property_obj.title}",
        payment_provider="flutterwave",
        related_property=property_obj,
        status="pending",
        metadata={
            "purpose": property_obj.purpose
        }
    )

    # ─── INIT FLUTTERWAVE ───
    # init = FlutterwaveService.initialize_payment(
    #     payment,
    #     request.user.email,
    #     request.user.get_full_name() or request.user.username,
    #     request.build_absolute_uri(
    #         reverse("flutterwave_verify")
    #     )
    # )
    
    init = FlutterwaveService.initialize(payment)

    if not init["success"]:
        messages.error(request, "Could not start payment")
        return redirect("property_detail", property_id=property_id)

    # → SEND USER TO FLUTTERWAVE PAGE
    return redirect(init["link"])



# ───────────────────────────────────────────────
#  INITIATE PAYMENT
# ───────────────────────────────────────────────
@login_required
@require_http_methods(["POST"])
def initiate_payment(request, property_id):

    property_obj, _ = PropertyAdapter.get_any(property_id)

    if not property_obj:
        return JsonResponse({"error": "Property not found"}, status=404)

    if property_obj.owner == request.user:
        return JsonResponse({"error": "You cannot pay for your own property"}, status=400)

    # 1. Create internal payment
    payment = PaymentProcessor.create_payment(
        user=request.user,
        amount=property_obj.price,
        description=f"Payment for {property_obj.title}",
        property_id=property_obj.id
    )

    # 2. Initialize Flutterwave
    fw = FlutterwaveService.initialize(payment)

    if fw.get("status") != "success":
        return JsonResponse({
            "error": "Could not initialize payment",
            "detail": fw
        }, status=400)

    checkout_url = fw["data"]["link"]

    return JsonResponse({
        "checkout_url": checkout_url,
        "payment_id": payment.id
    })


# ───────────────────────────────────────────────
#  VERIFY PAYMENT RETURN
# ───────────────────────────────────────────────
@login_required
def verify_payment(request):

    tx_id = request.GET.get("transaction_id")

    if not tx_id:
        messages.error(request, "Invalid payment reference")
        return redirect("home")

    data = FlutterwaveService.verify(tx_id)

    if data.get("status") != "success":
        messages.error(request, "Payment verification failed")
        return redirect("home")

    meta = data["data"]["meta"]
    payment_id = meta.get("payment_id")

    payment = get_object_or_404(Payment, id=payment_id)

    # Mark completed
    PaymentProcessor.mark_completed(payment, tx_id)

    # Create transactions + rental/ownership
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

    result = FlutterwaveService.verify(tx_ref)

    if not result["success"]:
        messages.error(request, "Payment verification failed")
        return redirect("dashboard")

    try:
        payment = Payment.objects.get(id=tx_ref)

        if payment.status != "completed":
            PaymentProcessor.mark_completed(payment, transaction_id)
            PaymentProcessor.create_transactions_and_records(payment)

        messages.success(request, "Payment successful!")

    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found")

    return redirect("dashboard")

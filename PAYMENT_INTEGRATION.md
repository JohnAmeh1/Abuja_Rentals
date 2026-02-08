# Payment Integration Guide

## New Payment System

### Overview
Your application now uses external payment providers instead of internal wallets. The `Payment` model tracks all transactions with external services.

---

## Payment Model Structure

```python
class Payment(models.Model):
    # Provider Information
    user = ForeignKey(User)
    payment_provider = CharField  # 'stripe', 'paypal', 'flutterwave', etc.
    external_payment_id = CharField  # Reference from provider (UNIQUE)
    
    # Payment Details
    amount = DecimalField(12, 2)
    currency = CharField(default='NGN')
    status = CharField(choices=['pending', 'completed', 'failed', 'cancelled'])
    payment_method = CharField  # 'card', 'bank_transfer', 'mobile_money'
    
    # Metadata
    description = TextField
    metadata = JSONField  # Store custom data
    related_property = ForeignKey(Property, null=True)
    related_rental = ForeignKey(PropertyRental, null=True)
    
    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    paid_at = DateTimeField(null=True)  # When payment confirmed
```

---

## Usage Examples

### 1. Creating a Payment Record (Initial)

```python
from .models import Payment
from django.utils import timezone
from decimal import Decimal

# When user initiates property purchase
payment = Payment.objects.create(
    user=request.user,
    payment_provider='stripe',
    amount=Decimal('500000.00'),
    currency='NGN',
    status='pending',
    payment_method='card',
    description=f'Property purchase: {property.title}',
    related_property=property,
    metadata={
        'property_id': property.id,
        'property_title': property.title,
        'tenant_id': request.user.id,
        'intent_type': 'purchase'
    }
)

# User gets payment ID to pass to Stripe
return JsonResponse({
    'payment_id': payment.id,
    'amount': float(payment.amount),
    'currency': payment.currency
})
```

### 2. Handling Stripe Webhook

```python
import stripe
from django.views.decorators.http import csrf_exempt
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle payment success
    if event['type'] == 'charge.succeeded':
        charge = event['data']['object']
        
        # Update payment record
        try:
            payment = Payment.objects.get(
                external_payment_id=charge['id'],
                payment_provider='stripe'
            )
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=payment.user,
                transaction_type='payment',
                amount=Decimal(str(charge['amount'] / 100)),
                payment=payment,
                related_property=payment.related_property,
                description=payment.description,
                status='completed'
            )
            
            # Update property/rental status
            if payment.related_property:
                payment.related_property.status = 'sold'
                payment.related_property.rented_to = payment.user
                payment.related_property.save()
                
        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Payment not found'}, status=404)
    
    # Handle payment failure
    elif event['type'] == 'charge.failed':
        charge = event['data']['object']
        try:
            payment = Payment.objects.get(
                external_payment_id=charge['id'],
                payment_provider='stripe'
            )
            payment.status = 'failed'
            payment.save()
        except Payment.DoesNotExist:
            pass
    
    return JsonResponse({'status': 'success'})
```

### 3. Creating Rental with Payment

```python
def book_property_rental(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        months = calculate_months(start_date, end_date)
        
        # Calculate amount
        monthly_rent = property.price
        total_amount = monthly_rent * months
        deposit = monthly_rent
        total_with_deposit = total_amount + deposit
        
        # Create payment
        payment = Payment.objects.create(
            user=request.user,
            payment_provider='stripe',
            amount=total_with_deposit,
            currency='NGN',
            status='pending',
            payment_method='card',
            description=f'Rental: {property.title} ({months} months)',
            related_property=property,
            metadata={
                'property_id': property.id,
                'start_date': start_date,
                'end_date': end_date,
                'months': months,
                'monthly_rent': float(monthly_rent),
                'deposit': float(deposit),
                'rent_type': 'month'
            }
        )
        
        # Create rental record (initially inactive until payment)
        rental = PropertyRental.objects.create(
            property=property,
            tenant=request.user,
            monthly_rent=monthly_rent,
            start_date=start_date,
            end_date=end_date,
            deposit=deposit,
            total_amount=total_amount,
            is_active=False  # Activate after payment success
        )
        
        # Link payment to rental
        payment.related_rental = rental
        payment.save()
        
        return redirect_to_payment_gateway(payment, rental)
```

### 4. Processing Refund

```python
def process_refund(payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status != 'completed':
        return False, "Payment not completed"
    
    try:
        # For Stripe
        if payment.payment_provider == 'stripe':
            refund = stripe.Refund.create(
                charge=payment.external_payment_id,
                amount=int(payment.amount * 100)  # Stripe uses cents
            )
            
            # Create refund payment record
            refund_payment = Payment.objects.create(
                user=payment.user,
                payment_provider='stripe',
                external_payment_id=refund.id,
                amount=-payment.amount,  # Negative for refund
                currency=payment.currency,
                status='completed',
                payment_method=payment.payment_method,
                description=f'Refund for {payment.description}',
                related_property=payment.related_property,
                related_rental=payment.related_rental,
                paid_at=timezone.now()
            )
            
            # Create refund transaction
            Transaction.objects.create(
                user=payment.user,
                transaction_type='refund',
                amount=payment.amount,
                payment=refund_payment,
                related_property=payment.related_property,
                description=f'Refunded: {payment.description}',
                status='completed'
            )
            
            return True, "Refund processed successfully"
            
    except Exception as e:
        return False, str(e)
```

### 5. Querying Payment History

```python
# Get all payments for a user
user_payments = Payment.objects.filter(user=request.user).order_by('-created_at')

# Get completed payments
completed_payments = Payment.objects.filter(
    user=request.user,
    status='completed'
).order_by('-paid_at')

# Get payments for specific property
property_payments = Payment.objects.filter(
    related_property=property
).order_by('-created_at')

# Get pending payments (payment gateway cleanup)
pending = Payment.objects.filter(
    status='pending',
    created_at__lt=timezone.now() - timedelta(hours=1)
).order_by('created_at')

# Get revenue statistics
from django.db.models import Sum, Count

stats = Payment.objects.filter(
    status='completed'
).aggregate(
    total_revenue=Sum('amount'),
    transaction_count=Count('id'),
    average_transaction=Sum('amount') / Count('id')
)
```

---

## Integration with Different Providers

### Stripe Integration

```python
# views.py
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_payment_intent(request, property_id):
    payment = Payment.objects.get(id=request.POST.get('payment_id'))
    
    intent = stripe.PaymentIntent.create(
        amount=int(payment.amount * 100),  # Stripe uses cents
        currency=payment.currency.lower(),
        metadata={
            'payment_id': payment.id,
            'user_id': payment.user.id,
            'property_id': payment.related_property.id if payment.related_property else None
        }
    )
    
    payment.external_payment_id = intent.id
    payment.save()
    
    return JsonResponse({
        'clientSecret': intent.client_secret,
        'paymentIntentId': intent.id
    })
```

### PayPal Integration

```python
import paypalrestsdk

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

def create_paypal_payment(request, property_id):
    payment = Payment.objects.get(id=request.POST.get('payment_id'))
    
    paypal_payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": request.build_absolute_uri(reverse('paypal_execute')),
            "cancel_url": request.build_absolute_uri(reverse('paypal_cancel'))
        },
        "transactions": [{
            "amount": {
                "total": str(payment.amount),
                "currency": payment.currency
            },
            "description": payment.description
        }]
    })
    
    if paypal_payment.create():
        payment.external_payment_id = paypal_payment.id
        payment.payment_provider = 'paypal'
        payment.save()
        
        return redirect(paypal_payment.links[1].href)
    else:
        payment.status = 'failed'
        payment.save()
        return redirect('property_detail', property_id=property_id)
```

### Flutterwave Integration

```python
import requests

def create_flutterwave_payment(request, property_id):
    payment = Payment.objects.get(id=request.POST.get('payment_id'))
    
    payload = {
        "tx_ref": f"payment_{payment.id}_{timezone.now().timestamp()}",
        "amount": str(payment.amount),
        "currency": payment.currency,
        "payment_options": "card,mobilemoneyghana",
        "redirect_url": request.build_absolute_uri(reverse('flutterwave_callback')),
        "meta": {
            "consumer_id": payment.user.id,
            "payment_id": payment.id
        },
        "customer": {
            "email": payment.user.email,
            "phonenumber": payment.user.userprofile.phone_number,
            "name": payment.user.get_full_name() or payment.user.username
        },
        "customizations": {
            "title": "Abuja Rentals",
            "description": payment.description,
            "logo": request.build_absolute_uri(static('images/logo.png'))
        }
    }
    
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"
    }
    
    response = requests.post(
        "https://api.flutterwave.com/v3/payments",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        payment.external_payment_id = data['data']['id']
        payment.payment_provider = 'flutterwave'
        payment.save()
        
        return redirect(data['data']['link'])
    else:
        payment.status = 'failed'
        payment.save()
        return redirect('payment_failed')
```

---

## Database Queries for Analytics

```python
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

# Daily revenue
today_revenue = Payment.objects.filter(
    status='completed',
    paid_at__date=timezone.now().date()
).aggregate(Sum('amount'))['amount__sum']

# Monthly revenue
month_ago = timezone.now() - timedelta(days=30)
monthly_revenue = Payment.objects.filter(
    status='completed',
    paid_at__gte=month_ago
).aggregate(Sum('amount'))['amount__sum']

# Payment methods breakdown
methods = Payment.objects.filter(
    status='completed'
).values('payment_method').annotate(
    count=Count('id'),
    total=Sum('amount')
).order_by('-total')

# Failed payments rate
failed_rate = Payment.objects.filter(
    created_at__gte=month_ago
).values('status').annotate(count=Count('id'))

# Provider comparison
providers = Payment.objects.filter(
    status='completed'
).values('payment_provider').annotate(
    count=Count('id'),
    total=Sum('amount'),
    average=Avg('amount')
)
```

---

## Security Best Practices

1. **Never expose external payment IDs in frontend** ✅
2. **Always verify webhook signatures** ✅
3. **Store API keys in environment variables** ✅
4. **Use HTTPS for all payment endpoints** ✅
5. **Validate amounts server-side** ✅
6. **Implement rate limiting on payment endpoints** ✅
7. **Log all payment transactions** ✅
8. **Use unique idempotency keys** ✅

---

## Troubleshooting

### Issue: Payment not updating on webhook
**Solution**: 
- Verify webhook secret is correct
- Check webhook endpoint is receiving requests
- Verify event type matches your code

### Issue: Duplicate payments
**Solution**:
- Use `unique_together` on external_payment_id + provider
- Implement idempotency keys

### Issue: Amount mismatch
**Solution**:
- Always convert to smallest currency unit (cents for USD, etc.)
- Store as Decimal in database (not float)
- Validate server-side before processing

---

## Migration Path

```python
# 1. Create Payment records for old transactions
from .models import Payment, Transaction

for transaction in Transaction.objects.all():
    Payment.objects.get_or_create(
        user=transaction.user,
        defaults={
            'payment_provider': 'manual',
            'amount': transaction.amount,
            'currency': 'NGN',
            'status': 'completed' if transaction.status == 'completed' else 'failed',
            'description': transaction.description,
            'created_at': transaction.created_at
        }
    )

# 2. Test payment flow
# 3. Deploy to production
```

---

## Next Steps

1. Choose payment provider (Stripe recommended)
2. Get API credentials
3. Implement payment initiation view
4. Set up webhook handler
5. Test in sandbox environment
6. Deploy to production
7. Monitor transactions

---

**Ready to go live?** Contact your payment provider's support for production API keys!

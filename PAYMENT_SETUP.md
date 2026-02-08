# Payment Integration Guide

## Overview

Your rental property system now has a complete Payment API built on the `Payment` and `Transaction` models. This enables seamless payment processing for student property rentals with support for multiple payment providers (Stripe, PayPal, Flutterwave, etc.).

## Architecture

### Models
- **Payment**: Tracks payment records with status, provider, and amounts
- **Transaction**: Audit trail for all financial activities

### Files
- `payment_utils.py` - Core payment processing logic
- `payment_views.py` - Payment API endpoints
- `urls.py` - Payment URL routes

## Quick Start

### 1. Initialize a Payment for Student Property Rental

```python
from .payment_utils import PaymentProcessor

# Process rental payment
result = PaymentProcessor.process_rental_payment(
    user=request.user,
    student_property=property_object,
    duration_months=6
)

if result['success']:
    payment = result['payment']
    total_amount = result['total_amount']
    platform_fee = result['platform_fee']
else:
    error = result['message']
```

### 2. API Endpoint Usage

#### Initiate Payment (POST)
```
POST /payment/student-property/{property_id}/initiate/

Parameters:
- duration_months: integer (1-24, default: 1)
- payment_method: string ('stripe', 'paypal', etc.)

Response:
{
    "success": true,
    "payment_id": 123,
    "amount": 50000.00,
    "client_secret": "pi_xxxxx",  // For Stripe
    "redirect_url": "/payment/123/confirmation/"
}
```

#### Payment Confirmation
```
GET /payment/{payment_id}/confirmation/
```

#### Mark Payment Complete
```
GET /payment/{payment_id}/success/?external_id=stripe_charge_id&provider=stripe
```

#### Handle Payment Failure
```
GET /payment/{payment_id}/failed/?reason=card_declined
```

#### Get Payment History
```
GET /payment/history/
```

#### Get Payment Receipt
```
GET /payment/{payment_id}/receipt/
```

## Integration Examples

### With Stripe

```python
# In your payment_utils.py, configure Stripe:
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
webhook_secret = settings.STRIPE_WEBHOOK_SECRET

# The system will automatically:
# 1. Create a Stripe PaymentIntent
# 2. Handle webhook callbacks
# 3. Update payment status
```

### With HTML/JavaScript

```html
<!-- Initiate payment -->
<form method="POST" action="/payment/student-property/{{ property.id }}/initiate/">
    {% csrf_token %}
    <input type="hidden" name="duration_months" value="6">
    <input type="hidden" name="payment_method" value="stripe">
    <button type="submit">Proceed to Payment</button>
</form>

<!-- After successful Stripe payment: -->
<script>
    // Redirect to success page with payment ID
    window.location.href = `/payment/${paymentId}/success/?external_id=${stripeChargeId}&provider=stripe`;
</script>
```

## Payment Flow

```
1. User clicks "Rent Property"
   ↓
2. POST /payment/student-property/{id}/initiate/
   ↓
3. PaymentProcessor.process_rental_payment() creates:
   - Payment record (status: pending)
   - Transaction record (type: property_rental)
   ↓
4. Redirect to payment provider (Stripe, PayPal, etc.)
   ↓
5. User completes payment
   ↓
6. Webhook or redirect callback
   ↓
7. GET /payment/{id}/success/ 
   - Updates Payment status to "completed"
   - Updates Transaction status to "completed"
   ↓
8. User sees confirmation
```

## Payment Statuses

- **pending**: Payment initiated, awaiting provider confirmation
- **completed**: Payment successful and verified
- **failed**: Payment declined or error occurred
- **cancelled**: User cancelled payment

## Transaction Types

- **payment**: General payment
- **property_rental**: Payment for renting a property
- **platform_fee**: Platform commission (calculated at 2%)
- **refund**: Refund transaction

## Admin Features

### View Payment History
```python
from .models import Payment, Transaction

# Get all payments
payments = Payment.objects.all()

# Filter by status
completed = Payment.objects.filter(status='completed')
pending = Payment.objects.filter(status='pending')

# Get user payments
user_payments = Payment.objects.filter(user=user_id)

# Get transaction history
transactions = Transaction.objects.filter(user=user_id)
```

### Create Refund
```python
from .payment_utils import PaymentProcessor

result = PaymentProcessor.create_refund(
    payment_id=123,
    refund_amount=50000,  # Optional, defaults to full amount
    reason='User requested cancellation'
)
```

## Settings Configuration

Add to your `settings.py`:

```python
# Payment Provider Keys
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')

# Platform Settings
PLATFORM_FEE_PERCENTAGE = Decimal('0.02')  # 2%
CURRENCY = 'NGN'
```

## Environment Variables

Add to `.env`:

```
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

PAYPAL_CLIENT_ID=xxxxx
PAYPAL_CLIENT_SECRET=xxxxx
```

## Templates Needed

Create the following templates:

1. `templates/payment/confirmation.html` - Payment review
2. `templates/payment/success.html` - Success confirmation
3. `templates/payment/failed.html` - Failure handling
4. `templates/payment/receipt.html` - Invoice/receipt
5. `templates/payment/history.html` - Payment history

## Helper Functions

```python
from .payment_utils import (
    process_student_property_rental,
    complete_payment,
    get_user_payment_history,
    get_user_transactions
)

# Quick payment processing
result = process_student_property_rental(user, property, months=6)

# Mark payment complete
PaymentProcessor.mark_payment_completed(payment_id, external_id, provider)

# Get user history
payments = get_user_payment_history(user, limit=10)
transactions = get_user_transactions(user, limit=20)
```

## Error Handling

```python
result = PaymentProcessor.process_rental_payment(user, property, months)

if result['success']:
    payment = result['payment']
    # Proceed with payment
else:
    error_message = result['message']
    # Handle error
    
# Specific error checks:
if not result.get('payment'):
    print("Payment creation failed")
    
if result.get('transaction'):
    print("Transaction recorded successfully")
```

## Security Notes

- All payment IDs are user-scoped (users can only see their own payments)
- Use `@login_required` on all payment views
- Validate payment amounts server-side
- Never store full credit card numbers
- Use HTTPS for all payment endpoints
- Implement proper webhook signature verification
- Keep API keys in environment variables only

## Testing

```python
# Test payment creation
result = PaymentProcessor.process_rental_payment(user, property, 1)
assert result['success'] == True
assert result['payment'].status == 'pending'

# Test marking complete
PaymentProcessor.mark_payment_completed(payment_id)
payment = Payment.objects.get(id=payment_id)
assert payment.status == 'completed'

# Test refund
PaymentProcessor.create_refund(payment_id, reason='Test refund')
```

## Webhook Setup (Stripe Example)

1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://yoursite.com/webhook/stripe/`
3. Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`
4. Copy webhook secret to `.env` as `STRIPE_WEBHOOK_SECRET`

## Next Steps

1. Create payment templates
2. Set up payment provider accounts (Stripe, PayPal)
3. Add environment variables
4. Test payment flow in development
5. Deploy with production keys
6. Monitor payment transactions in admin

## Support

For issues or questions:
- Check `console.log("[v0] ...")` output in browser console
- Review payment server logs
- Verify payment model records in Django admin
- Check transaction history for audit trail

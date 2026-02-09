
"""
Payment processing utilities for rental properties.
Handles Payment and Transaction record creation, status updates, and webhooks.
"""

from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Payment, Transaction, StudentProperty, PropertyRental
import uuid
import json


class PaymentProcessor:
    """Main payment processing handler"""
    
    @staticmethod
    def create_payment(
        user,
        amount,
        description='',
        payment_provider='pending',
        payment_method='',
        related_property=None,
        related_rental=None,
        metadata=None,
        currency='NGN'
    ):
        """
        Create a new payment record.
        
        Args:
            user: User object making the payment
            amount: Decimal amount to charge
            description: Payment description
            payment_provider: e.g., 'stripe', 'paypal', 'pending'
            payment_method: e.g., 'card', 'bank_transfer'
            related_property: Related Property object (optional)
            related_rental: Related PropertyRental object (optional)
            metadata: Additional JSON data to store
            currency: Currency code (default: NGN)
        
        Returns:
            Payment object
        """
        if metadata is None:
            metadata = {}
        
        payment = Payment.objects.create(
            user=user,
            amount=amount,
            currency=currency,
            description=description,
            payment_provider=payment_provider,
            payment_method=payment_method,
            status='pending',
            related_property=related_property,
            related_rental=related_rental,
            metadata=metadata
        )
        
        print(f"[v0] Payment created: {payment.id} for user {user.username}, amount: ₦{amount}")
        return payment
    
    @staticmethod
    def create_transaction(
        user,
        transaction_type,
        amount,
        description='',
        related_property=None,
        related_property_title='',
        payment=None,
        status='completed'
    ):
        """
        Create a transaction record for audit trail.
        
        Args:
            user: User object
            transaction_type: 'payment', 'refund', 'property_rental', 'platform_fee'
            amount: Decimal amount
            description: Transaction description
            related_property: Related Property object (optional)
            related_property_title: Property title (optional)
            payment: Related Payment object (optional)
            status: Transaction status (default: completed)
        
        Returns:
            Transaction object
        """
        transaction = Transaction.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            related_property=related_property,
            related_property_title=related_property_title,
            payment=payment,
            status=status
        )
        
        print(f"[v0] Transaction created: {transaction.reference} - {transaction_type} - ₦{amount}")
        return transaction
    
    @staticmethod
    def process_rental_payment(user, student_property, duration_months=1):
        """
        Process payment for a student property rental.
        Creates Payment and Transaction records.
        
        Args:
            user: User renting the property
            student_property: StudentProperty object
            duration_months: Rental duration in months
        
        Returns:
            dict: {'success': bool, 'payment': Payment, 'transaction': Transaction, 'message': str}
        """
        try:
            # Validate inputs
            if not isinstance(user, User):
                return {
                    'success': False,
                    'message': 'Invalid user object',
                    'payment': None,
                    'transaction': None
                }
            
            if not student_property:
                return {
                    'success': False,
                    'message': 'Invalid property',
                    'payment': None,
                    'transaction': None
                }
            
            # Calculate amounts
            total_amount = student_property.price * Decimal(str(duration_months))
            platform_fee = total_amount * Decimal('0.02')
            
            # Create payment record
            metadata = {
                'property_id': student_property.id,
                'property_title': student_property.title,
                'duration_months': duration_months,
                'platform_fee': str(platform_fee),
                'net_amount': str(total_amount * Decimal('0.98'))
            }
            
            payment = PaymentProcessor.create_payment(
                user=user,
                amount=total_amount,
                description=f"Rental payment for {student_property.title}",
                payment_provider='pending',
                related_property=None,  # StudentProperty not compatible with Property FK
                metadata=metadata,
                currency='NGN'
            )
            
            # Create transaction record
            transaction = PaymentProcessor.create_transaction(
                user=user,
                transaction_type='property_rental',
                amount=total_amount,
                description=f"Rental: {student_property.title} - {duration_months} month(s)",
                related_property_title=student_property.title,
                payment=payment,
                status='pending'
            )
            
            return {
                'success': True,
                'payment': payment,
                'transaction': transaction,
                'message': f'Payment initiated for ₦{total_amount}',
                'total_amount': total_amount,
                'platform_fee': platform_fee
            }
            
        except Exception as e:
            print(f"[v0] Error processing rental payment: {str(e)}")
            return {
                'success': False,
                'message': f'Payment error: {str(e)}',
                'payment': None,
                'transaction': None
            }
    
    @staticmethod
    def mark_payment_completed(payment_id, external_payment_id=None, payment_provider='stripe'):
        """
        Mark a payment as completed (after successful provider confirmation).
        
        Args:
            payment_id: Payment ID to mark complete
            external_payment_id: External provider payment ID (e.g., Stripe charge ID)
            payment_provider: Payment provider name
        
        Returns:
            dict: {'success': bool, 'payment': Payment, 'message': str}
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.payment_provider = payment_provider
            if external_payment_id:
                payment.external_payment_id = external_payment_id
            payment.save()
            
            # Update related transaction
            if payment.transactions.exists():
                for transaction in payment.transactions.all():
                    transaction.status = 'completed'
                    transaction.save()
            
            print(f"[v0] Payment {payment_id} marked as completed")
            
            return {
                'success': True,
                'payment': payment,
                'message': 'Payment completed successfully'
            }
            
        except Payment.DoesNotExist:
            return {
                'success': False,
                'payment': None,
                'message': 'Payment not found'
            }
        except Exception as e:
            print(f"[v0] Error marking payment completed: {str(e)}")
            return {
                'success': False,
                'payment': None,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def mark_payment_failed(payment_id, reason=''):
        """
        Mark a payment as failed.
        
        Args:
            payment_id: Payment ID to mark failed
            reason: Failure reason
        
        Returns:
            dict: {'success': bool, 'payment': Payment, 'message': str}
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            
            payment.status = 'failed'
            payment.metadata = payment.metadata or {}
            payment.metadata['failure_reason'] = reason
            payment.save()
            
            # Update related transaction
            if payment.transactions.exists():
                for transaction in payment.transactions.all():
                    transaction.status = 'failed'
                    transaction.save()
            
            print(f"[v0] Payment {payment_id} marked as failed: {reason}")
            
            return {
                'success': True,
                'payment': payment,
                'message': f'Payment failed: {reason}'
            }
            
        except Payment.DoesNotExist:
            return {
                'success': False,
                'payment': None,
                'message': 'Payment not found'
            }
        except Exception as e:
            print(f"[v0] Error marking payment failed: {str(e)}")
            return {
                'success': False,
                'payment': None,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def create_refund(payment_id, refund_amount=None, reason=''):
        """
        Create a refund transaction for a payment.
        
        Args:
            payment_id: Payment ID to refund
            refund_amount: Amount to refund (default: full amount)
            reason: Refund reason
        
        Returns:
            dict: {'success': bool, 'transaction': Transaction, 'message': str}
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            
            if refund_amount is None:
                refund_amount = payment.amount
            
            # Validate refund amount
            if refund_amount > payment.amount:
                return {
                    'success': False,
                    'transaction': None,
                    'message': 'Refund amount exceeds payment amount'
                }
            
            # Create refund transaction
            refund_transaction = PaymentProcessor.create_transaction(
                user=payment.user,
                transaction_type='refund',
                amount=refund_amount,
                description=f'Refund for payment {payment.id}: {reason}',
                related_property_title=payment.description,
                payment=payment,
                status='completed'
            )
            
            # Update payment metadata
            payment.metadata = payment.metadata or {}
            payment.metadata['refunded_amount'] = str(refund_amount)
            payment.metadata['refund_reason'] = reason
            payment.save()
            
            print(f"[v0] Refund created for payment {payment_id}: ₦{refund_amount}")
            
            return {
                'success': True,
                'transaction': refund_transaction,
                'message': f'Refund of ₦{refund_amount} created'
            }
            
        except Payment.DoesNotExist:
            return {
                'success': False,
                'transaction': None,
                'message': 'Payment not found'
            }
        except Exception as e:
            print(f"[v0] Error creating refund: {str(e)}")
            return {
                'success': False,
                'transaction': None,
                'message': f'Error: {str(e)}'
            }


class PaymentIntegration:
    """
    Payment provider integrations (Stripe, PayPal, Flutterwave, etc.)
    Extend this class to add specific provider implementations.
    """
    
    @staticmethod
    def create_stripe_payment_intent(payment):
        """
        Create a Stripe Payment Intent for the given Payment record.
        Requires: pip install stripe
        """
        try:
            import stripe
            stripe.api_key = 'sk_test_YOUR_KEY_HERE'  # Load from settings.STRIPE_SECRET_KEY
            
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Convert to cents
                currency=payment.currency.lower(),
                metadata={
                    'payment_id': payment.id,
                    'user_id': payment.user.id,
                    'description': payment.description
                }
            )
            
            payment.external_payment_id = intent.id
            payment.metadata = {
                'stripe_intent_id': intent.id,
                'stripe_client_secret': intent.client_secret
            }
            payment.save()
            
            return intent
        except ImportError:
            print("[v0] Stripe not installed. Install with: pip install stripe")
            return None
        except Exception as e:
            print(f"[v0] Error creating Stripe intent: {str(e)}")
            return None
    
    @staticmethod
    def verify_stripe_webhook(payload, sig_header):
        """
        Verify and process Stripe webhook events.
        """
        try:
            import stripe
            stripe.api_key = 'sk_test_YOUR_KEY_HERE'
            webhook_secret = 'whsec_YOUR_WEBHOOK_SECRET'
            
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                payment_id = payment_intent['metadata'].get('payment_id')
                
                result = PaymentProcessor.mark_payment_completed(
                    payment_id=payment_id,
                    external_payment_id=payment_intent['id'],
                    payment_provider='stripe'
                )
                return result
            
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                payment_id = payment_intent['metadata'].get('payment_id')
                
                result = PaymentProcessor.mark_payment_failed(
                    payment_id=payment_id,
                    reason=payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
                )
                return result
            
            return {'success': True, 'message': 'Event processed'}
            
        except Exception as e:
            print(f"[v0] Error verifying Stripe webhook: {str(e)}")
            return {'success': False, 'message': str(e)}


# Helper functions for quick access
def process_student_property_rental(user, student_property, duration_months=1):
    """Quick function to process rental payment"""
    return PaymentProcessor.process_rental_payment(user, student_property, duration_months)


def complete_payment(payment_id, external_id=None, provider='stripe'):
    """Quick function to mark payment complete"""
    return PaymentProcessor.mark_payment_completed(payment_id, external_id, provider)


def get_user_payment_history(user, limit=10):
    """Get user's payment history"""
    return Payment.objects.filter(user=user).order_by('-created_at')[:limit]


def get_user_transactions(user, limit=20):
    """Get user's transaction history"""
    return Transaction.objects.filter(user=user).order_by('-created_at')[:limit]




# 
# 
# 
# 
# 

"""
Payment API views for handling payment processing, confirmations, and webhooks.
"""

from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import json

from .models import Payment, Transaction, StudentProperty, Property, UserProfile
from .payment_utils import PaymentProcessor, PaymentIntegration

class PropertyAdapter:
    """Make Property and StudentProperty behave the same"""

    @staticmethod
    def get_any(id):
        from .models import Property, StudentProperty

        try:
            p = Property.objects.get(id=id)
            return p, "normal"
        except:
            pass

        try:
            p = StudentProperty.objects.get(id=id)
            return p, "student"
        except:
            pass

        return None, None



def complete_property_sale(property_id, sale_price):
    """Complete a property sale and distribute funds"""
    try:
        property = Property.objects.get(id=property_id)
        
        property.status = 'sold'
        property.sold_at = timezone.now()
        property.sale_price = sale_price
        property.save()
        
        platform_fee_percentage = Decimal('0.05')
        platform_fee_amount = sale_price * platform_fee_percentage
        seller_amount = sale_price - platform_fee_amount
        
        # Get admin user (assuming first admin or specific admin)
        # You might want to adjust this based on your admin identification logic
        admin_profile = UserProfile.objects.filter(user_type='admin').first()
        if admin_profile:
        
            # Create platform fee transaction for admin
            Transaction.objects.create(
                transaction_type='platform_fee',
                amount=platform_fee_amount,
                description=f'Platform fee from sale of {property.title}',
                property=property,
                reference=f'PF-{property.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
            )
        


        # Create property sale transaction for seller
        Transaction.objects.create(
            transaction_type='property_sale',
            amount=seller_amount,
            description=f'Sale of {property.title}',
            property=property,
            reference=f'SALE-{property.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
        )
        
        # Also create a transaction record for the platform fee deduction from seller
        Transaction.objects.create(
            transaction_type='platform_fee_payment',
            amount=-platform_fee_amount,
            description=f'Platform fee for sale of {property.title}',
            property=property,
            reference=f'PFEE-{property.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
        )
        
        return True, "Sale completed successfully"
        
    except Property.DoesNotExist:
        return False, "Property not found"
    except Exception as e:
        return False, f"Error completing sale: {str(e)}"
    
   

@login_required
def process_property_payment(request, property_id):
    """
    Process property purchase or rental payment
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('property_detail', property_id=property_id)
    
    property_obj = get_object_or_404(Property, id=property_id)
    user = request.user
    
    # Verify property is available
    if property_obj.status != 'available':
        messages.error(request, 'This property is no longer available.')
        return redirect('property_detail', property_id=property_id)
    
    # Verify user is not the owner
    if property_obj.owner == user:
        messages.error(request, 'You cannot purchase your own property.')
        return redirect('property_detail', property_id=property_id)
    


    try:
        # Use database transaction to ensure atomicity
        from django.db import transaction as db_transaction
        
        with db_transaction.atomic():
            platform_fee = property_obj.platform_fee
            seller_amount = property_obj.price - platform_fee
            

            # 2. Create transaction for buyer (debit)
            buyer_transaction = Transaction.objects.create(
                transaction_type='property_purchase' if property_obj.purpose == 'sale' else 'rental_payment',
                amount=-property_obj.price,
                description=f'{"Purchase" if property_obj.purpose == "sale" else "Rental payment"} of {property_obj.title}',
                reference=f'BUYER-{property_obj.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                related_property_id=property_obj.id,
                related_property_title=property_obj.title,
                # user_id=user.id
                user=user
                
            )
            

            

            # 5. Create transaction for seller (credit)
            seller_transaction = Transaction.objects.create(
                transaction_type='property_sale',
                amount=seller_amount,
                description=f'{"Sale" if property_obj.purpose == "sale" else "Rental"} of {property_obj.title} (after 5% platform fee)',
                reference=f'SELLER-{property_obj.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                related_property_id=property_obj.id,
                related_property_title=property_obj.title,
                # user_id = property.user.id
                user = property_obj.owner
            )
            
    
            # 9. Update property status to sold/rented
            property_obj.status = 'sold'
            property_obj.sold_at = timezone.now()
            property_obj.sale_price = property_obj.price
            
            if property_obj.purpose == 'sale':
                property_obj.sold_to = user
            else:
                property_obj.rented_to = user
            
            property_obj.save()
            
            # 10. Create ownership or rental record
            if property_obj.purpose == 'sale':
                # Create property ownership record
                ownership = PropertyOwnership.objects.create(
                    property=property_obj,
                    owner=user,
                    purchase_price=property_obj.price,
                )
                
                success_message = f'ðŸŽ‰ Congratulations! You have successfully purchased {property_obj.title} for ₦{property_obj.price:,.2f}'
            else:
                # Create rental record using calendar-accurate month arithmetic
                from dateutil.relativedelta import relativedelta

                start_date = timezone.now().date()
                duration_months = int(property_obj.rent_duration_months or 12)
                end_date = start_date + relativedelta(months=duration_months)

                rental = PropertyRental.objects.create(
                    property=property_obj,
                    tenant=user,
                    monthly_rent=(property_obj.price / Decimal(str(duration_months))) if duration_months else property_obj.price,
                    start_date=start_date,
                    end_date=end_date,
                    deposit=Decimal('0.00'),
                    total_amount=property_obj.price,
                    is_active=True
                )
                
                success_message = f'ðŸŽ‰ Congratulations! You have successfully rented {property_obj.title} for {duration_months} months at ₦{property_obj.price:,.2f}'
            
            # Success messages
            messages.success(request, success_message)
            messages.info(request, f'ðŸ’° Payment Details: ₦{property_obj.price:,.2f} paid. Platform fee of ₦{platform_fee:,.2f} (5%) deducted. Seller receives ₦{seller_amount:,.2f}')
        return redirect('property_detail', property_id=property_id)
        
            
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Payment processing error: {str(e)}")
        print(traceback.format_exc())
        
        messages.error(request, f'Payment failed: {str(e)}. Please try again or contact support.')
        return redirect('property_detail', property_id=property_id)


@login_required
def initiate_payment(request, property_id):

    property_obj, ptype = PropertyAdapter.get_any(property_id)

    if not property_obj:
        return JsonResponse({"error": "Property not found"}, status=404)

    # 1. Create internal payment
    payment = PaymentProcessor.create_payment(
        user=request.user,
        amount=property_obj.price,
        description=f"Payment for {property_obj.title}",
        payment_provider="flutterwave",
        related_property=None,
        metadata={
            "property_id": property_obj.id,
            "property_type": ptype
        }
    )

    # 2. Initialize Flutterwave
    fw = Flutterwave.initialize(payment)

    if fw["status"] != "success":
        return JsonResponse({"error": "Could not start payment"}, status=400)

    # Save reference
    payment.external_payment_id = fw["data"]["link"]
    payment.save()

    return JsonResponse({
        "checkout_url": fw["data"]["link"]
    })


@login_required
def payment_confirmation(request, payment_id):
    """
    Display payment confirmation page.
    """
    try:
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)
        
        context = {
            'payment': payment,
            'amount': payment.amount,
            'currency': payment.currency,
            'description': payment.description,
            'page_title': 'Payment Confirmation'
        }
        
        return render(request, 'payment/confirmation.html', context)
    except Exception as e:
        print(f"[v0] Error loading payment confirmation: {str(e)}")
        messages.error(request, 'Error loading payment details')
        return redirect('home')


@login_required
@require_http_methods(["GET", "POST"])
def payment_success(request, payment_id):
    """
    Handle successful payment.
    """
    try:
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)
        
        # Mark payment as completed
        result = PaymentProcessor.mark_payment_completed(
            payment_id=payment_id,
            external_payment_id=request.GET.get('external_id'),
            payment_provider=request.GET.get('provider', 'manual')
        )
        
        if result['success']:
            messages.success(request, f'Payment of ₦{payment.amount} completed successfully!')
            print(f"[v0] Payment {payment_id} successful for user {request.user.username}")
            
            context = {
                'payment': result['payment'],
                'success': True,
                'page_title': 'Payment Successful'
            }
        else:
            messages.error(request, result['message'])
            context = {
                'payment': payment,
                'success': False,
                'message': result['message'],
                'page_title': 'Payment Error'
            }
        
        return render(request, 'payment/success.html', context)
        
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found')
        return redirect('home')
    except Exception as e:
        print(f"[v0] Error processing payment success: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
        return redirect('home')


@login_required
@require_http_methods(["GET"])
def payment_failed(request, payment_id):
    """
    Handle failed payment.
    """
    try:
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)
        
        # Mark payment as failed
        reason = request.GET.get('reason', 'User declined payment')
        result = PaymentProcessor.mark_payment_failed(
            payment_id=payment_id,
            reason=reason
        )
        
        messages.warning(request, f'Payment failed: {reason}')
        print(f"[v0] Payment {payment_id} failed for user {request.user.username}: {reason}")
        
        context = {
            'payment': result['payment'],
            'reason': reason,
            'page_title': 'Payment Failed'
        }
        
        return render(request, 'payment/failed.html', context)
        
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found')
        return redirect('home')
    except Exception as e:
        print(f"[v0] Error processing payment failure: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
        return redirect('home')


@login_required
@require_http_methods(["GET"])
def payment_history(request):
    """
    Display user's payment and transaction history.
    """
    try:
        payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:50]
        transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:50]
        
        # Calculate statistics
        total_paid = sum(p.amount for p in payments.filter(status='completed'))
        total_pending = sum(p.amount for p in payments.filter(status='pending'))
        total_failed = sum(p.amount for p in payments.filter(status='failed'))
        
        context = {
            'payments': payments,
            'transactions': transactions,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'total_failed': total_failed,
            'page_title': 'Payment History'
        }
        
        return render(request, 'payment/history.html', context)
        
    except Exception as e:
        print(f"[v0] Error loading payment history: {str(e)}")
        messages.error(request, 'Error loading payment history')
        return redirect('home')


@login_required
@require_http_methods(["POST"])
def request_refund(request, payment_id):
    """
    Request a refund for a payment.
    """
    try:
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)
        
        if payment.status != 'completed':
            return JsonResponse({
                'success': False,
                'message': 'Can only refund completed payments'
            }, status=400)
        
        reason = request.POST.get('reason', '')
        
        # Create refund transaction
        result = PaymentProcessor.create_refund(
            payment_id=payment_id,
            refund_amount=payment.amount,
            reason=reason
        )
        
        if result['success']:
            messages.success(request, f'Refund of ₦{payment.amount} has been initiated')
            return JsonResponse({'success': True, 'message': 'Refund initiated'})
        else:
            return JsonResponse({
                'success': False,
                'message': result['message']
            }, status=400)
            
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Payment not found'}, status=404)
    except Exception as e:
        print(f"[v0] Error requesting refund: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt  # Stripe webhooks don't have CSRF tokens
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    Stripe will POST payment events to this endpoint.
    """
    try:
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        
        # Verify and process webhook
        result = PaymentIntegration.verify_stripe_webhook(payload, sig_header)
        
        if result['success']:
            print(f"[v0] Stripe webhook processed: {result.get('message')}")
            return JsonResponse({'status': 'success'})
        else:
            print(f"[v0] Stripe webhook error: {result.get('message')}")
            return JsonResponse({'status': 'error', 'message': result.get('message')}, status=400)
            
    except Exception as e:
        print(f"[v0] Error processing Stripe webhook: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def payment_receipt(request, payment_id):
    """
    Display payment receipt/invoice.
    """
    try:
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)
        
        context = {
            'payment': payment,
            'user': request.user,
            'page_title': f'Receipt - {payment.reference}'
        }
        
        return render(request, 'payment/receipt.html', context)
        
    except Payment.DoesNotExist:
        messages.error(request, 'Receipt not found')
        return redirect('home')
    except Exception as e:
        print(f"[v0] Error loading receipt: {str(e)}")
        messages.error(request, 'Error loading receipt')
        return redirect('home')

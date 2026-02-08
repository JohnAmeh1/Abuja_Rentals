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

from .models import Payment, Transaction, StudentProperty
from .payment_utils import PaymentProcessor, PaymentIntegration


@login_required
@require_http_methods(["POST"])
def initiate_student_property_payment(request, property_id):
    """
    Initiate payment for a student property rental.
    
    POST data:
        - duration_months: Number of months to rent (optional, default: 1)
        - payment_method: Payment method ('stripe', 'paypal', etc.)
    
    Returns:
        JSON with payment details and redirect URL
    """
    try:
        # Get the property
        student_property = get_object_or_404(StudentProperty, id=property_id)
        
        # Get payment parameters
        duration_months = int(request.POST.get('duration_months', 1))
        payment_method = request.POST.get('payment_method', 'stripe')
        
        # Validate duration
        if duration_months < 1 or duration_months > 24:
            return JsonResponse({
                'success': False,
                'message': 'Duration must be between 1 and 24 months'
            }, status=400)
        
        # Process the payment
        result = PaymentProcessor.process_rental_payment(
            user=request.user,
            student_property=student_property,
            duration_months=duration_months
        )
        
        if not result['success']:
            return JsonResponse({
                'success': False,
                'message': result['message']
            }, status=400)
        
        payment = result['payment']
        
        print(f"[v0] Payment initiated: {payment.id} for user {request.user.username}")
        
        # Redirect to appropriate payment provider
        if payment_method == 'stripe':
            # Create Stripe payment intent
            intent = PaymentIntegration.create_stripe_payment_intent(payment)
            if intent:
                return JsonResponse({
                    'success': True,
                    'payment_id': payment.id,
                    'client_secret': intent.client_secret,
                    'amount': float(payment.amount),
                    'message': 'Payment ready',
                    'redirect_url': f'/payment/stripe/{payment.id}/checkout/'
                })
        
        # Default: redirect to payment confirmation
        return JsonResponse({
            'success': True,
            'payment_id': payment.id,
            'amount': float(payment.amount),
            'message': 'Payment initiated',
            'redirect_url': f'/payment/{payment.id}/confirmation/'
        })
        
    except StudentProperty.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Property not found'
        }, status=404)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': f'Invalid parameters: {str(e)}'
        }, status=400)
    except Exception as e:
        print(f"[v0] Error initiating payment: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


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

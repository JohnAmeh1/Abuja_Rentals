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

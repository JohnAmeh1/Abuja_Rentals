import requests
from django.conf import settings

class Flutterwave:
    BASE_URL = "https://api.flutterwave.com/v3"

    @staticmethod
    def headers():
        return {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def initialize(payment):
        payload = {
            "tx_ref": f"RENT_{payment.id}",
            "amount": float(payment.amount),
            "currency": "NGN",
            "redirect_url": settings.FLUTTERWAVE_REDIRECT_URL,
            "customer": {
                "email": payment.user.email,
                "name": payment.user.username
            },
            "meta": {
                "payment_id": payment.id
            }
        }

        res = requests.post(
            f"{Flutterwave.BASE_URL}/payments",
            json=payload,
            headers=Flutterwave.headers()
        )

        return res.json()

    @staticmethod
    def verify(transaction_id):
        res = requests.get(
            f"{Flutterwave.BASE_URL}/transactions/{transaction_id}/verify",
            headers=Flutterwave.headers()
        )
        return res.json()

from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from users.models import KrisshakProfile
from .models import Payment
from .serializers import PaymentCreateSerializer, PaymentListSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from django.db.models import Q
import razorpay
from django.conf import settings
from django.core.mail import send_mail

User = get_user_model()

# 🎯 Step 1: Get Krisshak Rate
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_krisshak_price(request, user_id):
    try:
        profile = KrisshakProfile.objects.get(user__id=user_id)
        return Response({'price': float(profile.price)})
    except KrisshakProfile.DoesNotExist:
        return Response({'error': 'Krisshak profile not found'}, status=404)

# 💳 Step 2: Initiate a payment
class PaymentCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentCreateSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, status='pending')

# 📄 Step 3: View your payments (sent or received)
class PaymentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentListSerializer

    def get_queryset(self):
        return Payment.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        ).order_by('-created_at')

# ✅ Step 4: Create Razorpay Payment Order
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_razorpay_order(request):
    """Generate Razorpay payment order including ₹11 platform fee"""
    try:
        base_amount = int(request.data['amount']) * 100  # Convert ₹ to paise
        recipient_id = request.data['recipient_id']
        purpose = request.data.get('purpose', 'Krisshak Service')  # Ensure purpose is included
        platform_fee = 1100  # ₹11 in paise
        total_amount = base_amount + platform_fee  # Bhooswami pays (Krisshak price + ₹11 fee)

        recipient = User.objects.get(id=recipient_id)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        order_data = {
            "amount": total_amount,
            "currency": "INR",
            "receipt": f"txn_{request.user.id}_{recipient.id}",
            "payment_capture": 1,
            "notes": {"purpose": purpose}  # Added purpose field
        }

        razorpay_order = client.order.create(data=order_data)

        # Store pending payment in DB
        payment = Payment.objects.create(
            sender=request.user,
            recipient=recipient,
            amount=(base_amount / 100),  # Only Krisshak's portion
            platform_fee=(platform_fee / 100),  # ₹11 platform fee
            status='pending',
            external_payment_id=razorpay_order["id"],
            purpose=purpose  # Store purpose explicitly in DB
        )

        return Response({
            "order_id": razorpay_order["id"],
            "key": settings.RAZORPAY_KEY_ID
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# 🔁 Step 5: Handle Razorpay Webhook & Trigger Real Payout
@api_view(['POST'])
def razorpay_webhook(request):
    """Handle Razorpay webhook, confirm & trigger real payment, and distribute funds"""
    try:
        payload = request.data
        event = payload.get("event")

        if event == "payment.captured":
            razorpay_payment_id = payload["payload"]["payment"]["entity"]["id"]
            razorpay_order_id = payload["payload"]["payment"]["entity"]["order_id"]

            payment = Payment.objects.get(external_payment_id=razorpay_order_id)

            # Ensure recipient has bank/UPI details before sending payouts
            if not payment.recipient.account_number and not payment.recipient.upi_id:
                return Response({"error": "Recipient is missing payment details. Payout aborted."}, status=status.HTTP_400_BAD_REQUEST)

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Send ₹11 platform fee to my account
            payout_data_platform = {
                "account_number": settings.PLATFORM_ACCOUNT_NUMBER,
                "amount": int(payment.platform_fee * 100),
                "currency": "INR",
                "purpose": "platform_fee",
                "mode": "IMPS"
            }
            payout_response_platform = client.payout.create(data=payout_data_platform)

            # Send actual payment to Krisshak
            payout_data_krisshak = {
                "account_number": payment.recipient.account_number if payment.recipient.account_number else None,
                "upi_id": payment.recipient.upi_id if payment.recipient.upi_id else None,
                "amount": int(payment.amount * 100),
                "currency": "INR",
                "purpose": payment.purpose,  # Ensure the stored purpose is used
                "mode": "IMPS" if payment.recipient.account_number else "UPI",
            }
            payout_response_krisshak = client.payout.create(data=payout_data_krisshak)

           # ✅ Ensure Razorpay confirms payout before updating DB and Marking payment as completed
            if payout_response_krisshak["status"] == "processed":
                payment.status = "completed"
                payment.transaction_id = razorpay_payment_id
                payment.save()

                # Send invoice
                send_invoice(payment)

                return Response({"status": "success", "payouts": {
                    "krisshak": payout_response_krisshak["id"],
                    "platform_fee": payout_response_platform["id"]
                }}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Payout failed, payment not completed"}, status=status.HTTP_400_BAD_REQUEST)

    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# 📧 Step 6: Email Invoice to Bhooswami & Krisshak
def send_invoice(payment):
    """Send payment invoice via email"""
    subject = f"Payment Receipt - ₹{payment.amount}"
    message = f"""
Hello {payment.sender.email},

Your payment of ₹{payment.amount} to {payment.recipient.email} was successful.

Transaction ID: {payment.transaction_id}
Date: {payment.timestamp}

Thank you!
"""

    send_mail(
        subject,
        message,
        "payments@ekrisshak2.0emails.and.help@gmail.com",
        [payment.sender.email, payment.recipient.email]
    )

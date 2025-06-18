from django.urls import path
from .views import get_krisshak_price, PaymentCreateView, PaymentListView, create_razorpay_order, razorpay_webhook

urlpatterns = [
    path('price/<int:user_id>/', get_krisshak_price, name='get-krisshak-price'),
    path('create/', PaymentCreateView.as_view(), name='create-payment'),
    path('my/', PaymentListView.as_view(), name='my-payments'),

    path('razorpay/order/', create_razorpay_order, name='create-razorpay-order'),
    path('razorpay/webhook/', razorpay_webhook, name='razorpay-webhook'),
]

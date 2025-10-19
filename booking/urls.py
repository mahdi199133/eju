from django.urls import path
from .views import (
    SendOTPView,
    VerifyOTPView,
    SalonListView,
    BookingCreateView,
    UserBookingListView,
    SimulatePaymentView,
    CancelBookingView,
    UpdateBookingView
)

urlpatterns = [
    # Authentication
    path('auth/send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),

    # User facing APIs
    path('salons/', SalonListView.as_view(), name='salon-list'),
    path('bookings/create/', BookingCreateView.as_view(), name='booking-create'),
    path('bookings/', UserBookingListView.as_view(), name='user-booking-list'),
    path('bookings/<int:booking_id>/pay/', SimulatePaymentView.as_view(), name='simulate-payment'),
    path('bookings/<int:booking_id>/cancel/', CancelBookingView.as_view(), name='cancel-booking'),
    path('bookings/<int:booking_id>/update/', UpdateBookingView.as_view(), name='update-booking'),
]

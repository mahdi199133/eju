from django.urls import path
from .views import (
    SendOTPView, VerifyOTPView, SalonListView, BookingCreateView,
    UserBookingListView, SimulatePaymentView, CancelBookingView, UpdateBookingView,
    SalonAvailabilityView, UserProfileView
)

urlpatterns = [
    # Auth
    path('auth/send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),

    # Profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Salons
    path('salons/', SalonListView.as_view(), name='salon-list'),
    path('salons/<int:salon_id>/availability/', SalonAvailabilityView.as_view(), name='salon-availability'),

    # Bookings
    path('bookings/create/', BookingCreateView.as_view(), name='booking-create'),
    path('bookings/', UserBookingListView.as_view(), name='user-booking-list'),
    path('bookings/<int:booking_id>/cancel/', CancelBookingView.as_view(), name='cancel-booking'),
    path('bookings/<int:booking_id>/update/', UpdateBookingView.as_view(), name='update-booking'),
    path('bookings/<int:booking_id>/pay/', SimulatePaymentView.as_view(), name='simulate-payment'),
]

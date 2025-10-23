from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView, CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.cache import cache
from .models import CustomUser, Salon, Booking, Payment
from .serializers import SalonSerializer, BookingSerializer, BookingCreateSerializer, BookingUpdateSerializer, UserProfileSerializer
from django.utils import timezone
import uuid
from decimal import Decimal
import random
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        otp = str(random.randint(100000, 999999))
        cache.set(phone_number, otp, timeout=300)

        # In a real app, this would be sent via SMS
        print(f"Generated OTP for {phone_number}: {otp}")
        return Response({'message': 'OTP sent successfully.', 'otp': otp}, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp_entered = request.data.get('otp')
        if not phone_number or not otp_entered:
            return Response({'error': 'Phone number and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_cached = cache.get(phone_number)
        if not otp_cached or otp_entered != otp_cached:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(phone_number)
        user, created = CustomUser.objects.get_or_create(phone_number=phone_number)
        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)

class SalonListView(ListCreateAPIView):
    queryset = Salon.objects.all()
    serializer_class = SalonSerializer
    permission_classes = [permissions.IsAuthenticated]

class BookingCreateView(CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        salon = serializer.validated_data['salon']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']
        duration_hours = (end_time - start_time).total_seconds() / 3600
        total_cost = Decimal(duration_hours) * salon.price_per_hour
        serializer.save(user=self.request.user, total_cost=total_cost, status='PENDING')

class UpdateBookingView(UpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'booking_id'

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.status = 'PENDING'
        duration_hours = (instance.end_time - instance.start_time).total_seconds() / 3600
        instance.total_cost = Decimal(duration_hours) * instance.salon.price_per_hour
        instance.save()

class UserBookingListView(ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')

class SalonAvailabilityView(ListAPIView):
    serializer_class = BookingSerializer # We can reuse this serializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        salon_id = self.kwargs.get('salon_id')
        start_str = self.request.query_params.get('start')
        end_str = self.request.query_params.get('end')

        if not all([salon_id, start_str, end_str]):
            return Booking.objects.none()

        queryset = Booking.objects.filter(
            salon_id=salon_id,
            status__in=['PENDING', 'APPROVED', 'PAID'],
            start_time__lt=end_str,
            end_time__gt=start_str
        )
        return queryset

class SimulatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        if booking.status != 'APPROVED':
            return Response({"error": f"Booking not in APPROVED state."}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = 'PAID'
        booking.save()
        Payment.objects.create(
            booking=booking,
            amount=booking.total_cost,
            transaction_id=f"txn_{uuid.uuid4()}"
        )
        return Response({"message": "Payment successful!", "booking_status": "PAID"}, status=status.HTTP_200_OK)

class CancelBookingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        if booking.status not in ['PENDING', 'APPROVED']:
            return Response(
                {"error": f"Cannot cancel a booking with status '{booking.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'CANCELED'
        booking.save()

        print(f"Booking ID {booking.id} was canceled by the user.")

        return Response({"message": "Booking canceled successfully.", "booking_status": "CANCELED"}, status=status.HTTP_200_OK)

from rest_framework.generics import RetrieveUpdateAPIView

class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

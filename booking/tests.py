from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from .models import CustomUser, Salon, Booking
from datetime import timedelta
from rest_framework_simplejwt.tokens import AccessToken

class ModelTests(TestCase):

    def test_create_user(self):
        user = CustomUser.objects.create_user(phone_number='09121234567', password='testpassword')
        self.assertEqual(user.phone_number, '09121234567')

    def test_create_salon(self):
        salon = Salon.objects.create(name='Test Salon', address='123 Test St', price_per_hour=100.00)
        self.assertEqual(salon.name, 'Test Salon')

    def test_create_booking(self):
        user = CustomUser.objects.create_user(phone_number='09121234568', password='testpassword')
        salon = Salon.objects.create(name='Another Salon', address='456 Test Ave', price_per_hour=150.00)
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=2)
        booking = Booking.objects.create(
            user=user,
            salon=salon,
            start_time=start_time,
            end_time=end_time,
            total_cost=300.00
        )
        self.assertEqual(booking.salon.name, 'Another Salon')
        self.assertEqual(booking.total_cost, 300.00)

class APITests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(phone_number='09129876543', password='apipassword')
        self.salon = Salon.objects.create(name='API Test Salon', address='789 API Blvd', price_per_hour=200.00)

        # Authenticate the client with a JWT token
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_salon_list_api(self):
        url = reverse('salon-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'API Test Salon')

    def test_booking_create_api(self):
        url = reverse('booking-create')
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=3)
        data = {
            'salon': self.salon.id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertAlmostEqual(Booking.objects.get().total_cost, 600.00, places=2)

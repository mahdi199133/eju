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
            total_cost=300.00,
            status='PENDING'
        )
        self.assertEqual(booking.status, 'PENDING')

class APITests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(phone_number='09129876543', password='apipassword')
        self.salon = Salon.objects.create(name='API Test Salon', address='789 API Blvd', price_per_hour=200.00)

        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        self.start_time = timezone.now() + timedelta(days=1)
        self.end_time = self.start_time + timedelta(hours=2)
        self.booking = Booking.objects.create(
            user=self.user,
            salon=self.salon,
            start_time=self.start_time,
            end_time=self.end_time,
            total_cost=400.00,
            status='APPROVED'
        )

    def test_cancel_booking_api(self):
        url = reverse('cancel-booking', kwargs={'booking_id': self.booking.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'CANCELED')

    def test_update_booking_api(self):
        url = reverse('update-booking', kwargs={'booking_id': self.booking.id})
        new_start_time = self.start_time + timedelta(hours=1)
        new_end_time = self.end_time + timedelta(hours=1)
        data = {
            'start_time': new_start_time.isoformat(),
            'end_time': new_end_time.isoformat()
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'PENDING')
        self.assertEqual(self.booking.start_time, new_start_time)

    def test_list_and_create_api(self):
        # A quick check on existing create/list APIs to ensure no regression
        url = reverse('booking-create')
        data = {
            'salon': self.salon.id,
            'start_time': (self.start_time + timedelta(days=2)).isoformat(),
            'end_time': (self.end_time + timedelta(days=2)).isoformat()
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.count(), 2)

        list_url = reverse('user-booking-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from .models import CustomUser, Salon, Booking
from datetime import timedelta
from rest_framework_simplejwt.tokens import AccessToken
import urllib.parse

class ValidationTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(phone_number='09121111111', password='password')
        self.salon = Salon.objects.create(name='Validation Salon', price_per_hour=100)
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        start = timezone.now() + timedelta(days=1)
        Booking.objects.create(user=self.user, salon=self.salon, status='APPROVED', start_time=start, end_time=start + timedelta(hours=2), total_cost=200)

    def test_prevent_overlapping_booking(self):
        url = reverse('booking-create')
        start_time = timezone.now() + timedelta(days=1, hours=1)
        data = {'salon': self.salon.id, 'start_time': start_time.isoformat(), 'end_time': (start_time + timedelta(hours=1)).isoformat()}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class APITests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(phone_number='09129876543', full_name='Initial Name', password='apipassword')
        self.salon = Salon.objects.create(name='API Test Salon', price_per_hour=200)
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.start_time = timezone.now() + timedelta(days=2)
        self.booking = Booking.objects.create(user=self.user, salon=self.salon, status='APPROVED', start_time=self.start_time, end_time=self.start_time + timedelta(hours=2), total_cost=400)

    def test_profile_get_and_update(self):
        url = reverse('user-profile')
        # Get profile
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Initial Name')
        # Update profile
        response = self.client.patch(url, {'full_name': 'Updated Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Updated Name')
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Updated Name')

    def test_availability_api(self):
        url = reverse('salon-availability', kwargs={'salon_id': self.salon.id})
        params = urllib.parse.urlencode({'start': self.start_time.isoformat(), 'end': (self.start_time + timedelta(days=1)).isoformat()})
        response = self.client.get(f"{url}?{params}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_cancel_booking_api(self):
        url = reverse('cancel-booking', kwargs={'booking_id': self.booking.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'CANCELED')

    def test_update_booking_api(self):
        url = reverse('update-booking', kwargs={'booking_id': self.booking.id})
        new_start = self.start_time + timedelta(days=1)
        data = {'start_time': new_start.isoformat(), 'end_time': (new_start + timedelta(hours=2)).isoformat()}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'PENDING')

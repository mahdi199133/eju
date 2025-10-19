from rest_framework import serializers
from .models import Salon, Booking, CustomUser

class SalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salon
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'full_name']

class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    salon = SalonSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'

class BookingCreateSerializer(serializers.ModelSerializer):
    salon = serializers.PrimaryKeyRelatedField(queryset=Salon.objects.all())

    class Meta:
        model = Booking
        fields = ['salon', 'start_time', 'end_time']

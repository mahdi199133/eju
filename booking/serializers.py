from rest_framework import serializers
from django.db.models import Q
from .models import Salon, Booking, CustomUser, SalonImage

class SalonImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalonImage
        fields = ['image', 'is_cover']

class SalonSerializer(serializers.ModelSerializer):
    images = SalonImageSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Salon
        fields = ['id', 'name', 'address', 'price_per_hour', 'images', 'cover_image']

    def get_cover_image(self, obj):
        cover = obj.images.filter(is_cover=True).first()
        if cover:
            return self.context['request'].build_absolute_uri(cover.image.url)
        # Return the first image if no cover is set
        first_image = obj.images.first()
        if first_image:
            return self.context['request'].build_absolute_uri(first_image.image.url)
        return None


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

    def validate(self, data):
        start_time = data['start_time']
        end_time = data['end_time']
        salon = data['salon']

        if start_time >= end_time:
            raise serializers.ValidationError("زمان پایان باید بعد از زمان شروع باشد.")

        overlapping_bookings = Booking.objects.filter(
            salon=salon,
            status__in=['PENDING', 'APPROVED', 'PAID'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if overlapping_bookings:
            raise serializers.ValidationError("این بازه زمانی برای سالن مورد نظر قبلاً رزرو شده است.")

        return data

class BookingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['start_time', 'end_time']

    def validate(self, data):
        start_time = data.get('start_time', self.instance.start_time)
        end_time = data.get('end_time', self.instance.end_time)
        salon = self.instance.salon

        if start_time >= end_time:
            raise serializers.ValidationError("زمان پایان باید بعد از زمان شروع باشد.")

        overlapping_bookings = Booking.objects.filter(
            salon=salon,
            status__in=['PENDING', 'APPROVED', 'PAID'],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(pk=self.instance.pk).exists()

        if overlapping_bookings:
            raise serializers.ValidationError("این بازه زمانی برای سالن مورد نظر قبلاً رزرو شده است.")

        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['phone_number', 'full_name']
        read_only_fields = ['phone_number']

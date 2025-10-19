from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError(_('The Phone Number must be set'))
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(_('phone number'), max_length=15, unique=True)
    full_name = models.CharField(_('full name'), max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number

class Salon(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام سالن")
    address = models.TextField(verbose_name="آدرس")
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="هزینه هر ساعت")

    def __str__(self):
        return self.name

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار تایید'),
        ('APPROVED', 'تایید شده'),
        ('REJECTED', 'رد شده'),
        ('PAID', 'پرداخت شده'),
        ('CANCELED', 'لغو شده'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="کاربر")
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, verbose_name="سالن")
    start_time = models.DateTimeField(verbose_name="زمان شروع")
    end_time = models.DateTimeField(verbose_name="زمان پایان")
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="هزینه کل")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"رزرو {self.user} برای {self.salon}"

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, verbose_name="رزرو")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="مبلغ")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ پرداخت")
    transaction_id = models.CharField(max_length=100, unique=True, verbose_name="شماره تراکنش")

    def __str__(self):
        return f"پرداخت برای {self.booking}"

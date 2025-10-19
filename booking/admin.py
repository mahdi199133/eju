from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum
from .models import CustomUser, Salon, Booking, Payment
from .sms_service import get_sms_service

class BookingAdminSite(admin.AdminSite):
    site_header = "مدیریت سامانه رزرو سالن"
    site_title = "پنل مدیریت"
    index_title = "به پنل مدیریت خوش آمدید"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('booking-report/', self.admin_view(self.report_view), name='booking-report'),
        ]
        return custom_urls + urls

    def report_view(self, request):
        total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        booking_stats = Booking.objects.values('status').annotate(count=Count('status'))

        context = dict(
           self.each_context(request),
           total_revenue=total_revenue,
           booking_stats=booking_stats,
        )
        return render(request, "admin/booking_report.html", context)

booking_admin_site = BookingAdminSite(name='booking_admin')

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'full_name', 'is_staff', 'date_joined')
    search_fields = ('phone_number', 'full_name')
    list_filter = ('is_staff', 'is_active')

class SalonAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'price_per_hour')
    search_fields = ('name',)

class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'salon', 'start_time', 'end_time', 'status', 'total_cost', 'contract_details')
    list_filter = ('status', 'salon')
    search_fields = ('user__phone_number', 'salon__name')
    raw_id_fields = ('user', 'salon')
    actions = ['approve_bookings', 'reject_bookings']

    fields = ('user', 'salon', 'status', 'start_time', 'end_time', 'total_cost', 'contract_details')

    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return ('user', 'salon')
        return ()

    def approve_bookings(self, request, queryset):
        sms_service = get_sms_service()
        updated_count = queryset.update(status='APPROVED')
        for booking in queryset:
            message = f"رزرو شما برای سالن {booking.salon.name} در تاریخ {booking.start_time.strftime('%Y-%m-%d %H:%M')} تایید شد. لطفا جهت پرداخت اقدام نمایید."
            sms_service.send(booking.user.phone_number, message)
        self.message_user(request, f"{updated_count} رزرو با موفقیت تایید شد.", messages.SUCCESS)
    approve_bookings.short_description = "تایید رزروهای انتخاب شده"

    def reject_bookings(self, request, queryset):
        sms_service = get_sms_service()
        updated_count = queryset.update(status='REJECTED')
        for booking in queryset:
            message = f"متاسفانه رزرو شما برای سالن {booking.salon.name} در تاریخ {booking.start_time.strftime('%Y-%m-%d %H:%M')} رد شد."
            sms_service.send(booking.user.phone_number, message)
        self.message_user(request, f"{updated_count} رزرو با موفقیت رد شد.", messages.WARNING)
    reject_bookings.short_description = "رد رزروهای انتخاب شده"

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_date', 'transaction_id')
    search_fields = ('booking__user__phone_number', 'transaction_id')

booking_admin_site.register(CustomUser, CustomUserAdmin)
booking_admin_site.register(Salon, SalonAdmin)
booking_admin_site.register(Booking, BookingAdmin)
booking_admin_site.register(Payment, PaymentAdmin)

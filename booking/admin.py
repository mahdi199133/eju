from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import CustomUser, Salon, Booking, Payment, SalonImage
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
        queryset = Booking.objects.select_related('user', 'salon').all().order_by('-start_time')

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        salon_id = request.GET.get('salon')
        status = request.GET.get('status')

        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__date__lte=end_date)
        if salon_id:
            queryset = queryset.filter(salon_id=salon_id)
        if status:
            queryset = queryset.filter(status=status)

        total_revenue = queryset.aggregate(total=Sum('total_cost'))['total'] or 0

        context = {
            'bookings': queryset,
            'total_revenue': total_revenue,
            'salons': Salon.objects.all(),
            'status_choices': Booking.STATUS_CHOICES,
            **self.each_context(request),
        }

        # Check if a PDF export is requested
        if 'export' in request.GET and request.GET['export'] == 'pdf':
            template = get_template('admin/report_pdf_template.html')
            html = template.render(context)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="booking_report.pdf"'

            pisa_status = pisa.CreatePDF(html.encode("UTF-8"), dest=response, encoding='UTF-8')

            if pisa_status.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>')
            return response

        return render(request, "admin/booking_report.html", context)

booking_admin_site = BookingAdminSite(name='booking_admin')

class SalonImageInline(admin.TabularInline):
    model = SalonImage
    extra = 1
    fields = ('image', 'is_cover')

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'full_name', 'is_staff', 'date_joined')
    search_fields = ('phone_number', 'full_name')
    list_filter = ('is_staff', 'is_active')

class SalonAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'price_per_hour')
    search_fields = ('name',)
    inlines = [SalonImageInline]

class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'salon', 'start_time', 'end_time', 'status', 'total_cost', 'contract_details')
    list_filter = ('status', 'salon')
    search_fields = ('user__phone_number', 'salon__name')
    raw_id_fields = ('user', 'salon')
    actions = ['approve_bookings', 'reject_bookings']
    # Make total_cost readonly as it will be calculated automatically
    fields = ('user', 'salon', 'status', 'start_time', 'end_time', 'total_cost', 'contract_details')
    readonly_fields = ('total_cost',)

    def save_model(self, request, obj, form, change):
        if obj.start_time and obj.end_time and obj.salon:
            duration = (obj.end_time - obj.start_time).total_seconds() / 3600
            obj.total_cost = duration * obj.salon.price_per_hour
        super().save_model(request, obj, form, change)

    def approve_bookings(self, request, queryset):
        sms_service = get_sms_service()
        updated_count = queryset.update(status='APPROVED')
        for booking in queryset:
            message = f"رزرو شما برای سالن {booking.salon.name} تایید شد."
            sms_service.send(booking.user.phone_number, message)
        self.message_user(request, f"{updated_count} رزرو تایید شد.", messages.SUCCESS)
    approve_bookings.short_description = "تایید رزروهای انتخاب شده"

    def reject_bookings(self, request, queryset):
        sms_service = get_sms_service()
        updated_count = queryset.update(status='REJECTED')
        for booking in queryset:
            message = f"رزرو شما برای سالن {booking.salon.name} رد شد."
            sms_service.send(booking.user.phone_number, message)
        self.message_user(request, f"{updated_count} رزرو رد شد.", messages.WARNING)
    reject_bookings.short_description = "رد رزروهای انتخاب شده"

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_date', 'transaction_id')
    search_fields = ('booking__user__phone_number', 'transaction_id')

booking_admin_site.register(CustomUser, CustomUserAdmin)
booking_admin_site.register(Salon, SalonAdmin)
booking_admin_site.register(Booking, BookingAdmin)
booking_admin_site.register(Payment, PaymentAdmin)

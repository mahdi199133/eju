from django.urls import path, include
from booking.admin import booking_admin_site

urlpatterns = [
    path("admin/", booking_admin_site.urls),
    path("api/", include("booking.urls")),
]

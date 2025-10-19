from django.urls import path, include
from django.views.generic import TemplateView
from booking.admin import booking_admin_site

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html")),
    path("verify.html", TemplateView.as_view(template_name="verify.html")),
    path("app.html", TemplateView.as_view(template_name="app.html")),
    path("admin/", booking_admin_site.urls),
    path("api/", include("booking.urls")),
]

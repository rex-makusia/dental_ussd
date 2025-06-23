from django.urls import path

from .views import DentalAppUssdGateway

urlpatterns = [
    path("dental_ussd_gw/", DentalAppUssdGateway.as_view(), name="dental_ussd_gw"),
]
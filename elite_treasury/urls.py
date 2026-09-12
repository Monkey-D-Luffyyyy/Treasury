from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # <-- DAGDAG MO 'TO: I-redirect ang root URL sa core app
]
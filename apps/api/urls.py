# hello/urls.py
from django.urls import path

from apps.api.views import test_view, InitViewSet

urlpatterns = [
    path("", test_view, name='home'),
    path('test2/', InitViewSet.as_view())
]

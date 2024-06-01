from django.urls import path
from .views import *

urlpatterns = [
    path('', coffee_logs_view, name='coffee_logs'),
]

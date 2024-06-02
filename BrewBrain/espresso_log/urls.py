from django.urls import path
from .views import *

urlpatterns = [
    path('', coffee_logs_view, name='coffee_logs'),
    path('ml_predict/', ml_predict, name='ml_predict'),
    path('train_model/', train_model, name='train_model'),
    path('predict/', predict, name='predict'),
]

from django.urls import path
from .views import positions_list

urlpatterns = [
    path('positions/', positions_list, name='positions_list'),
]
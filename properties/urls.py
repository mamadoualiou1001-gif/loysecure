from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('declare/', views.declare_rooms, name='declare_rooms'),
]
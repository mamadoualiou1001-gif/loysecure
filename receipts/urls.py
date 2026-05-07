from django.urls import path
from . import views

app_name = 'receipts'

urlpatterns = [
    path('', views.receipt_list, name='list'),
    path('create/<int:tenant_id>/', views.receipt_create, name='create'),
    path('download/<uuid:pk>/', views.receipt_download, name='download'),
]
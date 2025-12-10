from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.enquiry_list, name='enquiry_list'),
    path('delete/<int:pk>/', views.enquiry_delete, name='enquiry_delete'),
    path('delete/', views.enquiry_delete, name='enquiry_delete'),
]

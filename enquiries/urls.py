from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.enquiry_list, name='enquiry_list'),
    path('delete/<int:pk>/', views.enquiry_delete, name='enquiry_delete'),
    path('delete/', views.enquiry_delete, name='enquiry_delete'),
    path('', views.index, name='index'),

    path('team/member1/', views.member1, name='member1'),
    path('team/member2/', views.member2, name='member2'),
    path('team/member3/', views.member3, name='member3'),
    path('team/member4/', views.member4, name='member4'),
    
]

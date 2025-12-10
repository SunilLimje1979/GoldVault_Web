from django.contrib import admin
from django.urls import path, include
from enquiries import views as enq_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', enq_views.index, name='index'),
    path('admin-login/', enq_views.admin_login, name='admin_login'),
    path('admin-logout/', enq_views.admin_logout, name='admin_logout'),
    path('enquiries/', include('enquiries.urls')),
]

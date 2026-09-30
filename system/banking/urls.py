"""
URL configuration for banking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('create-account/', views.create_account_view, name='create-account'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('check-balance/', views.check_balance_view, name='check-balance'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdrawal/', views.withdrawal_view, name='withdrawal'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('transaction-history/', views.transaction_history_view, name='transaction-history'),
    path('change-pin/', views.change_pin_view, name='change-pin'),
    path('logout/', views.logout_view, name='logout'),
]

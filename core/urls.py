from django.urls import path
from . import views

urlpatterns = [
    # Public Pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('initiatives/', views.initiatives_list, name='initiatives_list'),
    path('initiatives/<slug:slug>/', views.initiative_detail, name='initiative_detail'),
    path('events/', views.events_list, name='events_list'),
    path('events/<slug:slug>/', views.event_detail, name='event_detail'),
    path('trustees/', views.trustees_list, name='trustees_list'),
    path('transparency/maintenance-costs/', views.maintenance_costs, name='maintenance_costs'),
    path('donate/', views.donate, name='donate'),
    
    # RazorPay Integration
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('receipt/<str:receipt_number>/', views.receipt_detail, name='receipt_detail'),

    # WhatsApp Automation Actions
    path('whatsapp/reminder/<int:donation_id>/', views.send_whatsapp_reminder, name='send_whatsapp_reminder'),
    path('whatsapp/broadcast-event/<int:event_id>/', views.broadcast_event_whatsapp, name='broadcast_event_whatsapp'),
    path('whatsapp/logs/', views.whatsapp_logs, name='whatsapp_logs'),

    # Content & Expense Management (Trustee / Staff Portal)
    path('manage/initiative/new/', views.manage_initiative, name='initiative_create'),
    path('manage/initiative/<int:pk>/edit/', views.manage_initiative, name='initiative_edit'),
    path('manage/event/new/', views.manage_event, name='event_create'),
    path('manage/event/<int:pk>/edit/', views.manage_event, name='event_edit'),
    path('manage/expense/new/', views.manage_expense, name='expense_create'),
    path('manage/expense/<int:pk>/edit/', views.manage_expense, name='expense_edit'),
    path('manage/trustee/new/', views.manage_trustee, name='trustee_create'),
    path('manage/trustee/<int:pk>/edit/', views.manage_trustee, name='trustee_edit'),
]

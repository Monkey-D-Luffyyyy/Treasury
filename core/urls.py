from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('members/', views.member_list, name='member_list'),
    path('members/add/', views.member_create, name='member_create'),
    path('members/<int:pk>/edit/', views.member_update, name='member_update'), # <int:pk> means the member's ID
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),
    path('',views.dashboard, name='dashboard'),
    path('treasury/', views.treasury_ledger, name='treasury_ledger'),
    path('treasury/contribution/add/', views.contribution_create, name='contribution_create'),
    path('treasury/expense/add/', views.expense_create, name='expense_create'),
    path('collection/', views.fund_collection, name='fund_collection'),
    path('collection/pay/<int:member_id>/', views.quick_pay, name='quick_pay'),
    path('collection/new-fund/', views.fund_period_create, name='fund_period_create'),
    path('notes/', views.notes_list, name='notes_list'),
    path('notes/add/', views.note_create, name='note_create'),
    path('notes/<int:pk>/toggle/', views.note_toggle_complete, name='note_toggle_complete'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),
]
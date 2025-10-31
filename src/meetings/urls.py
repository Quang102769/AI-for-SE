"""
URL Configuration for meetings app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # Email Verification
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    # Home & Dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Leader Workflow - Create Request (3-step wizard)
    path('create/step1/', views.create_request_step1, name='create_request_step1'),
    path('create/step2/', views.create_request_step2, name='create_request_step2'),
    path('create/step3/', views.create_request_step3, name='create_request_step3'),
    path('create/success/<uuid:request_id>/', views.request_created, name='request_created'),
    
    # AI-Powered Meeting Creation
    path('api/generate-meeting-ai/', views.generate_meeting_with_ai, name='generate_meeting_with_ai'),
    
    # Leader Workflow - View & Manage
    path('request/<uuid:request_id>/', views.view_request, name='view_request'),
    path('request/<uuid:request_id>/edit/', views.edit_request, name='edit_request'),
    path('request/<uuid:request_id>/lock/<uuid:slot_id>/', views.lock_slot, name='lock_slot'),
    path('request/<uuid:request_id>/delete/', views.delete_request, name='delete_request'),
    path('request/<uuid:request_id>/send-invitations/', views.send_meeting_invitations, name='send_meeting_invitations'),
    
    # Member Workflow - Respond
    path('r/<uuid:request_id>/', views.respond_to_request, name='respond_to_request'),
    path('r/<uuid:request_id>/select/', views.select_busy_times, name='select_busy_times'),
    path('r/<uuid:request_id>/save/', views.save_busy_slots, name='save_busy_slots'),
    path('r/<uuid:request_id>/complete/', views.response_complete, name='response_complete'),
    
    # API Endpoints
    path('api/request/<uuid:request_id>/heatmap/', views.api_get_heatmap, name='api_get_heatmap'),
    path('api/request/<uuid:request_id>/suggestions/', views.api_get_suggestions, name='api_get_suggestions'),
]

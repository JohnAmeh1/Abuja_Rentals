from django.urls import path, include
from . import views
from . import payment_views
import os
from django.views.generic import TemplateView
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Properties routes (public and owner) - Regular Properties
    path('properties/', views.owner_properties_view, name='properties'),
    path('owner/properties/', views.owner_properties_view, name='owner_properties'),
    path('owner/properties/add/', views.add_property_view, name='add_property'),
    path('owner/properties/edit/<int:property_id>/', views.edit_property_view, name='edit_property'),
    path('owner/properties/status/<int:property_id>/', views.update_property_status, name='update_property_status'),
    path('owner/properties/delete/<int:property_id>/', views.delete_property_view, name='delete_property'),
    
    # Property detail and actions - Regular Properties
    path('property/<int:property_id>/', views.property_detail_view, name='property_detail'),
    path('property/<int:property_id>/contact-owner/', views.contact_property_owner, name='contact_property_owner'),
    path('property/<int:property_id>/update-status/', views.update_property_status, name='update_property_status'),
    
    # Property actions - Regular Properties
    path('property/<int:property_id>/save/', views.save_property, name='save_property'),
    path('property/<int:property_id>/book-visit/', views.book_property_visit, name='book_property_visit'),
    path('property/<int:property_id>/report/', views.submit_report, name='submit_report'),
    

    # Tenant views
    path('saved-properties/', views.saved_properties_view, name='saved_properties'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    
    # Owner views
    path('owner/manage-bookings/', views.manage_bookings_view, name='manage_bookings'),
    path('owner/bookings/<int:booking_id>/update/', views.update_booking_status, name='update_booking_status'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/properties/', views.admin_properties_view, name='admin_properties'),
    path('admin/transactions/', views.admin_transactions_view, name='admin_transactions'),
    path('admin/platform-fees/', views.admin_platform_fees_view, name='admin_platform_fees'),
    path('admin/settings/', views.admin_settings_view, name='admin_settings'),
    path('admin/users/update/<int:user_id>/', views.update_user_status, name='update_user_status'),
    path('admin/properties/update/<int:property_id>/', views.update_property_status_admin, name='update_property_status_admin'),
    
    path('admin/messages/', views.admin_messages_view, name='admin_messages'),
    path('admin/messages/create/', views.create_admin_message, name='create_admin_message'),
    path('admin/messages/edit/<int:message_id>/', views.edit_admin_message, name='edit_admin_message'),
    path('admin/messages/toggle/<int:message_id>/', views.toggle_admin_message, name='toggle_admin_message'),
    path('admin/messages/delete/<int:message_id>/', views.delete_admin_message, name='delete_admin_message'),
    path('admin/messages/dismiss/', views.dismiss_admin_message, name='dismiss_admin_message'),
    path('api/active-messages/', views.get_active_messages, name='get_active_messages'),
    path('admin/student-properties/review/<int:pk>/', views.review_student_property, name='review_student_property'),
    path('admin/student-properties/', views.admin_student_properties, name='admin_student_properties'),
    path('admin/approve/<int:pk>/', views.approve_student_property, name='approve_student_property'),
    path('admin/properties/update/<int:property_id>/', views.update_property_status_admin, name='update_property_status_admin'),
    path('admin/student-properties/update/<int:property_id>/', views.update_student_property_status_admin, name='update_student_property_status_admin'),


    # Reports
    path('admin/reports/', views.admin_reports_view, name='admin_reports'),
    path('admin/reports/<int:report_id>/action/', views.admin_report_action, name='admin_report_action'),
    
    path('api/check-username/', views.check_username_api, name='check_username_api'),
    
    # Student-specific URLs - Student Properties (separate from regular properties)
    path('student/properties/', views.student_properties, name='student_properties'),
    path('student/properties/create/', views.create_property, name='create_property'),
    path('student/property/<int:pk>/', views.student_property_detail, name='student_property_detail'),
    path('student/properties/<int:pk>/edit/', views.edit_student_property, name='edit_student_property'),
    path('student/properties/<int:pk>/delete/', views.delete_student_property, name='delete_student_property'),

    # API endpoints
    path('api/property/<int:property_id>/bookings/', views.property_bookings_api, name='property_bookings_api'),
    path('api/bookings/<int:booking_id>/details/', views.booking_details_api, name='booking_details_api'),
    path('api/bookings/<int:booking_id>/respond/', views.booking_respond_api, name='booking_respond_api'),
    path('api/bookings/<int:booking_id>/complete/', views.booking_complete_api, name='booking_complete_api'),
    
    # Rental actions
    
    # AJAX endpoints
    path('calculate-platform-fee/', views.calculate_platform_fee, name='calculate_platform_fee'),
    

    path("payments/initiate/<int:property_id>/", payment_views.initiate_payment, name="initiate_payment"),
    path("payments/verify/", payment_views.verify_payment, name="verify_payment"),
    path("payments/receipt/<int:payment_id>/", payment_views.payment_receipt, name="payment_receipt"),
    path("payments/property/<int:property_id>/",payment_views.process_property_payment,name="process_property_payment"),
    path("payments/flutterwave/verify/",payment_views.flutterwave_verify,name="flutterwave_verify"),
    path("payments/webhook/flutterwave/",payment_views.flutterwave_webhook,name="flutterwave_webhook"),


    # PWA URLs
    # path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),
    # path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest'),
    # path('static/pwa/<path:path>', serve, {'document_root': os.path.join(settings.STATIC_ROOT, 'pwa')}),
    
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest'),
    path('serviceworker.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='serviceworker'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

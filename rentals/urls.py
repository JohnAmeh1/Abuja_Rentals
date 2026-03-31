from django.urls import include, path
from . import views
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password/', views.forgot_password, name='change_password'),
    path('verify-forgot-password-otp/', views.verify_forgot_password_otp, name='verify_forgot_password_otp'),
    path('resend-forgot-password-otp/<int:user_id>/', views.resend_forgot_password_otp, name='resend_forgot_password_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('redirect/', views.send_message, name='redirect'),
    
    path('agent/properties/', views.agent_properties_view, name='agent_properties'),
    path('api/welcome-seen/', views.mark_welcome_seen, name='mark_welcome_seen'),
    path('api/profile-shared/', views.mark_profile_shared, name='mark_profile_shared'),
    path('agent/profile/', views.agent_profile_edit, name='agent_profile_edit'),
    path('agent/request_verification/', views.request_agent_verification, name='request_agent_verification'),
    path('agents/<int:agent_id>/', views.agent_public_profile, name='agent_public_profile'),
    
    path('properties/', views.properties_view, name='properties'),
    path('api/properties/', views.get_properties, name='properties_api'),
    path('properties/add/', views.add_property_view, name='add_property'),
    path('properties/edit/<int:property_id>/', views.edit_property_view, name='edit_property'),
    path('properties/status/<int:property_id>/', views.update_property_status, name='update_property_status'),
    path('properties/delete/<int:property_id>/', views.delete_property_view, name='delete_property'),
    
    path('property/<int:property_id>/', views.property_detail_view, name='property_detail'),
    path('property/<int:property_id>/update-status/', views.update_property_status, name='update_property_status'),
    
    path('property/<int:property_id>/save/', views.save_property, name='save_property'),
    path('property/<int:property_id>/book-visit/', views.book_property_visit, name='book_property_visit'),
    path('property/<int:property_id>/report/', views.submit_report, name='submit_report'),
    

    path('saved-properties/', views.saved_properties_view, name='saved_properties'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('property-request/', views.property_request, name='property_request'),
    
    path('manage-bookings/', views.manage_bookings_view, name='manage_bookings'),
    path('bookings/<int:booking_id>/update/', views.update_booking_status, name='update_booking_status'),
    
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/applications/<int:application_id>/review/', views.review_agent_application, name='review_agent_application'),
    path('admin/properties/', views.admin_properties_view, name='admin_properties'),
    path('admin/settings/', views.admin_settings_view, name='admin_settings'),
    path('admin/users/update/<int:user_id>/', views.update_user_status, name='update_user_status'),
    path('admin/properties/update/<int:property_id>/', views.update_property_status_admin, name='update_property_status_admin'),
    
    path('admin/messages/', views.admin_messages_view, name='admin_messages'),
    path('admin/messages/create', views.create_admin_message, name='create_admin_message'),
    path('admin/messages/edit/<int:message_id>/', views.edit_admin_message, name='edit_admin_message'),
    path('admin/messages/toggle/<int:message_id>/', views.toggle_admin_message, name='toggle_admin_message'),
    path('admin/messages/delete/<int:message_id>/', views.delete_admin_message, name='delete_admin_message'),
    path('admin/messages/dismiss/', views.dismiss_admin_message, name='dismiss_admin_message'),
    path('api/active-messages/', views.get_active_messages, name='get_active_messages'),
    path('admin/properties/update/<int:property_id>/', views.update_property_status_admin, name='update_property_status_admin'),

    path('admin/reports/', views.admin_reports_view, name='admin_reports'),
    path('admin/reports/<int:report_id>/action/', views.admin_report_action, name='admin_report_action'),
    
    path('api/check-username/', views.check_username_api, name='check_username_api'),
    path('api/get-details/', views.get_details, name='get_details'),

    path('api/property/<int:property_id>/bookings/', views.property_bookings_api, name='property_bookings_api'),

    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest'),
    path('serviceworker.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='serviceworker'),

    path('dashboard/apply/', views.agent_apply, name='agent_apply'),
    path('dashboard/apply/withdraw/', views.agent_application_withdraw, name='agent_application_withdraw'),
    path('dashboard/requests/', views.dashboard_requests, name='dashboard_requests'),
    path('dashboard/requests/<int:inquiry_id>/close/', views.close_inquiry, name='close_inquiry'),
    path('api/inquiries/<int:inquiry_id>/mark-opened/', views.mark_responses_opened, name='mark_responses_opened'),

    path('dashboard/requests/agent/', views.agent_inquiries, name='agent_inquiries'),
    path('dashboard/agent/preferences/', views.agent_update_preferences, name='agent_update_preferences'),

    path('api/inquiries/<int:inquiry_id>/respond/', views.agent_respond_inquiry, name='agent_respond_inquiry'),
    path('api/inquiries/<int:response_id>/', views.mark_response_opened, name='mark_response_opened'),
    path('api/areas/', views.areas_by_city_api, name='areas_by_city'),
    path('api/properties/compare/', views.compare_properties_api, name='compare_properties_api'),
    
    path('about/',   views.AboutView.as_view(),   name='about'),
    path('careers/', views.CareersView.as_view(), name='careers'),
    path('faq/',     views.FAQView.as_view(),     name='faq'),
    path('terms/',   views.TermsView.as_view(),   name='terms'),
    
    path('universities/', views.SchoolsView.as_view(), name='schools'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

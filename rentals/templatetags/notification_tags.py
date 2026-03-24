from django import template
from django.urls import reverse
from django.utils.html import format_html

register = template.Library()

@register.filter
def get_notification_url(notification):
    """Get URL for notification"""
    if notification.related_object_type == 'propertyvisit' and notification.related_object_id:
        if notification.notification_type == 'booking_request':
            return reverse('manage_bookings')
        elif notification.notification_type in ['booking_confirmed', 'booking_declined', 'booking_cancelled']:
            return reverse('my_bookings')
    return reverse('notifications')

@register.filter
def is_read(queryset, value):
    """Filter notifications by read status"""
    return queryset.filter(is_read=value)


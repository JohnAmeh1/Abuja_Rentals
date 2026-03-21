PURPOSE_CHOICES = [
    ('rent', 'For Rent'),
    ('sale', 'For Sale'),
]

PROPERTY_STATUS_CHOICES = [
    ('available', 'Available'),
    ('pending', 'Pending'),
    ('draft', 'Draft'),
]

AGENT_PROPERTY_STATUS_CHOICES = [
    ('available', 'Available'),
    ('draft', 'Draft'),
]

USER_TYPE_CHOICES = [
    ('tenant', 'Tenant/Looking to Rent'),
    ('agent', 'Real Estate Agent'),
    ('admin', 'Administrator'),
]

REASON_CHOICES = [
    ('fake_listing', 'Fake / Misleading Listing'),
    ('harassment', 'Harassment / Abusive Behavior'),
    ('other', 'Other'),
]

REPORT_STATUS_CHOICES = [
    ('open', 'Open'),
    ('investigating', 'Investigating'),
    ('resolved', 'Resolved'),
    ('dismissed', 'Dismissed'),
]

VISIT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
    ('declined', 'Declined'),
]

MESSAGE_TYPE_CHOICES = [
    ('info', 'Information'),
    ('warning', 'Warning'),
    ('success', 'Success'),
    ('alert', 'Alert'),
    ('maintenance', 'Maintenance'),
]

AGENT_APP_STATUS_CHOICES = [
    ('pending',  'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

NOTIFICATION_MESSAGE_TYPE_CHOICES = [
    ("inquiry_sent", "Inquiry Sent"),
    ("inquiry_responded", "Inquiry Responded"),
    ("inquiries", "Inquiries"),
    ("agent_application_sent", "Agent Application Sent"),
    ("agent_application_reviewed", "Agent Application Reviewed"),
    ("agent_applications", "Agent Applications"),
    ("agent_verification_request", "Agent Verification Request"),
    ("agent_verification_requests", "Agent Verification Requests"),
]

NOTIFICATION_MODE_CHOICES = [
    ("email", "Email"),
    ("whatsapp", "Whatsapp"),
    ("phone", "Phone"),
]
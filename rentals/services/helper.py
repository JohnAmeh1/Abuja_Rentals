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
    ("new_inquiry",           "New Inquiry"),
    ("inquiry_response",      "Inquiry Responded"),
    ("property_approved",     "Property Approved"),
    ("property_rejected",     "Property Rejected"),
    ("application_reviewed",  "Agent Reviewed"),
    ("application_request",   "Agent Request"),
    ("agent_verified",        "Agent Verified"),
    ("new_visit_request",     "New Visit Request"),
    ("visit_confirmed",       "Visit Confirmed"),
    ("verification_request",  "Verification Request"),

    ("email_verification",    "Email Verification"),
    ("login_otp",             "Login OTP"),
    ("forgot_password",       "Forgot Password"),

    ("welcome",               "Welcome"),
    ("password_changed",      "Password Changed"),
    ("visit_cancelled",       "Visit Cancelled"),
    ("property_expired",      "Property Expired"),
    ("inquiry_closed",        "Inquiry Closed"),
]

NOTIFICATION_MODE_CHOICES = [
    ("email", "Email"),
    ("whatsapp", "Whatsapp"),
    ("phone", "Phone"),
]
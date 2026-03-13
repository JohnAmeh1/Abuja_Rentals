PURPOSE_CHOICES = [
    ('rent', 'For Rent'),
    ('sale', 'For Sale'),
]

PROPERTY_STATUS_CHOICES = [
    ('available', 'Available'),
    ('pending', 'Pending'),
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
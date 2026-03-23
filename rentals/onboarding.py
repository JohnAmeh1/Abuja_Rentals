from django.urls import reverse


def get_agent_onboarding(user, agent):
    """
    Returns onboarding context for the agent dashboard.
    Each step is a dict with: label, hint, done, url, cta, onclick (optional).
    """
    profile = getattr(user, 'userprofile', None)


    steps = [
        {
            'key':    'profile_complete',
            'label':  'Complete your profile',
            'hint':   'Add your name, phone number and a profile photo',
            'done':   bool(
                user.first_name and
                user.last_name and
                profile and profile.phone_number
            ),
            'url':    reverse('profile'),
            'cta':    'Edit profile',
        },
        {
            'key':    'agent_name',
            'label':  'Add your agency name',
            'hint':   'You might want to be displayed as an agency',
            'done':   bool(agent.name),
            'url':    reverse('agent_profile_edit'),
            'cta':    'Edit agent profile',
        },
        {
            'key':    'agent_bio',
            'label':  'Write your agent bio and add a photo',
            'hint':   'Clients read your bio before they contact you',
            'done':   bool(agent.bio and agent.image),
            'url':    reverse('agent_profile_edit'),
            'cta':    'Edit agent profile',
        },
        {
            'key':    'add_listing',
            'label':  'Add your first property listing',
            'hint':   'Listings get you discovered by tenants searching in your area',
            'done':   agent.properties.filter(status__in=['available', 'pending']).exists(),
            'url':    reverse('add_property'),
            'cta':    'Add listing',
        },
        {
            'key':    'pick_cities',
            'label':  'Select the cities you cover',
            'hint':   'You\'ll only see client requests from your selected cities',
            'done':   agent.assigned_cities.exists(),
            'url':    f"{reverse('agent_inquiries')}?openmodal=true",
            'cta':    'Set cities',
        },
        {
            'key':    'pick_schools',
            'label':  'Pick schools you operate near',
            'hint':   'You\'ll appear on the schools page for students looking for housing',
            'done':   agent.assigned_schools.exists(),
            'url':    f"{reverse('agent_inquiries')}?openmodal=true",
            'cta':    'Set schools',
        },
        {
            'key':    'check_requests',
            'label':  'Check your first client request',
            'hint':   'Clients submit requests and agents respond with matching listings',
            'done':   (
                agent.inquires_responses.exists() if hasattr(agent, 'inquires_responses')
                else False
            ),
            'url':    reverse('agent_inquiries'),
            'cta':    'View requests',
        },
        {
            'key':      'share_profile',
            'label':    'Share your public profile link',
            'hint':     'Send it to clients so they can see all your listings in one place',
            'done':     agent.has_shared_profile,  
            'url':      reverse('agent_profile_edit'),
            'cta':      'View profile',
        },
    ]

    # ── Compute progress ─────────────────────────────────────────────────────

    complete_count = sum(1 for s in steps if s['done'])
    total          = len(steps)
    pct            = round((complete_count / total) * 100) if total else 0
    all_done       = complete_count == total

    # SVG ring: circumference of r=18 circle is 2π×18 ≈ 113
    # stroke-dashoffset = 113 × (1 - pct/100)
    dash_offset = round(113 * (1 - pct / 100))

    return {
        'onboarding_steps':          steps,
        'onboarding_complete_count': complete_count,
        'onboarding_pct':            pct,
        'onboarding_dash_offset':    dash_offset,
        'onboarding_done':           all_done,
    }

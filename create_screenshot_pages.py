"""One-off script: create 4 screenshot pages for home page image grid."""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.Settings.dev')
import sys
sys.path.insert(0, r'c:\Users\mprov\Dropbox\Projects\flexible_website')
django.setup()

from core.models import Site, Page, Section, SectionItem

site = Site.objects.first()

PAGES = [
    {
        'slug': 'launch-in-days',
        'title': 'Launch Campaign Pages in Days, Not Weeks',
        'page_type': 'services',
        'order': 10,
        'sections': [
            {
                'type': 'hero', 'layout': 'layout_2',
                'heading': 'Launch Campaign Pages in Days, Not Weeks',
                'subheading': 'Stop waiting on dev cycles. CBL gives your marketing team the tools to build, test, and ship high-converting campaign pages independently — no engineering bottlenecks, no compromises.',
                'items': [
                    {'link_text': 'Start Building Free', 'link_url': '/contact/'},
                    {'link_text': 'See How It Works', 'link_url': '/services/'},
                ],
            },
            {
                'type': 'feature_list', 'layout': 'layout_1',
                'heading': 'Everything Your Team Needs to Move Fast',
                'subheading': 'Built for marketers who cannot afford to wait.',
                'config': {'columns_desktop': 3},
                'items': [
                    {'icon': 'lightning-charge', 'title': 'Drag-and-Drop Builder', 'text': 'Assemble pages from a library of pre-built, conversion-tested sections in minutes.'},
                    {'icon': 'arrow-repeat', 'title': 'Reusable Section Library', 'text': 'Save your best layouts and reuse them across every campaign. Consistency at scale.'},
                    {'icon': 'phone', 'title': 'Mobile-First by Default', 'text': 'Every page looks perfect on any device, right out of the box. No extra QA required.'},
                    {'icon': 'bar-chart-line', 'title': 'Built-In Analytics Ready', 'text': 'Drop in your GA4 or pixel — your pages are clean, fast, and tracking-ready.'},
                    {'icon': 'people', 'title': 'Team Collaboration', 'text': 'Multiple editors, real-time previews, and approval workflows that keep everyone aligned.'},
                    {'icon': 'shield-check', 'title': 'Brand Guardrails', 'text': 'Lock down fonts, colors, and logo usage so every page looks on-brand, every time.'},
                ],
            },
            {
                'type': 'text_block', 'layout': 'layout_2',
                'heading': 'How It Works',
                'subheading': 'Pick a campaign type, customize your sections, and hit publish. Your page is live in minutes — not a sprint cycle.\n\nCBL handles hosting, performance optimization, and mobile responsiveness automatically. Your team focuses on messaging and conversion. We handle the rest.\n\nWhen the campaign ends, archive the page in one click. Reuse its best sections next quarter.',
            },
            {
                'type': 'testimonials', 'layout': 'layout_1',
                'heading': 'Teams That Moved Faster With CBL',
                'config': {'columns_desktop': 3},
                'items': [
                    {'title': 'Priya S., Head of Growth', 'text': 'We used to wait 3 weeks for a landing page. Now our team ships one in an afternoon. CBL changed how we operate.'},
                    {'title': 'Marcus T., Marketing Director', 'text': 'The reusable section library alone saved us months of design work. Every campaign feels polished without starting from scratch.'},
                    {'title': 'Leila R., Campaign Manager', 'text': 'I can build a fully branded product launch page without touching a single line of code. That was unthinkable before CBL.'},
                ],
            },
            {
                'type': 'cta_banner', 'layout': 'layout_1',
                'heading': 'Your Next Campaign Page Is 20 Minutes Away',
                'subheading': 'Join hundreds of marketing teams building and shipping faster with CBL.',
                'items': [
                    {'link_text': 'Get Started Free', 'link_url': '/contact/'},
                    {'link_text': 'Book a Demo', 'link_url': '/contact/'},
                ],
            },
        ],
    },
    {
        'slug': 'product-launch-page',
        'title': 'Product Launch Page',
        'page_type': 'services',
        'order': 11,
        'sections': [
            {
                'type': 'hero', 'layout': 'layout_2',
                'heading': 'Introducing Apex — The Smarter Project Dashboard',
                'subheading': 'Real-time insights, team-wide visibility, and zero setup. Apex turns your scattered project data into a single source of truth.',
                'items': [
                    {'link_text': 'Get Early Access', 'link_url': '/contact/'},
                    {'link_text': 'Watch the Demo', 'link_url': '/contact/'},
                ],
            },
            {
                'type': 'feature_list', 'layout': 'layout_1',
                'heading': 'Built for the Way Modern Teams Work',
                'subheading': 'Powerful enough for ops. Simple enough for everyone else.',
                'config': {'columns_desktop': 3},
                'items': [
                    {'icon': 'speedometer2', 'title': 'Live Project Dashboards', 'text': 'See every project status, blocker, and milestone update the moment it happens.'},
                    {'icon': 'diagram-3', 'title': 'Cross-Team Visibility', 'text': 'Break down silos. Every stakeholder sees exactly what they need, nothing they do not.'},
                    {'icon': 'bell', 'title': 'Smart Alerts', 'text': 'Get notified when things drift off track — before they become problems.'},
                    {'icon': 'plug', 'title': 'One-Click Integrations', 'text': 'Connect Slack, Jira, Asana, and 40+ tools in minutes. No IT ticket required.'},
                    {'icon': 'graph-up-arrow', 'title': 'Progress Analytics', 'text': 'Spot bottlenecks, forecast completion dates, and report to leadership with confidence.'},
                    {'icon': 'lock', 'title': 'Enterprise-Grade Security', 'text': 'SOC 2 Type II compliant with SSO, audit logs, and role-based permissions.'},
                ],
            },
            {
                'type': 'testimonials', 'layout': 'layout_1',
                'heading': 'Early Adopters Love It',
                'config': {'columns_desktop': 3},
                'items': [
                    {'title': 'Jordan K., VP of Engineering', 'text': 'Apex gave us visibility we never had. We caught a critical delay two weeks early and delivered on time for the first time in a year.'},
                    {'title': 'Sofia M., PMO Lead', 'text': 'I replaced four different tools with Apex. My Monday morning reports now take 10 minutes instead of two hours.'},
                    {'title': 'Dev R., COO', 'text': 'Our board now gets a live link instead of a deck. Apex made that possible.'},
                ],
            },
            {
                'type': 'cta_banner', 'layout': 'layout_1',
                'heading': 'Be First in Line — Early Access Is Limited',
                'subheading': 'Join the waitlist today and get three months free when we launch.',
                'items': [
                    {'link_text': 'Request Early Access', 'link_url': '/contact/'},
                ],
            },
        ],
    },
    {
        'slug': 'webinar-signup-funnel',
        'title': 'Webinar Signup Funnel',
        'page_type': 'services',
        'order': 12,
        'sections': [
            {
                'type': 'hero', 'layout': 'layout_2',
                'heading': 'Live Webinar: How Top Marketing Teams Ship 3x Faster',
                'subheading': 'Thursday, June 19  ·  1:00 PM ET  ·  Free to attend\n\nJoin 500+ marketers learning the exact playbook high-growth teams use to launch campaign pages in days, not sprint cycles.',
                'items': [
                    {'link_text': 'Reserve My Free Seat', 'link_url': '/contact/'},
                ],
            },
            {
                'type': 'feature_list', 'layout': 'layout_1',
                'heading': 'What You Will Walk Away With',
                'subheading': 'One hour. Actionable frameworks you can use the next day.',
                'config': {'columns_desktop': 2},
                'items': [
                    {'icon': 'map', 'title': 'The 5-Step Launch Framework', 'text': 'A repeatable process for going from campaign brief to live page in under 48 hours.'},
                    {'icon': 'scissors', 'title': 'How to Cut Approval Time in Half', 'text': 'Stakeholder alignment strategies that eliminate last-minute revision cycles.'},
                    {'icon': 'bar-chart', 'title': 'Which Metrics Actually Matter', 'text': 'Stop tracking vanity metrics. Learn the three numbers that predict campaign ROI.'},
                    {'icon': 'collection', 'title': 'The Reusable Section System', 'text': 'How to build a section library your whole team can use — and reuse — forever.'},
                ],
            },
            {
                'type': 'text_block', 'layout': 'layout_2',
                'heading': 'Meet Your Hosts',
                'subheading': 'Dana Okafor — Head of Marketing at CBL with 12 years running campaigns for SaaS, e-commerce, and B2B brands.\n\nRyan Cho — Growth Lead at Apex, who took the company from 0 to 10,000 signups in 90 days using the frameworks covered in this webinar.\n\nBoth will be live to take your questions in the final 20 minutes.',
            },
            {
                'type': 'testimonials', 'layout': 'layout_1',
                'heading': 'What Past Attendees Said',
                'config': {'columns_desktop': 3},
                'items': [
                    {'title': 'Camille D., Marketing Manager', 'text': 'Best webinar I have attended this year. Walked away with a framework I used the very next week.'},
                    {'title': 'Ahmed N., Growth Marketer', 'text': 'Dana and Ryan do not waste your time. Every minute was packed with things I could actually use.'},
                    {'title': 'Tess W., Campaign Lead', 'text': 'The Q&A alone was worth it. They answered my exact situation in real time.'},
                ],
            },
            {
                'type': 'cta_banner', 'layout': 'layout_1',
                'heading': 'Seats Are Limited — Register Now',
                'subheading': "Can't make it live? Register anyway and we will send you the full recording.",
                'items': [
                    {'link_text': 'Reserve My Free Seat', 'link_url': '/contact/'},
                ],
            },
        ],
    },
    {
        'slug': 'seasonal-campaign-hub',
        'title': 'Seasonal Campaign Hub',
        'page_type': 'services',
        'order': 13,
        'sections': [
            {
                'type': 'hero', 'layout': 'layout_2',
                'heading': 'Summer Campaign Hub — All Your Launches, One Place',
                'subheading': 'Plan, build, and track every summer promotion from a single dashboard. Coordinate your team, align your messaging, and hit every deadline.',
                'items': [
                    {'link_text': 'Browse Active Campaigns', 'link_url': '/contact/'},
                    {'link_text': 'Start a New Campaign', 'link_url': '/contact/'},
                ],
            },
            {
                'type': 'image_grid', 'layout': 'layout_1',
                'heading': 'Active Campaigns This Season',
                'subheading': 'Click any campaign to view its page, analytics, and team notes.',
                'config': {'columns_desktop': 3},
                'items': [
                    {'title': 'Summer Flash Sale', 'text': 'July 4–7  ·  40% off sitewide  ·  Status: Live'},
                    {'title': 'Back to School Drive', 'text': 'Aug 1–31  ·  Education bundles  ·  Status: Scheduled'},
                    {'title': 'Partner Co-Launch', 'text': 'July 15  ·  Apex x CBL promo  ·  Status: In Review'},
                    {'title': 'Referral Sprint', 'text': 'Ongoing  ·  Double rewards  ·  Status: Live'},
                    {'title': 'Newsletter Re-Engagement', 'text': 'July 20  ·  Win-back sequence  ·  Status: Draft'},
                    {'title': 'End of Summer Clearance', 'text': 'Aug 25–31  ·  Final markdown  ·  Status: Planned'},
                ],
            },
            {
                'type': 'feature_list', 'layout': 'layout_1',
                'heading': 'What the Campaign Hub Gives Your Team',
                'config': {'columns_desktop': 3},
                'items': [
                    {'icon': 'calendar2-check', 'title': 'Campaign Calendar', 'text': 'See every launch, deadline, and go-live date for the season at a glance.'},
                    {'icon': 'people', 'title': 'Team Assignments', 'text': 'Assign owners to every campaign so nothing falls through the cracks.'},
                    {'icon': 'bar-chart-line', 'title': 'Live Performance Roll-Up', 'text': 'Aggregate results across all active campaigns in one dashboard view.'},
                ],
            },
            {
                'type': 'cta_banner', 'layout': 'layout_1',
                'heading': 'Ready to Plan Your Next Season?',
                'subheading': 'Set up your campaign hub in minutes and get your whole team aligned before the season starts.',
                'items': [
                    {'link_text': 'Build Your Campaign Hub', 'link_url': '/contact/'},
                    {'link_text': 'Talk to the Team', 'link_url': '/contact/'},
                ],
            },
        ],
    },
]


def create_page(pdef):
    page, created = Page.objects.get_or_create(
        site=site, slug=pdef['slug'],
        defaults={
            'title': pdef['title'],
            'page_type': pdef['page_type'],
            'order': pdef['order'],
            'is_enabled': True,
        },
    )
    if not created:
        page.title = pdef['title']
        page.save(update_fields=['title'])
        Section.all_objects.filter(page=page).delete()

    for order, sdef in enumerate(pdef['sections']):
        s = Section.objects.create(
            page=page,
            section_type=sdef['type'],
            layout=sdef.get('layout', 'layout_1'),
            order=order,
            is_visible=True,
            heading=sdef.get('heading', ''),
            subheading=sdef.get('subheading', ''),
            config=sdef.get('config', {}),
        )
        for i, idef in enumerate(sdef.get('items', [])):
            SectionItem.objects.create(
                section=s, order=i,
                title=idef.get('title', ''),
                text=idef.get('text', ''),
                icon=idef.get('icon', ''),
                link_url=idef.get('link_url', ''),
                link_text=idef.get('link_text', ''),
            )
    action = 'Created' if created else 'Rebuilt'
    print(f'  {action}: /{page.slug}/')


for pdef in PAGES:
    create_page(pdef)

print('Done.')

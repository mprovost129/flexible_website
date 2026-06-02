"""
Industry packs: declarative starter content bundles for specific business types.

A pack is pure data describing a ready-to-launch site:
  - site-level identity defaults (name placeholder, tagline, theme key, navbar preset/footer)
  - a list of pages, each with an ordered list of sections
  - each section's type, layout, headings, config, and items

The applier (core/packs/applier.py) turns this data into real Site/Page/
Section/SectionItem rows. Authoring a new pack means adding a dict here; no
new code. This is the feature that turns "a Django template" into
"CBL for <industry>".

Pack schema (per section):
    {
        'type': 'hero',                # Section.section_type
        'layout': 'layout_2',          # optional, defaults to 'layout_1'
        'heading': '...',
        'subheading': '...',
        'background_color': '#fff',    # optional
        'config': {'columns_desktop': 3},  # optional
        'items': [                     # optional, list of SectionItem dicts
            {'title': '...', 'text': '...', 'icon': '...',
             'link_text': '...', 'link_url': '...'},
        ],
    }
"""

CONTRACTOR_PACK = {
    'key': 'contractor',
    'name': 'Contractor / Home Services',
    'description': 'For builders, remodelers, plumbers, electricians, and trades.',
    'theme_key': 'slate',        # Corporate Slate reads as trustworthy/solid
    'navbar': 'app',             # Universal navbar preset; all presets use same engine
    'footer': 'footer_4',        # Multi-column with sections
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Quality work, done right, on time.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_2',
                    'heading': 'Reliable Contracting You Can Count On',
                    'subheading': 'Licensed, insured, and trusted by homeowners across the region. Get a free estimate today.',
                    'items': [
                        {'link_text': 'Get a Free Quote', 'link_url': '/contact/'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Why Choose Us',
                    'subheading': 'Decades of combined experience on every job.',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'patch-check', 'title': 'Licensed & Insured', 'text': 'Fully certified and covered for your peace of mind.'},
                        {'icon': 'clock-history', 'title': 'On-Time, On-Budget', 'text': 'We respect your schedule and your wallet.'},
                        {'icon': 'hand-thumbs-up', 'title': 'Satisfaction Guaranteed', 'text': 'We are not done until you are happy with the work.'},
                    ],
                },
                {
                    'type': 'image_grid',
                    'layout': 'layout_1',
                    'heading': 'Recent Projects',
                    'subheading': 'A look at some of our completed work.',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Kitchen Remodel', 'text': 'Full renovation, modern finishes.'},
                        {'title': 'Bathroom Upgrade', 'text': 'Tile, fixtures, and lighting.'},
                        {'title': 'Deck Build', 'text': 'Custom outdoor living space.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Ready to Start Your Project?',
                    'subheading': 'Call today or request a quote online. Free estimates, no obligation.',
                    'items': [
                        {'link_text': 'Request a Quote', 'link_url': '/contact/'},
                        {'link_text': 'Call Now', 'link_url': 'tel:5550000000'},
                    ],
                },
            ],
        },
        {
            'page_type': 'services',
            'slug': 'services',
            'title': 'Services',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Our Services',
                    'subheading': 'Comprehensive contracting services for residential and commercial clients.',
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'What We Do',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'house-gear', 'title': 'Remodeling', 'text': 'Kitchens, bathrooms, basements, and whole-home renovations.'},
                        {'icon': 'tools', 'title': 'Repairs & Maintenance', 'text': 'Prompt, dependable fixes for any issue.'},
                        {'icon': 'building', 'title': 'New Construction', 'text': 'From foundation to finish, built to last.'},
                        {'icon': 'brush', 'title': 'Finishing Work', 'text': 'Painting, trim, flooring, and detail work.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'text_block',
                    'layout': 'layout_2',
                    'heading': 'About Our Company',
                    'subheading': 'We are a family-owned contracting business serving the community for over 20 years.\n\nOur team takes pride in craftsmanship, honest pricing, and treating every home like our own. From the first estimate to the final walkthrough, we keep you informed and involved.',
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'What Our Clients Say',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Sarah M.', 'text': 'They transformed our kitchen and finished ahead of schedule. Highly recommend.'},
                        {'title': 'James T.', 'text': 'Honest, professional, and the quality was outstanding.'},
                        {'title': 'The Reyes Family', 'text': 'Great communication from start to finish. We love our new deck.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'nav_slot': 'right',     # Demo: Contact pushed to the right of the navbar
            'sections': [
                {
                    'type': 'contact_form',
                    'layout': 'layout_1',
                    'heading': 'Get in Touch',
                    'subheading': 'Tell us about your project and we will get back to you within one business day.',
                },
            ],
        },
    ],
}


RESTAURANT_PACK = {
    'key': 'restaurant',
    'name': 'Restaurant / Cafe',
    'description': 'For restaurants, cafes, food trucks, and catering businesses.',
    'theme_key': 'sunset',
    'navbar': 'app',
    'footer': 'footer_4',
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Good food, great company.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_2',
                    'heading': 'Fresh Food, Warm Atmosphere',
                    'subheading': 'Made from scratch with locally sourced ingredients. Join us for breakfast, lunch, and dinner.',
                    'items': [
                        {'link_text': 'View Our Menu', 'link_url': '/menu/'},
                        {'link_text': 'Reserve a Table', 'link_url': '/contact/'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Why Guests Love Us',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'egg-fried', 'title': 'Fresh Ingredients', 'text': 'Every dish is made to order with seasonal, locally sourced produce.'},
                        {'icon': 'cup-hot', 'title': 'Craft Beverages', 'text': 'Specialty coffees, teas, and house-made drinks to complement every meal.'},
                        {'icon': 'people', 'title': 'Great for Groups', 'text': 'Spacious dining room and private event space for parties of any size.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Open Tuesday through Sunday',
                    'subheading': 'Breakfast 7am–11am · Lunch 11am–3pm · Dinner 5pm–9pm',
                    'items': [
                        {'link_text': 'Make a Reservation', 'link_url': '/contact/'},
                    ],
                },
            ],
        },
        {
            'page_type': 'services',
            'slug': 'menu',
            'title': 'Menu',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Our Menu',
                    'subheading': 'Something for everyone - hearty plates, lighter bites, and daily specials.',
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'What We Serve',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'sunrise', 'title': 'Breakfast & Brunch', 'text': 'Eggs any style, pancakes, avocado toast, and weekend specials.'},
                        {'icon': 'egg-fried', 'title': 'Lunch', 'text': 'Soups, salads, sandwiches, and seasonal grain bowls.'},
                        {'icon': 'moon-stars', 'title': 'Dinner', 'text': 'Pasta, grilled mains, shareables, and rotating chef specials.'},
                        {'icon': 'cup-hot', 'title': 'Drinks', 'text': 'House-roasted coffee, craft cocktails, wine, and local beers.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'text_block',
                    'layout': 'layout_2',
                    'heading': 'Our Story',
                    'subheading': 'We started as a small neighborhood cafe with a simple idea: serve honest food made with care.\n\nOver the years we have grown into a beloved local spot without ever losing what made us special - a warm welcome, a familiar face, and a meal worth coming back for.',
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'What Our Guests Say',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Amanda R.', 'text': 'Best brunch in town, hands down. The eggs benedict alone is worth the trip.'},
                        {'title': 'Carlos N.', 'text': 'We come every Sunday. The staff knows our order by heart. It feels like home.'},
                        {'title': 'Priya L.', 'text': 'Fantastic vegetarian options and the coffee is incredible. My new regular spot.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'nav_slot': 'right',
            'sections': [
                {
                    'type': 'contact_form',
                    'layout': 'layout_1',
                    'heading': 'Reservations & Inquiries',
                    'subheading': 'Book a table, ask about private dining, or just say hello. We will get back to you within 24 hours.',
                },
            ],
        },
    ],
}


SALON_PACK = {
    'key': 'salon',
    'name': 'Salon & Spa',
    'description': 'For hair salons, spas, nail studios, and beauty professionals.',
    'theme_key': 'rose',
    'navbar': 'app',
    'footer': 'footer_4',
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Look your best, feel your best.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_2',
                    'heading': 'Where Style Meets Relaxation',
                    'subheading': 'Expert stylists, a calming atmosphere, and personalized service - all in one place.',
                    'items': [
                        {'link_text': 'Book an Appointment', 'link_url': '/contact/'},
                        {'link_text': 'See Our Services', 'link_url': '/services/'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'The Experience You Deserve',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'scissors', 'title': 'Expert Stylists', 'text': 'Our team brings years of training and a passion for making you look great.'},
                        {'icon': 'stars', 'title': 'Premium Products', 'text': 'We use only top-quality, professional-grade products in every service.'},
                        {'icon': 'heart', 'title': 'Personalized Care', 'text': 'Every appointment is tailored to your unique hair type, skin, and style goals.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Ready for a Fresh Look?',
                    'subheading': 'New clients welcome. Book online or give us a call to schedule your visit.',
                    'items': [
                        {'link_text': 'Book Now', 'link_url': '/contact/'},
                    ],
                },
            ],
        },
        {
            'page_type': 'services',
            'slug': 'services',
            'title': 'Services',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Our Services',
                    'subheading': 'From everyday cuts to special-occasion styling - we do it all.',
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'What We Offer',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'scissors', 'title': 'Cuts & Styling', 'text': "Haircuts, blowouts, and special-occasion styles for all hair types."},
                        {'icon': 'palette', 'title': 'Color & Highlights', 'text': 'Balayage, full color, highlights, and corrective color by certified colorists.'},
                        {'icon': 'flower1', 'title': 'Facials & Skincare', 'text': 'Customized facials, peels, and treatments for healthy, glowing skin.'},
                        {'icon': 'hand-index-thumb', 'title': 'Nails', 'text': 'Manicures, pedicures, gel, and nail art by skilled nail technicians.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'text_block',
                    'layout': 'layout_2',
                    'heading': 'About Us',
                    'subheading': 'We opened our doors with one goal: to create a space where every client leaves feeling confident and cared for.\n\nOur team of licensed professionals stays current with the latest trends and techniques through ongoing education. Whether you are here for a quick trim or a full day of pampering, you are in good hands.',
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'Client Love',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Jessica K.', 'text': 'I have been coming here for three years and I would never go anywhere else. They truly listen.'},
                        {'title': 'Marcus D.', 'text': 'Got a balayage that turned out exactly as I hoped. The colorist is an absolute artist.'},
                        {'title': 'Olivia S.', 'text': 'The atmosphere is so relaxing and the facial left my skin glowing for a week.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Book',
            'order': 3,
            'nav_slot': 'right',
            'sections': [
                {
                    'type': 'contact_form',
                    'layout': 'layout_1',
                    'heading': 'Book an Appointment',
                    'subheading': 'Tell us what service you are interested in and your preferred date and time. We will confirm within one business day.',
                },
            ],
        },
    ],
}


LAW_FIRM_PACK = {
    'key': 'law_firm',
    'name': 'Law Firm',
    'description': 'For attorneys, legal practices, and professional services firms.',
    'theme_key': 'midnight',
    'navbar': 'app',
    'footer': 'footer_4',
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Experienced counsel you can trust.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_2',
                    'heading': 'Proven Advocacy. Trusted Results.',
                    'subheading': 'We fight for our clients with diligence, integrity, and decades of courtroom experience.',
                    'items': [
                        {'link_text': 'Schedule a Consultation', 'link_url': '/contact/'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Why Clients Choose Us',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'shield-check', 'title': 'Experienced Attorneys', 'text': 'Our team has handled thousands of cases across a broad range of practice areas.'},
                        {'icon': 'person-check', 'title': 'Client-First Approach', 'text': 'We return calls, explain every step, and keep you informed throughout your case.'},
                        {'icon': 'award', 'title': 'Track Record of Success', 'text': 'Consistently strong outcomes achieved through thorough preparation and skilled advocacy.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Your Case Starts with a Conversation',
                    'subheading': 'Consultations are confidential. Reach out today and let us review your situation.',
                    'items': [
                        {'link_text': 'Request a Consultation', 'link_url': '/contact/'},
                        {'link_text': 'Call Our Office', 'link_url': 'tel:5550000000'},
                    ],
                },
            ],
        },
        {
            'page_type': 'services',
            'slug': 'practice-areas',
            'title': 'Practice Areas',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Practice Areas',
                    'subheading': 'We bring focused expertise to the matters that affect you most.',
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'How We Can Help',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'briefcase', 'title': 'Business & Commercial', 'text': 'Contracts, disputes, mergers, and day-to-day business legal needs.'},
                        {'icon': 'house', 'title': 'Real Estate', 'text': 'Transactions, closings, landlord-tenant matters, and property disputes.'},
                        {'icon': 'people', 'title': 'Family Law', 'text': 'Divorce, custody, support, and adoption handled with care and discretion.'},
                        {'icon': 'file-earmark-text', 'title': 'Estate Planning', 'text': 'Wills, trusts, powers of attorney, and probate administration.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'text_block',
                    'layout': 'layout_2',
                    'heading': 'About Our Firm',
                    'subheading': 'Founded on the principles of honest counsel and zealous advocacy, our firm has served clients in this community for over 25 years.\n\nWe believe every client deserves access to skilled legal representation, clear communication, and a lawyer who genuinely cares about the outcome. That commitment drives everything we do.',
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'Client Testimonials',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Robert H.', 'text': 'They handled our business dispute quickly and professionally. An exceptional team.'},
                        {'title': 'Maria G.', 'text': 'Going through a divorce is hard. This firm made a difficult process as smooth as possible.'},
                        {'title': 'David P.', 'text': 'Clear, honest advice from day one. They told me exactly what to expect and delivered.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'nav_slot': 'right',
            'sections': [
                {
                    'type': 'contact_form',
                    'layout': 'layout_1',
                    'heading': 'Schedule a Consultation',
                    'subheading': 'All inquiries are confidential. Describe your situation and we will be in touch within one business day.',
                },
            ],
        },
    ],
}


MEDICAL_PACK = {
    'key': 'medical',
    'name': 'Medical / Dental Practice',
    'description': 'For doctors, dentists, therapists, and healthcare clinics.',
    'theme_key': 'ocean',
    'navbar': 'app',
    'footer': 'footer_4',
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Compassionate care for your whole family.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_2',
                    'heading': 'Healthcare You Can Count On',
                    'subheading': 'Welcoming new patients. Our team provides compassionate, comprehensive care for patients of all ages.',
                    'items': [
                        {'link_text': 'Request an Appointment', 'link_url': '/contact/'},
                        {'link_text': 'Our Services', 'link_url': '/services/'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Why Patients Trust Us',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'heart-pulse', 'title': 'Experienced Providers', 'text': 'Board-certified physicians and specialists with years of hands-on clinical experience.'},
                        {'icon': 'clock', 'title': 'Same-Day Appointments', 'text': 'We work hard to see urgent patients the same day whenever possible.'},
                        {'icon': 'shield-plus', 'title': 'Most Insurance Accepted', 'text': 'We accept most major insurance plans and offer flexible payment options.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Now Accepting New Patients',
                    'subheading': 'Getting started is easy. Request an appointment online or call our front desk.',
                    'items': [
                        {'link_text': 'Book an Appointment', 'link_url': '/contact/'},
                        {'link_text': 'Call Us', 'link_url': 'tel:5550000000'},
                    ],
                },
            ],
        },
        {
            'page_type': 'services',
            'slug': 'services',
            'title': 'Services',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Our Services',
                    'subheading': 'Comprehensive care from routine check-ups to specialized treatment.',
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'What We Offer',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'clipboard2-pulse', 'title': 'Preventive Care', 'text': 'Annual physicals, screenings, immunizations, and wellness visits.'},
                        {'icon': 'bandaid', 'title': 'Acute & Urgent Care', 'text': 'Prompt diagnosis and treatment for illness and injury.'},
                        {'icon': 'heart-pulse', 'title': 'Chronic Disease Management', 'text': 'Ongoing support for diabetes, hypertension, asthma, and more.'},
                        {'icon': 'people', 'title': 'Family Medicine', 'text': 'Care for every member of your family, from pediatrics to senior health.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'text_block',
                    'layout': 'layout_2',
                    'heading': 'About Our Practice',
                    'subheading': 'We are an independent practice built on a simple belief: patients deserve more than a rushed appointment.\n\nOur providers take time to listen, explain, and involve you in every care decision. We combine the warmth of a community clinic with the capabilities of a modern medical facility.',
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'Patient Stories',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Linda F.', 'text': 'My whole family comes here. The doctors listen and never make you feel rushed.'},
                        {'title': 'Tom W.', 'text': 'Got a same-day appointment when I really needed one. This practice goes above and beyond.'},
                        {'title': 'Angela M.', 'text': 'Compassionate, thorough, and genuinely kind. Exactly what healthcare should feel like.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'nav_slot': 'right',
            'sections': [
                {
                    'type': 'contact_form',
                    'layout': 'layout_1',
                    'heading': 'Request an Appointment',
                    'subheading': 'Fill out the form below and our team will contact you to confirm your appointment time.',
                },
            ],
        },
    ],
}


REAL_ESTATE_PACK = {
    'key': 'real_estate',
    'name': 'Real Estate Agent',
    'description': 'For real estate agents, brokers, and property professionals.',
    'theme_key': 'classic_blue',
    'navbar': 'app',
    'footer': 'footer_4',
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Your trusted guide to buying and selling.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_2',
                    'heading': "Find the Home You Have Been Looking For",
                    'subheading': 'Local expertise, honest guidance, and a relentless commitment to getting you the best deal.',
                    'items': [
                        {'link_text': 'View Listings', 'link_url': '/listings/'},
                        {'link_text': 'Contact Me', 'link_url': '/contact/'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Why Work With Me',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'geo-alt', 'title': 'Local Market Expert', 'text': 'Deep knowledge of neighborhoods, pricing trends, and off-market opportunities.'},
                        {'icon': 'graph-up', 'title': 'Proven Negotiator', 'text': 'Skilled at getting buyers the best price and maximizing sellers returns.'},
                        {'icon': 'chat-dots', 'title': 'Always Responsive', 'text': 'You will always have a direct line to me - no assistants, no runaround.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Buying or Selling? Let\'s Talk.',
                    'subheading': 'Free consultations with no pressure and no obligation. I am here to help you make the right move.',
                    'items': [
                        {'link_text': 'Schedule a Call', 'link_url': '/contact/'},
                    ],
                },
            ],
        },
        {
            'page_type': 'services',
            'slug': 'listings',
            'title': 'Listings',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Featured Listings',
                    'subheading': 'Homes currently on the market - each one hand-selected for quality and value.',
                },
                {
                    'type': 'image_grid',
                    'layout': 'layout_1',
                    'heading': 'Available Properties',
                    'subheading': 'Contact me for showings, pricing details, and neighborhood information.',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': '4 Bed / 2 Bath Colonial', 'text': 'Quiet cul-de-sac, updated kitchen, large yard.'},
                        {'title': '2 Bed / 2 Bath Condo', 'text': 'Downtown location, modern finishes, covered parking.'},
                        {'title': '3 Bed / 1 Bath Ranch', 'text': 'Move-in ready, new roof, great starter home.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'text_block',
                    'layout': 'layout_2',
                    'heading': 'About Me',
                    'subheading': 'I have been helping families buy and sell homes in this area for over 15 years.\n\nReal estate is personal. Whether you are a first-time buyer, a growing family, or downsizing for retirement, I take the time to understand your goals and guide you every step of the way. My clients become lifelong connections.',
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'Client Testimonials',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'The Okafor Family', 'text': 'Found us our dream home in a tough market. Incredibly patient and knowledgeable.'},
                        {'title': 'Sandra B.', 'text': 'Sold my house in 11 days above asking price. I could not be happier.'},
                        {'title': 'Kevin & Dana L.', 'text': 'As first-time buyers we had so many questions. They answered every single one.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'nav_slot': 'right',
            'sections': [
                {
                    'type': 'contact_form',
                    'layout': 'layout_1',
                    'heading': 'Get in Touch',
                    'subheading': 'Looking to buy, sell, or just explore your options? Send me a message and I will reach out within one business day.',
                },
            ],
        },
    ],
}


FITNESS_PACK = {
    'key': 'fitness',
    'name': 'Fitness & Personal Training',
    'description': 'For personal trainers, gyms, yoga studios, and wellness coaches.',
    'theme_key': 'forest',
    'navbar': 'app',
    'footer': 'footer_4',
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Stronger every day.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_2',
                    'heading': 'Your Fitness Goals Start Here',
                    'subheading': 'Personalized training, real results, and a coach who is with you every rep of the way.',
                    'items': [
                        {'link_text': 'Start Your Free Session', 'link_url': '/contact/'},
                        {'link_text': 'View Programs', 'link_url': '/programs/'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'What Sets Us Apart',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'trophy', 'title': 'Real Results', 'text': 'Our clients average 20 lbs lost and measurable strength gains within their first 90 days.'},
                        {'icon': 'lightning', 'title': 'Personalized Plans', 'text': 'No cookie-cutter workouts. Every program is built around your body, schedule, and goals.'},
                        {'icon': 'people', 'title': 'Supportive Community', 'text': 'Train alongside motivated people who push each other to show up and level up.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Ready to Make a Change?',
                    'subheading': 'Your first session is free. No commitment, no pressure - just come in and see what it feels like.',
                    'items': [
                        {'link_text': 'Claim Your Free Session', 'link_url': '/contact/'},
                    ],
                },
            ],
        },
        {
            'page_type': 'services',
            'slug': 'programs',
            'title': 'Programs',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Training Programs',
                    'subheading': 'Built for every fitness level - from first-timers to competitive athletes.',
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Find Your Program',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'person-walking', 'title': '1-on-1 Personal Training', 'text': 'Fully customized sessions with undivided coaching attention and detailed progress tracking.'},
                        {'icon': 'people', 'title': 'Small Group Training', 'text': 'The energy of a class with the attention of personal training. Groups of 4–6.'},
                        {'icon': 'calendar2-check', 'title': 'Online Coaching', 'text': 'Train anywhere with a structured plan, weekly check-ins, and direct coach access.'},
                        {'icon': 'apple', 'title': 'Nutrition Coaching', 'text': 'Fuel your results with a personalized nutrition strategy built around your lifestyle.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'text_block',
                    'layout': 'layout_2',
                    'heading': 'About Your Coach',
                    'subheading': 'I became a personal trainer because fitness changed my life - and I want to share that with others.\n\nWith certifications in strength and conditioning, nutrition, and corrective exercise, I bring both the science and the motivation to every session. My philosophy is simple: build sustainable habits, celebrate every win, and never stop improving.',
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'Client Success Stories',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'title': 'Mike T.', 'text': 'Lost 35 pounds in six months and actually enjoyed the process. Best investment I have made.'},
                        {'title': 'Rachel K.', 'text': 'I went from never working out to completing my first 5K. The accountability made all the difference.'},
                        {'title': 'James & Tara W.', 'text': 'We train together as a couple. The programs keep it fresh and we push each other.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'nav_slot': 'right',
            'sections': [
                {
                    'type': 'contact_form',
                    'layout': 'layout_1',
                    'heading': 'Let\'s Get Started',
                    'subheading': 'Tell me about your goals and current fitness level. I will put together a plan and reach out within 24 hours.',
                },
            ],
        },
    ],
}


BLOG_PACK = {
    'key': 'blog',
    'name': 'Blog / Content Site',
    'description': 'A clean site built around publishing. Home page, blog, about, and contact.',
    'theme_key': 'ocean',
    'navbar': 'classic',
    'footer': 'footer_2',
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Ideas worth sharing.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Ideas Worth Sharing',
                    'subheading': 'Insights, stories, and guides from our team. Fresh content every week.',
                    'items': [
                        {'link_text': 'Read the Blog', 'link_url': '/blog/'},
                        {'link_text': 'About Us', 'link_url': '/about/', 'link_style': 'btn-outline-secondary'},
                    ],
                },
                {
                    'type': 'recent_posts',
                    'layout': 'layout_1',
                    'heading': 'Latest Posts',
                    'config': {'post_count': 3},
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Have a question or topic request?',
                    'subheading': 'We love hearing from our readers.',
                    'items': [
                        {'link_text': 'Get in Touch', 'link_url': '/contact/'},
                    ],
                },
            ],
        },
        {
            'page_type': 'blog',
            'slug': 'blog',
            'title': 'Blog',
            'order': 1,
            'nav_label': 'Blog',
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'The Blog',
                    'subheading': 'Articles, guides, and stories from our team.',
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'About Us',
                    'subheading': 'We write about things we care about. Here is who we are.',
                },
                {
                    'type': 'text_block',
                    'layout': 'layout_1',
                    'heading': 'Our Story',
                    'subheading': 'Tell your story here. Why did you start writing? What do you cover? Who is your audience?',
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Get in Touch',
                    'subheading': 'Questions, feedback, or just want to say hello — we would love to hear from you.',
                },
                {
                    'type': 'contact_form',
                    'layout': 'layout_2',
                    'heading': 'Send a Message',
                },
            ],
        },
    ],
}


ECOMMERCE_PACK = {
    'key': 'ecommerce',
    'name': 'Online Store',
    'description': 'A storefront ready for products and Stripe checkout. Shop, about, and contact pages.',
    'theme_key': 'slate',
    'navbar': 'app',
    'footer': 'footer_2',
    'brand_position': 'left',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Quality products, delivered.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Shop Our Products',
                    'subheading': 'Quality you can trust, shipped straight to your door.',
                    'items': [
                        {'link_text': 'Browse Products', 'link_url': '/shop/'},
                        {'link_text': 'Our Story', 'link_url': '/about/', 'link_style': 'btn-outline-secondary'},
                    ],
                },
                {
                    'type': 'product_grid',
                    'layout': 'layout_1',
                    'heading': 'Featured Products',
                    'config': {'columns_desktop': 3},
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'Why Shop With Us',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'shield-fill-check', 'title': 'Secure Checkout',  'text': 'Payments processed securely by Stripe.'},
                        {'icon': 'truck',              'title': 'Fast Shipping',    'text': 'Orders ship within 1–2 business days.'},
                        {'icon': 'arrow-return-left',  'title': 'Easy Returns',     'text': '30-day hassle-free returns.'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Questions Before You Buy?',
                    'subheading': 'We are happy to help.',
                    'items': [
                        {'link_text': 'Contact Us', 'link_url': '/contact/'},
                    ],
                },
            ],
        },
        {
            'page_type': 'ecommerce',
            'slug': 'shop',
            'title': 'Shop',
            'order': 1,
            'nav_label': 'Shop',
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Our Products',
                    'subheading': 'Browse everything we carry.',
                },
                {
                    'type': 'product_grid',
                    'layout': 'layout_1',
                    'heading': '',
                    'config': {'columns_desktop': 3},
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'About Us',
                    'subheading': 'We are a small team that cares deeply about what we make.',
                },
                {
                    'type': 'text_block',
                    'layout': 'layout_1',
                    'heading': 'Our Story',
                    'subheading': 'Tell your story here — why you started, what you stand for, who you make things for.',
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_2',
                    'heading': 'Our Values',
                    'items': [
                        {'icon': 'award-fill',     'title': 'Quality First',    'text': 'We only sell what we would be proud to own ourselves.'},
                        {'icon': 'people-fill',    'title': 'Customer Focus',   'text': 'Your satisfaction is the only metric that matters.'},
                        {'icon': 'recycle',        'title': 'Sustainability',   'text': 'We are committed to responsible sourcing and packaging.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Get in Touch',
                    'subheading': 'Questions about an order, a product, or anything else — we are here.',
                },
                {
                    'type': 'contact_form',
                    'layout': 'layout_2',
                    'heading': 'Send a Message',
                    'items': [
                        {'icon': 'envelope-fill', 'title': 'Email', 'text': 'hello@example.com', 'link_url': 'mailto:hello@example.com'},
                    ],
                },
            ],
        },
    ],
}


ARCHITECTURE_PACK = {
    'key': 'architecture',
    'name': 'Architect / Home Designer',
    'description': 'For architects, home/house-plan designers, and drafting services — portfolio, services, process, and an inquiry form.',
    'theme_key': 'slate',          # clean, professional, trustworthy
    'navbar': 'centered',
    'footer': 'footer_4',
    'brand_position': 'center',
    'show_brand_logo': True,
    'show_brand_name': True,
    'tagline': 'Thoughtful home design, built to code.',
    'pages': [
        {
            'page_type': 'home',
            'slug': 'home',
            'title': 'Home',
            'order': 0,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Thoughtful Home Design, Built to Code',
                    'subheading': 'Stock and custom house plans designed with form, function, and style in mind — permit-ready and made for the way you live.',
                    'items': [
                        {'item_type': 'button', 'link_text': 'View Our Work', 'link_url': '#work'},
                        {'item_type': 'button', 'link_text': 'Start a Project', 'link_url': '/contact/', 'link_style': 'btn-outline-secondary'},
                    ],
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'What We Do',
                    'subheading': 'From first sketch to permit-ready drawings.',
                    'config': {'columns_desktop': 3},
                    'items': [
                        {'icon': 'house-door-fill',   'title': 'Custom Home Plans',   'text': 'Fully custom designs tailored to your lot, budget, and lifestyle.'},
                        {'icon': 'pencil-square',     'title': 'Plan Modifications',  'text': 'Already have a plan? We adapt stock or existing drawings to fit your needs.'},
                        {'icon': 'file-earmark-text', 'title': 'Permit & Framing',    'text': 'Code-compliant construction documents, framing plans, and permit packages.'},
                    ],
                },
                {
                    'type': 'plan_grid',
                    'layout': 'layout_1',
                    'heading': 'Featured Plans & Projects',
                    'subheading': 'A selection of recent designs.',
                    'config': {'columns_desktop': 3, 'plan_count': 6},
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_2',
                    'heading': 'How It Works',
                    'subheading': 'A clear path from idea to build.',
                    'config': {'show_step_number': 'true'},
                    'items': [
                        {'icon': 'chat-dots-fill',    'title': 'Consultation',         'text': 'We talk through your goals, site, budget, and must-haves.'},
                        {'icon': 'pencil-fill',       'title': 'Design & Revisions',   'text': 'You review concepts and we refine until the plan feels right.'},
                        {'icon': 'check-circle-fill', 'title': 'Permit-Ready Plans',   'text': 'You receive complete, code-compliant drawings ready to build.'},
                    ],
                },
                {
                    'type': 'testimonials',
                    'layout': 'layout_1',
                    'heading': 'What Clients Say',
                    'items': [
                        {'title': 'Sarah & Tom',  'link_text': 'New Build, Maine',     'text': 'Mike turned our rough ideas into a plan our builder loved. Fast, thorough, and a pleasure to work with.', 'icon': 'star-fill'},
                        {'title': 'David R.',     'link_text': 'Renovation',           'text': 'He modified an existing plan on a short turnaround and saved our timeline. Highly recommended.', 'icon': 'star-fill'},
                        {'title': 'The Bennetts', 'link_text': 'Custom Home',          'text': 'Beautiful, functional design that fit our budget. The permit set was flawless.', 'icon': 'star-fill'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Ready to design your dream home?',
                    'subheading': 'Tell us about your project and we will get back to you within one business day.',
                    'items': [
                        {'item_type': 'button', 'link_text': 'Get Started', 'link_url': '/contact/'},
                    ],
                },
            ],
        },
        {
            'page_type': 'services',
            'slug': 'services',
            'title': 'Services',
            'order': 1,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Design Services',
                    'subheading': 'Everything you need to go from concept to construction.',
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_1',
                    'heading': 'What I Offer',
                    'config': {'columns_desktop': 2},
                    'items': [
                        {'icon': 'house-door-fill',   'title': 'Custom House Plans',  'text': 'One-of-a-kind designs drawn around your site and lifestyle.'},
                        {'icon': 'grid-3x3-gap-fill', 'title': 'Stock Plan Library',  'text': 'Proven, ready-to-purchase plans you can build as-is or modify.'},
                        {'icon': 'pencil-square',     'title': 'Modifications',       'text': 'Adjust an existing or stock plan — layouts, footprints, elevations.'},
                        {'icon': 'file-earmark-text', 'title': 'Permit & Framing',    'text': 'Complete construction documents and framing plans for permitting.'},
                    ],
                },
                {
                    'type': 'pricing_table',
                    'layout': 'layout_1',
                    'heading': 'Simple, Transparent Pricing',
                    'subheading': 'Every project is unique — these are typical starting points.',
                    'config': {'highlighted_plan': 2},
                    'items': [
                        {'title': 'Stock Plan',    'link_text': 'from $1,200', 'link_url': '/contact/', 'text': 'one-time\nReady-to-build plan set\nPDF + CAD files\nEmail support'},
                        {'title': 'Custom Design', 'link_text': 'from $4,500', 'link_url': '/contact/', 'icon': 'star-fill', 'text': 'per project\nFully custom plans\nMultiple revisions\nPermit-ready set\nFraming plan included'},
                        {'title': 'Modification',  'link_text': 'from $600',   'link_url': '/contact/', 'text': 'per plan\nEdit an existing plan\nLayout & elevation changes\nUpdated drawings'},
                    ],
                },
                {
                    'type': 'cta_banner',
                    'layout': 'layout_1',
                    'heading': 'Not sure which fits? Let’s talk.',
                    'items': [
                        {'item_type': 'button', 'link_text': 'Request a Quote', 'link_url': '/contact/'},
                    ],
                },
            ],
        },
        {
            'page_type': 'about',
            'slug': 'about',
            'title': 'About',
            'order': 2,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_2',
                    'heading': 'About the Designer',
                    'subheading': 'Decades of experience turning ideas into homes people love to live in.',
                },
                {
                    'type': 'text_block',
                    'layout': 'layout_1',
                    'heading': 'Our Approach',
                    'subheading': (
                        'Tell your story here — how you got started, what kinds of homes you love to design, '
                        'and what clients can expect when they work with you.\n\n'
                        'A second paragraph is a good place to talk about your design philosophy and the '
                        'regions or code jurisdictions you serve.'
                    ),
                },
                {
                    'type': 'feature_list',
                    'layout': 'layout_2',
                    'heading': 'Why Work With Me',
                    'items': [
                        {'icon': 'patch-check-fill', 'title': 'Code-Compliant',      'text': 'Drawings built to pass review and keep your project on schedule.'},
                        {'icon': 'geo-alt-fill',     'title': 'Local Expertise',     'text': 'Familiar with regional building codes, climate, and permitting.'},
                        {'icon': 'person-hearts',    'title': 'Personal Service',    'text': 'You work directly with the designer from first call to final plan.'},
                    ],
                },
            ],
        },
        {
            'page_type': 'contact',
            'slug': 'contact',
            'title': 'Contact',
            'order': 3,
            'sections': [
                {
                    'type': 'hero',
                    'layout': 'layout_1',
                    'heading': 'Get in Touch',
                    'subheading': 'Tell me about your project and I will follow up within one business day.',
                },
                {
                    'type': 'contact_form',
                    'layout': 'layout_2',
                    'heading': 'Request a Consultation',
                    'subheading': 'Share a few details about your lot, timeline, and what you have in mind.',
                    'items': [
                        {'icon': 'telephone-fill', 'title': 'Phone',   'text': '+1 (555) 000-0000',   'link_url': 'tel:+15550000000'},
                        {'icon': 'envelope-fill',  'title': 'Email',   'text': 'hello@example.com',    'link_url': 'mailto:hello@example.com'},
                        {'icon': 'geo-alt-fill',   'title': 'Service Area', 'text': 'New England & remote'},
                    ],
                },
            ],
        },
    ],
}


# Registry of all available packs, keyed by their `key`.
PACKS = {
    CONTRACTOR_PACK['key']: CONTRACTOR_PACK,
    RESTAURANT_PACK['key']: RESTAURANT_PACK,
    SALON_PACK['key']:      SALON_PACK,
    LAW_FIRM_PACK['key']:   LAW_FIRM_PACK,
    MEDICAL_PACK['key']:    MEDICAL_PACK,
    REAL_ESTATE_PACK['key']: REAL_ESTATE_PACK,
    FITNESS_PACK['key']:    FITNESS_PACK,
    BLOG_PACK['key']:       BLOG_PACK,
    ECOMMERCE_PACK['key']:  ECOMMERCE_PACK,
    ARCHITECTURE_PACK['key']: ARCHITECTURE_PACK,
}


def get_pack(key):
    """Return a pack dict by key, or None if not found."""
    return PACKS.get(key)


def list_packs():
    """Return [(key, name, description), ...] for all packs, for menus."""
    return [
        (p['key'], p['name'], p.get('description', ''))
        for p in PACKS.values()
    ]

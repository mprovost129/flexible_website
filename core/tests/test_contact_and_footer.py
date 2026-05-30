from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Page, Section, Site


def ensure_admin():
    """First-run setup middleware redirects everything to /setup/ until an
    admin exists. Tests exercise a normal (already-set-up) site, so make sure
    one superuser is present."""
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser(email="admin@example.com", password="testpass12345")


@override_settings(DEFAULT_FROM_EMAIL="default@example.com")
class ContactSubmitSecurityTests(TestCase):
    def setUp(self):
        ensure_admin()
        cache.clear()
        self.site = Site.get_current()
        self.contact_page = Page.objects.create(
            site=self.site,
            page_type="contact",
            variant="home_1",
            slug="contact",
            title="Contact",
            is_enabled=True,
            order=0,
        )
        self.about_page = Page.objects.create(
            site=self.site,
            page_type="about",
            variant="home_1",
            slug="about",
            title="About",
            is_enabled=True,
            order=1,
        )

        self.contact_section = Section.objects.create(
            page=self.contact_page,
            section_type="contact_form",
            layout="layout_1",
            order=0,
            is_visible=True,
            config={"to_email": "owner@example.com"},
        )
        self.about_section = Section.objects.create(
            page=self.about_page,
            section_type="contact_form",
            layout="layout_1",
            order=0,
            is_visible=True,
            config={"to_email": "about-owner@example.com"},
        )

    def _base_payload(self):
        return {
            "name": "Taylor",
            "email": "taylor@example.com",
            "subject": "Question",
            "message": "Hello from the test suite.",
            "website": "",
        }

    @patch("core.views.send_mail")
    def test_ignores_posted_to_email_uses_section_config(self, mock_send_mail):
        payload = {
            **self._base_payload(),
            "page_slug": "contact",
            "section_id": str(self.contact_section.id),
            "to_email": "attacker@example.com",
        }

        response = self.client.post(reverse("core:contact_submit"), payload)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("core:page", kwargs={"slug": "contact"}))
        mock_send_mail.assert_called_once()
        self.assertEqual(
            mock_send_mail.call_args.kwargs["recipient_list"],
            ["owner@example.com"],
        )

    @patch("core.views.send_mail")
    def test_mismatched_section_and_page_slug_falls_back_to_default(self, mock_send_mail):
        payload = {
            **self._base_payload(),
            "page_slug": "contact",
            "section_id": str(self.about_section.id),
            "to_email": "attacker@example.com",
        }

        response = self.client.post(reverse("core:contact_submit"), payload)

        self.assertEqual(response.status_code, 302)
        mock_send_mail.assert_called_once()
        self.assertEqual(
            mock_send_mail.call_args.kwargs["recipient_list"],
            ["default@example.com"],
        )

    @patch("core.views.send_mail")
    def test_rate_limit_blocks_after_five_submissions_per_minute(self, mock_send_mail):
        payload = {
            **self._base_payload(),
            "page_slug": "contact",
            "section_id": str(self.contact_section.id),
        }

        for _ in range(6):
            self.client.post(reverse("core:contact_submit"), payload)

        self.assertEqual(mock_send_mail.call_count, 5)


class FooterRenderingTests(TestCase):
    def setUp(self):
        ensure_admin()
        self.site = Site.get_current()
        self.site.copyright_text = "© 2026 CBL. Built for fast-moving marketing teams."
        self.site.show_footer = True
        self.site.save(update_fields=["copyright_text", "show_footer"])

        Page.objects.create(
            site=self.site,
            page_type="home",
            variant="home_1",
            slug="home",
            title="Home",
            is_enabled=True,
            order=0,
        )

    def test_footer_variants_render_single_source_copyright_text(self):
        variants = ["footer_1", "footer_2", "footer_3", "footer_4", "footer_5"]

        for variant in variants:
            with self.subTest(variant=variant):
                self.site.footer_variant = variant
                self.site.save(update_fields=["footer_variant"])

                response = self.client.get(reverse("core:home"))
                html = response.content.decode("utf-8")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(html.count(self.site.copyright_text), 1)
                self.assertNotIn("© 2026 © 2026", html)


class AccessibilityShellTests(TestCase):
    def setUp(self):
        ensure_admin()
        self.site = Site.get_current()

        self.home_page = Page.objects.create(
            site=self.site,
            page_type="home",
            variant="home_1",
            slug="home",
            title="Home",
            is_enabled=True,
            order=0,
        )

        self.contact_page = Page.objects.create(
            site=self.site,
            page_type="contact",
            variant="home_1",
            slug="contact",
            title="Contact",
            is_enabled=True,
            order=1,
        )

        Section.objects.create(
            page=self.contact_page,
            section_type="contact_form",
            layout="layout_1",
            order=0,
            is_visible=True,
            heading="Contact",
            subheading="Talk to us",
            config={"show_subject": "true"},
        )

    def _response_html(self, response):
        self.assertEqual(response.status_code, 200)
        return response.content.decode("utf-8")

    def test_base_shell_includes_skip_link_and_main_target(self):
        response = self.client.get(reverse("core:home"))
        html = self._response_html(response)

        self.assertIn('class="skip-link" href="#main-content"', html)
        self.assertIn('<main id="main-content" tabindex="-1">', html)

    def test_contact_honeypot_input_has_accessible_label(self):
        response = self.client.get(reverse("core:page", kwargs={"slug": "contact"}))
        html = self._response_html(response)

        self.assertIn('name="website"', html)
        self.assertIn('aria-label="Leave this field blank"', html)


class FirstRunSetupTests(TestCase):
    """The browser-based setup wizard replaces the old shell command."""

    def test_fresh_deploy_redirects_to_setup(self):
        # No admin yet: every page bounces to the wizard.
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get("Location"), reverse("core:setup_wizard"))

    def test_healthz_bypasses_setup_redirect(self):
        # Hosting health checks must pass even before setup.
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)

    def test_wizard_creates_admin_and_locks_itself(self):
        User = get_user_model()
        self.assertFalse(User.objects.filter(is_superuser=True).exists())

        response = self.client.post(reverse("core:setup_wizard"), {
            "email": "owner@example.com",
            "password": "supersecret123",
            "password2": "supersecret123",
            "site_name": "Acme Co",
            "pack": "",
        })
        # Redirects to the live site, logged in.
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(is_superuser=True, email="owner@example.com").exists())
        self.assertEqual(Site.get_current().name, "Acme Co")

        # Wizard now locks itself.
        response = self.client.get(reverse("core:setup_wizard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get("Location"), reverse("core:dashboard_home"))

    def test_wizard_rejects_mismatched_passwords(self):
        User = get_user_model()
        response = self.client.post(reverse("core:setup_wizard"), {
            "email": "owner@example.com",
            "password": "supersecret123",
            "password2": "different456",
            "site_name": "Acme Co",
            "pack": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(is_superuser=True).exists())

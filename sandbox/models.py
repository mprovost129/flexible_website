from django.db import models
from django.utils import timezone


class SandboxSession(models.Model):
    """Tracks one visitor's temporary sandbox page.

    The related Page (and its Sections/Items) are real DB rows that get deleted
    when the session ends or expires, so nothing accumulates permanently.
    """
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    site_id     = models.IntegerField(null=True, blank=True)  # per-session core.Site clone
    page_id     = models.IntegerField()   # core.Page pk — not a FK so we can delete freely
    is_preview  = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'SandboxSession({self.session_key[:8]}…)'

    @staticmethod
    def purge_site(site_id):
        """Hard-delete a sandbox clone site and everything under it.

        We must delete the soft-deletable models via `all_objects` first: their
        default/base manager hides soft-deleted rows, so a plain Site cascade
        would leave orphaned (soft-deleted) sections/nav links behind and the
        database would refuse to drop the page they still reference.
        """
        if not site_id:
            return
        from core.models import (
            Site, Section, SectionItem, NavLink, FooterColumn, FooterLink,
        )
        SectionItem.all_objects.filter(section__page__site_id=site_id).delete()
        Section.all_objects.filter(page__site_id=site_id).delete()
        FooterLink.all_objects.filter(column__site_id=site_id).delete()
        FooterColumn.all_objects.filter(site_id=site_id).delete()
        NavLink.all_objects.filter(site_id=site_id).delete()
        Site.objects.filter(pk=site_id).delete()  # cascades pages, banners, etc.

    @staticmethod
    def purge_page(page_id):
        """Hard-delete a sandbox page (legacy sessions with no clone site)."""
        if not page_id:
            return
        from core.models import Page, Section, SectionItem
        SectionItem.all_objects.filter(section__page_id=page_id).delete()
        Section.all_objects.filter(page_id=page_id).delete()
        Page.objects.filter(pk=page_id).delete()

    @classmethod
    def cleanup_stale(cls, hours=8):
        """Delete sessions and the data behind them after `hours` of inactivity."""
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        stale = list(cls.objects.filter(last_active__lt=cutoff))
        for sb in stale:
            if sb.site_id:
                cls.purge_site(sb.site_id)
            else:
                cls.purge_page(sb.page_id)
        cls.objects.filter(pk__in=[sb.pk for sb in stale]).delete()

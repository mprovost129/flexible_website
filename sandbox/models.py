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

    @classmethod
    def cleanup_stale(cls, hours=8):
        """Delete sessions and their per-session site (which cascades to the
        page, sections, items, nav links, and footer rows)."""
        from core.models import Page, Site
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        stale = cls.objects.filter(last_active__lt=cutoff)
        site_ids = [s for s in stale.values_list('site_id', flat=True) if s]
        if site_ids:
            # Deleting the Site cascades to pages/sections/items/navlinks/footers.
            Site.objects.filter(pk__in=site_ids).delete()
        # Safety net for legacy sessions created before per-session sites existed.
        orphan_pages = [p for p, s in stale.values_list('page_id', 'site_id') if not s and p]
        if orphan_pages:
            Page.objects.filter(pk__in=orphan_pages).delete()
        stale.delete()

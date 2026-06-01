from django.db import models
from django.utils import timezone


class SandboxSession(models.Model):
    """Tracks one visitor's temporary sandbox page.

    The related Page (and its Sections/Items) are real DB rows that get deleted
    when the session ends or expires, so nothing accumulates permanently.
    """
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
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
        """Delete sessions (and their pages) that have been inactive for `hours`."""
        from core.models import Page
        cutoff = timezone.now() - timezone.timedelta(hours=hours)
        stale = cls.objects.filter(last_active__lt=cutoff)
        page_ids = list(stale.values_list('page_id', flat=True))
        if page_ids:
            Page.objects.filter(pk__in=page_ids).delete()  # cascades to sections/items
        stale.delete()

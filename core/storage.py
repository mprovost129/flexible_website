"""
Static files storage that minifies JS/CSS during `collectstatic`, then defers
to WhiteNoise for hashing (cache-busting) and gzip/brotli compression.

Only used in production (wired in config/Settings/prod.py). The dev server keeps
serving the original, readable source files untouched.

Minification is best-effort: any failure on a single file is swallowed so it
can never break a deploy — that file just ships unminified.
"""

import rcssmin
import rjsmin
from whitenoise.storage import CompressedManifestStaticFilesStorage


class MinifyingManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    def post_process(self, paths, dry_run=False, **options):
        # Minify the collected files in place BEFORE WhiteNoise hashes and
        # compresses them, so the hash + .gz/.br reflect the minified content.
        if not dry_run:
            for name in list(paths):
                self._minify(name)
        yield from super().post_process(paths, dry_run=dry_run, **options)

    def _minify(self, name):
        lower = name.lower()
        if lower.endswith(('.min.js', '.min.css')):
            return
        if lower.endswith('.js'):
            minify = rjsmin.jsmin
        elif lower.endswith('.css'):
            minify = rcssmin.cssmin
        else:
            return
        try:
            path = self.path(name)
            with open(path, 'rb') as fh:
                original = fh.read()
            minified = minify(original)
            if minified and len(minified) < len(original):
                with open(path, 'wb') as fh:
                    fh.write(minified)
        except Exception:
            # Never let minification break collectstatic; ship the file as-is.
            pass

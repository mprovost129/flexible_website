/**
 * sandbox_cleanup.js
 *
 * Runs only in sandbox mode. Watches the edit sidebar body via MutationObserver
 * and removes sections that don't apply inside a sandbox:
 *   - Page management (publish, delete, SEO, etc.)
 *   - Pages list / switch template
 *   - Page design controls
 *   - Nav / footer editing instructions
 *
 * Also injects a small sandbox info panel when the user clicks on blank page
 * space (which would otherwise show the full Page management panel).
 */
(function () {
    'use strict';

    // Sidebar section headings to remove in sandbox mode
    var REMOVE_HEADINGS = [
        'SEO',
        'Pages',
        'Theme',
        'Switch template',
        'Page design',
    ];

    // Button/element classes to remove even if the section heading is kept
    var REMOVE_CLASSES = [
        '.sidebar-page-action',
        '.sidebar-delete-page',
        '.sidebar-new-page-btn',
        '.sidebar-save-seo',
        '.sidebar-seo-title',
        '.sidebar-seo-og-title',
        '.sidebar-seo-og-desc',
        '.sidebar-save-page-design',
        '.sidebar-section-spacing',
        '.sidebar-body-bg',
    ];

    function cleanSidebar(body) {
        if (!body) return;

        // Remove entire sections by heading
        body.querySelectorAll('.edit-sidebar-section h3').forEach(function (h3) {
            if (REMOVE_HEADINGS.indexOf(h3.textContent.trim()) !== -1) {
                var section = h3.closest('.edit-sidebar-section');
                if (section) section.remove();
            }
        });

        // Remove specific elements
        REMOVE_CLASSES.forEach(function (cls) {
            body.querySelectorAll(cls).forEach(function (el) {
                // Remove the closest label + input pair, or just the element
                var wrap = el.closest('.mb-2, .mb-3, .d-grid') || el;
                wrap.remove();
            });
        });

        // Replace the publish/status badge row with a sandbox notice
        var badgeDiv = body.querySelector('.mb-3 .badge');
        if (badgeDiv) {
            var row = badgeDiv.closest('.mb-3');
            if (row && !row.dataset.sandboxPatched) {
                row.dataset.sandboxPatched = '1';
                row.innerHTML = '<span class="badge text-bg-secondary">Sandbox — changes are not saved</span>';
            }
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var sidebarBody = document.getElementById('edit-sidebar-body');
        if (!sidebarBody) return;

        // Initial clean + watch for re-renders
        cleanSidebar(sidebarBody);
        new MutationObserver(function () {
            cleanSidebar(sidebarBody);
        }).observe(sidebarBody, { childList: true });
    });
})();

/* admin_sortable.js
 *
 * Drag-and-drop reordering for TabularInline rows in the Django admin.
 * Loaded on the Page change form (sections) and the Section change form (items).
 *
 * Requirements:
 *   - SortableJS must be loaded before this script.
 *   - Each reorderable row must contain:
 *       <span class="drag-handle"
 *             data-pk="<section or item PK>"
 *             data-reorder-url="/edit/sections/reorder/">⠿</span>
 *
 * On drop: POSTs the new PK order as JSON to the URL in data-reorder-url.
 * Also syncs the visible `order` number inputs so a subsequent form Save
 * doesn't revert the order back to what the database had before.
 */

(function () {
  'use strict';

  // ── CSRF token ──────────────────────────────────────────────────────────────
  function getCsrf() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  // ── Brief green-outline flash to confirm a successful save ─────────────────
  function flashSaved(table) {
    table.style.outline = '2px solid #5cb85c';
    table.style.borderRadius = '3px';
    setTimeout(function () {
      table.style.transition = 'outline 0.6s';
      table.style.outline = '2px solid transparent';
      setTimeout(function () {
        table.style.outline = '';
        table.style.transition = '';
        table.style.borderRadius = '';
      }, 650);
    }, 400);
  }

  // ── Initialise SortableJS on a single <tbody> ───────────────────────────────
  function initSortable(tbody, url) {
    // eslint-disable-next-line no-undef
    Sortable.create(tbody, {
      handle: '.drag-handle[data-pk]',   // only real rows (with PKs) can be dragged
      animation: 150,
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',

      onEnd: function () {
        // Collect PKs in their new visual order
        var pks = [];
        tbody.querySelectorAll('.drag-handle[data-pk]').forEach(function (el) {
          pks.push(parseInt(el.dataset.pk, 10));
        });
        if (!pks.length) return;

        fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrf(),
          },
          body: JSON.stringify({ order: pks }),
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.success) {
            // Sync the hidden `order` number inputs so a form Save keeps this order
            tbody.querySelectorAll('.drag-handle[data-pk]').forEach(function (el, i) {
              var input = el.closest('tr').querySelector('input[name$="-order"]');
              if (input) input.value = i;
            });
            flashSaved(tbody.closest('table'));
          } else {
            alert('Could not save order: ' + (data.error || 'unknown error'));
          }
        })
        .catch(function () {
          alert('Network error saving order. Please reload and try again.');
        });
      },
    });
  }

  // ── Boot: find every <tbody> that contains drag handles and wire it up ──────
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.drag-handle[data-pk][data-reorder-url]').forEach(function (el) {
      var tbody = el.closest('tbody');
      if (tbody && !tbody.dataset.sortableReady) {
        tbody.dataset.sortableReady = '1';
        initSortable(tbody, el.dataset.reorderUrl);
      }
    });
  });

}());

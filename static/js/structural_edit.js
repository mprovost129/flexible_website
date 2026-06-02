/**
 * structural_edit.js
 *
 * Adds the ability to ADD and DELETE sections and items while in edit mode,
 * complementing inline_edit.js (which handles editing existing content).
 *
 * Activated only when <body class="edit-mode"> is present.
 *
 * What it wires up:
 *   - "Add section" button (#add-section-btn) -> opens a type picker, POSTs to
 *     the add_section endpoint, injects the returned HTML.
 *   - A delete button on each .section-wrap -> confirms, POSTs to delete_section,
 *     removes the section from the DOM.
 *   - An "Add item" button per section (for section types that use items).
 *   - A delete button per item, attached to the column that contains that
 *     item's edit-wraps (grouped by data-edit-id).
 *
 * After add_item / delete_item, the server returns the re-rendered section HTML
 * so grids and lists reflow correctly; we swap the section's inner content and
 * re-initialise editing on the new markup.
 */

(function () {
  'use strict';

  // Section types offered in the "Add section" picker. Keep in sync with
  // ADDABLE_SECTION_TYPES in edit_views.py (server validates regardless).
  var SECTION_TYPES = [
    ['hero', 'Hero'],
    ['text_block', 'Text Block'],
    ['image_grid', 'Image Grid'],
    ['feature_list', 'Feature List'],
    ['cta_banner', 'Call to Action Banner'],
    ['testimonials', 'Testimonials'],
    ['gallery', 'Image Gallery'],
    ['contact_form', 'Contact Form'],
    ['video_embed', 'Video Embed'],
    ['pricing_table', 'Pricing Table'],
    ['recent_posts', 'Recent Blog Posts'],
    ['product_grid', 'Product Grid'],
    ['plan_grid', 'Plans / Projects Grid'],
  ];

  function getCsrf() {
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function postJson(url, bodyObj) {
    var opts = {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() },
    };
    if (bodyObj instanceof FormData) {
      opts.body = bodyObj;
    } else if (bodyObj) {
      opts.headers['Content-Type'] = 'application/x-www-form-urlencoded';
      opts.body = Object.keys(bodyObj)
        .map(function (k) { return k + '=' + encodeURIComponent(bodyObj[k]); })
        .join('&');
    }
    return fetch(url, opts).then(function (resp) {
      if (!resp.ok) {
        return resp.json().catch(function () { return {}; }).then(function (d) {
          throw new Error(d.error || ('Request failed (' + resp.status + ')'));
        });
      }
      return resp.json();
    });
  }

  function init() {
    if (!document.body.classList.contains('edit-mode')) return;

    setupAddSection();
    setupDeletePage();
    document.querySelectorAll('.section-wrap').forEach(setupSectionControls);
  }

  // -------------------------------------------------------------------------
  // Delete whole page (button added to the floating edit toolbar)
  // -------------------------------------------------------------------------
  function setupDeletePage() {
    var container = document.getElementById('page-sections');
    if (!container) return;  // not a CMS page

    var pageId   = container.dataset.pageId;
    var pageSlug = container.dataset.pageSlug;
    if (!pageId) return;

    // The home page must not be deletable (server enforces this too).
    if (pageSlug === 'home') return;

    // The staff toolbar is rendered server-side in base.html, so we can attach
    // immediately on DOMContentLoaded.
    var toolbar = document.getElementById('staff-toolbar');
    if (toolbar) addDeletePageButton(toolbar, pageId);
  }

  function addDeletePageButton(toolbar, pageId) {
    if (toolbar.querySelector('.delete-page-btn')) return;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-sm btn-danger ms-2 delete-page-btn';
    btn.innerHTML = '<i class="bi bi-trash"></i> Delete page';
    btn.addEventListener('click', function () {
      if (!confirm('Delete this ENTIRE page and all its sections? This cannot be undone.')) return;
      if (!confirm('Are you absolutely sure? The page will be gone permanently.')) return;
      postJson('/edit/page/' + pageId + '/delete/')
        .then(function (data) {
          window.location.href = data.redirect || '/';
        })
        .catch(function (err) { alert('Could not delete page: ' + err.message); });
    });
    toolbar.appendChild(btn);
  }

  // -------------------------------------------------------------------------
  // Add section
  // -------------------------------------------------------------------------
  function setupAddSection() {
    var btn = document.getElementById('add-section-btn');
    var bar = document.getElementById('add-section-bar');
    if (!btn || !bar) return;

    btn.addEventListener('click', function () {
      // Toggle a simple picker of section-type buttons
      var existing = document.getElementById('section-type-picker');
      if (existing) { existing.remove(); return; }

      var picker = document.createElement('div');
      picker.id = 'section-type-picker';
      picker.className = 'section-type-picker';

      SECTION_TYPES.forEach(function (pair) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'btn btn-outline-primary btn-sm m-1';
        b.textContent = pair[1];
        b.addEventListener('click', function () {
          picker.remove();
          doAddSection(bar.dataset.addUrl, pair[0]);
        });
        picker.appendChild(b);
      });

      bar.appendChild(picker);
    });
  }

  function doAddSection(url, sectionType) {
    postJson(url, { section_type: sectionType })
      .then(function (data) {
        var container = document.getElementById('page-sections');
        var wrap = document.createElement('div');
        wrap.className = 'section-wrap';
        wrap.dataset.sectionId = data.id;
        wrap.innerHTML = data.html;
        container.appendChild(wrap);

        setupSectionControls(wrap);
        reinitEditing();
        wrap.scrollIntoView({ behavior: 'smooth', block: 'center' });
      })
      .catch(function (err) {
        alert('Could not add section: ' + err.message);
      });
  }

  // -------------------------------------------------------------------------
  // Per-section controls: delete section, add item, delete items
  // -------------------------------------------------------------------------
  // Section types that support a column-count control (grid-like layouts).
  var COLUMN_SECTION_TYPES = [
    'image_grid', 'feature_list', 'testimonials', 'gallery', 'pricing_table',
    'video_embed',
  ];

  // Available layouts per section are emitted by the server in
  // data-section-layouts (auto-detected from the template folder), so there is
  // no hardcoded layout list to keep in sync here.

  var ALLOWED_COLUMNS = [1, 2, 3, 4, 6];

  function setupSectionControls(wrap) {
    var sectionId = wrap.dataset.sectionId;
    if (!sectionId) return;

    // Avoid double-wiring if called again after a re-render
    if (wrap.querySelector(':scope > .section-toolbar')) {
      attachItemControls(wrap, sectionId);
      return;
    }

    var toolbar = document.createElement('div');
    toolbar.className = 'section-toolbar';

    // Add item. Hero/CTA sections can hold different element kinds, so they get
    // a button per kind; other item sections get a single "Add item".
    var sType = wrap.dataset.sectionType;
    function makeAddBtn(label, kind) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'btn btn-sm btn-success section-add-item-btn';
      b.innerHTML = '<i class="bi bi-plus-lg"></i> ' + label;
      b.title = 'Add ' + label.toLowerCase();
      b.addEventListener('click', function () {
        postJson('/edit/section/' + sectionId + '/item/add/', kind ? { item_type: kind } : null)
          .then(function (data) { swapSectionHtml(wrap, sectionId, data.html); })
          .catch(function (err) { alert('Could not add item: ' + err.message); });
      });
      return b;
    }

    // Settings (gear): opens the config popover
    var gearBtn = document.createElement('button');
    gearBtn.type = 'button';
    gearBtn.className = 'btn btn-sm btn-light section-config-btn';
    gearBtn.innerHTML = '<i class="bi bi-gear"></i>';
    gearBtn.title = 'Section settings';
    gearBtn.addEventListener('click', function () {
      toggleConfigPanel(wrap, sectionId);
    });

    // Visibility toggle (show/hide)
    var visBtn = document.createElement('button');
    visBtn.type = 'button';
    visBtn.className = 'btn btn-sm btn-light section-visibility-btn';
    setVisIcon(visBtn, wrap.dataset.sectionVisible !== '0');
    visBtn.title = 'Show / hide this section';
    visBtn.addEventListener('click', function () {
      postJson('/edit/section/' + sectionId + '/visibility/')
        .then(function (data) {
          wrap.classList.toggle('section-hidden', !data.is_visible);
          wrap.dataset.sectionVisible = data.is_visible ? '1' : '0';
          setVisIcon(visBtn, data.is_visible);
        })
        .catch(function (err) { alert('Could not toggle visibility: ' + err.message); });
    });

    // Delete section
    var delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'btn btn-sm btn-danger section-delete-btn';
    delBtn.innerHTML = '<i class="bi bi-trash"></i>';
    delBtn.title = 'Delete this section';
    delBtn.addEventListener('click', function () {
      if (!confirm('Delete this section? You can undo this right after.')) return;
      postJson('/edit/section/' + sectionId + '/delete/')
        .then(function (data) {
          // Remember enough to restore it (and its items) on undo.
          var undo = data.undo || {};
          var itemIds = (undo.item_ids || []).join(',');

          wrap.style.transition = 'opacity .2s';
          wrap.style.opacity = '0';
          var nextSibling = wrap.nextElementSibling;
          var parent = wrap.parentNode;
          setTimeout(function () { wrap.remove(); }, 200);

          showUndoToast('Section deleted.', function () {
            // Restore: re-create the section wrapper from returned HTML.
            postJson('/edit/section/' + sectionId + '/undo/', { item_ids: itemIds })
              .then(function (r) {
                var newWrap = document.createElement('div');
                newWrap.className = 'section-wrap';
                newWrap.dataset.sectionId = r.id;
                newWrap.innerHTML = r.html;
                // Put it back where it was if possible, else at the end.
                if (nextSibling && nextSibling.parentNode === parent) {
                  parent.insertBefore(newWrap, nextSibling);
                } else {
                  parent.appendChild(newWrap);
                }
                setupSectionControls(newWrap);
                reinitEditing();
              })
              .catch(function (err) { alert('Could not undo: ' + err.message); });
          });
        })
        .catch(function (err) { alert('Could not delete section: ' + err.message); });
    });

    // "Add item" only applies to sections that render items.
    if (sType === 'hero' || sType === 'cta_banner') {
      toolbar.appendChild(makeAddBtn('Button', 'button'));
      toolbar.appendChild(makeAddBtn('Text', 'text'));
      toolbar.appendChild(makeAddBtn('Heading', 'heading'));
    } else if (['text_block', 'video_embed'].indexOf(sType) === -1) {
      toolbar.appendChild(makeAddBtn('Add item', ''));
    }
    toolbar.appendChild(gearBtn);
    toolbar.appendChild(visBtn);
    toolbar.appendChild(delBtn);
    wrap.insertBefore(toolbar, wrap.firstChild);

    attachItemControls(wrap, sectionId);
  }

  function setVisIcon(btn, isVisible) {
    btn.innerHTML = isVisible
      ? '<i class="bi bi-eye"></i>'
      : '<i class="bi bi-eye-slash"></i>';
  }

  // -------------------------------------------------------------------------
  // Section config panel (gear): layout, columns, background color
  // -------------------------------------------------------------------------
  function toggleConfigPanel(wrap, sectionId) {
    var existing = wrap.querySelector(':scope > .section-config-panel');
    if (existing) { existing.remove(); return; }

    var type    = wrap.dataset.sectionType || '';
    var layout  = wrap.dataset.sectionLayout || 'layout_1';
    var columns = wrap.dataset.sectionColumns || '';
    var bg      = wrap.dataset.sectionBg || '';
    var layouts = (wrap.dataset.sectionLayouts || 'layout_1')
                    .split(',')
                    .map(function (s) { return s.trim(); })
                    .filter(Boolean);

    var panel = document.createElement('div');
    panel.className = 'section-config-panel';

    var html = '<div class="scp-row"><strong>Section settings</strong></div>';

    // Layout switcher (only if more than one layout exists for this type)
    if (layouts.length > 1) {
      html += '<div class="scp-row"><label>Layout</label><select class="form-select form-select-sm scp-layout">';
      layouts.forEach(function (l) {
        var sel = l === layout ? ' selected' : '';
        var label = 'Layout ' + l.replace('layout_', '');
        html += '<option value="' + l + '"' + sel + '>' + label + '</option>';
      });
      html += '</select></div>';
    }

    // Columns (only for grid-like sections)
    if (COLUMN_SECTION_TYPES.indexOf(type) !== -1) {
      html += '<div class="scp-row"><label>Columns</label><select class="form-select form-select-sm scp-columns">';
      ALLOWED_COLUMNS.forEach(function (n) {
        var sel = String(n) === String(columns) ? ' selected' : '';
        html += '<option value="' + n + '"' + sel + '>' + n + ' across</option>';
      });
      html += '</select></div>';
    }

    // Background color
    html += '<div class="scp-row"><label>Background</label>' +
            '<input type="text" class="form-control form-control-sm scp-bg" ' +
            'placeholder="#f8f9fa or blank" value="' + escAttr(bg) + '"></div>';

    html += '<div class="scp-row scp-actions">' +
            '<button type="button" class="btn btn-sm btn-primary scp-save">Apply</button>' +
            '<button type="button" class="btn btn-sm btn-outline-secondary scp-close">Close</button>' +
            '<span class="scp-feedback small ms-2"></span>' +
            '</div>';

    panel.innerHTML = html;
    wrap.insertBefore(panel, wrap.firstChild);

    panel.querySelector('.scp-close').addEventListener('click', function () {
      panel.remove();
    });

    // Layout change applies immediately (re-renders the section)
    var layoutSel = panel.querySelector('.scp-layout');
    if (layoutSel) {
      layoutSel.addEventListener('change', function () {
        postJson('/edit/section/' + sectionId + '/layout/', { layout: layoutSel.value })
          .then(function (data) {
            wrap.dataset.sectionLayout = data.layout;
            swapSectionHtml(wrap, sectionId, data.html);
          })
          .catch(function (err) { alert('Could not change layout: ' + err.message); });
      });
    }

    panel.querySelector('.scp-save').addEventListener('click', function () {
      var body = {};
      var colSel = panel.querySelector('.scp-columns');
      if (colSel) body.columns_desktop = colSel.value;
      var bgInput = panel.querySelector('.scp-bg');
      if (bgInput) body.background_color = bgInput.value.trim();

      var fb = panel.querySelector('.scp-feedback');
      fb.textContent = 'Saving…';
      fb.className = 'scp-feedback small ms-2';

      postJson('/edit/section/' + sectionId + '/config/', body)
        .then(function (data) {
          wrap.dataset.sectionColumns = body.columns_desktop || wrap.dataset.sectionColumns;
          wrap.dataset.sectionBg = body.background_color || '';
          swapSectionHtml(wrap, sectionId, data.html);
          // swapSectionHtml wipes the panel; nothing more to do
        })
        .catch(function (err) {
          fb.textContent = err.message;
          fb.className = 'scp-feedback small ms-2 text-danger';
        });
    });
  }

  function escAttr(s) {
    return String(s).replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Group an item's edit-wraps by data-edit-id, find their shared column,
  // and attach a delete button to it.
  function attachItemControls(wrap, sectionId) {
    var itemWraps = wrap.querySelectorAll('.edit-wrap[data-edit-model="item"]');
    var seen = {};

    itemWraps.forEach(function (ew) {
      var itemId = ew.dataset.editId;
      if (!itemId || seen[itemId]) return;
      seen[itemId] = true;

      // The "item container" is the nearest ancestor that holds all of this
      // item's edit-wraps. Walk up until the parent contains edit-wraps for a
      // different item (or until we hit the section). The immediate column div
      // is the common case.
      var container = findItemContainer(ew, itemId, wrap);
      if (!container || container.querySelector(':scope > .item-delete-btn')) return;

      container.classList.add('item-editable');

      var del = document.createElement('button');
      del.type = 'button';
      del.className = 'btn btn-sm btn-danger item-delete-btn';
      del.innerHTML = '<i class="bi bi-x-lg"></i>';
      del.title = 'Delete this item';
      del.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        // No confirm dialog for items: undo makes it low-risk and faster to work.
        postJson('/edit/item/' + itemId + '/delete/')
          .then(function (data) {
            swapSectionHtml(wrap, sectionId, data.html);
            showUndoToast('Item deleted.', function () {
              postJson('/edit/item/' + itemId + '/undo/')
                .then(function (r) { swapSectionHtml(wrap, sectionId, r.html); })
                .catch(function (err) { alert('Could not undo: ' + err.message); });
            });
          })
          .catch(function (err) { alert('Could not delete item: ' + err.message); });
      });
      container.appendChild(del);
    });
  }

  // Find the element that wraps all edit-wraps belonging to itemId.
  // Strategy: start at the edit-wrap's parent; if every item edit-wrap inside
  // it shares the same id, that's our container. Otherwise climb once more.
  function findItemContainer(editWrap, itemId, sectionWrap) {
    var node = editWrap.parentElement;
    while (node && node !== sectionWrap) {
      var inside = node.querySelectorAll('.edit-wrap[data-edit-model="item"]');
      var ids = {};
      inside.forEach(function (w) { ids[w.dataset.editId] = true; });
      var keys = Object.keys(ids);
      if (keys.length === 1 && keys[0] === itemId) {
        return node;
      }
      node = node.parentElement;
    }
    // Fallback: the immediate parent
    return editWrap.parentElement;
  }

  // Replace a section's inner HTML after the server re-renders it (add/delete
  // item), then re-wire both structural and inline editing on the new markup.
  function swapSectionHtml(wrap, sectionId, html) {
    // Preserve the toolbar; replace only the rendered section content.
    var toolbar = wrap.querySelector(':scope > .section-toolbar');
    wrap.innerHTML = html;
    if (toolbar) wrap.insertBefore(toolbar, wrap.firstChild);

    attachItemControls(wrap, sectionId);
    reinitEditing();
  }

  // -------------------------------------------------------------------------
  // Re-initialise inline_edit.js on freshly injected markup.
  // inline_edit.js exposes window.reinitInlineEdit if available; otherwise we
  // fall back to dispatching a custom event it can listen for.
  // -------------------------------------------------------------------------
  function reinitEditing() {
    if (typeof window.reinitInlineEdit === 'function') {
      window.reinitInlineEdit();
    }
  }

  // -------------------------------------------------------------------------
  // Undo toast: a transient bar with an Undo button. Auto-dismisses after a
  // few seconds. Only one toast at a time.
  // -------------------------------------------------------------------------
  var activeToastTimer = null;

  function showUndoToast(message, onUndo) {
    // Remove any existing toast first
    var existing = document.getElementById('undo-toast');
    if (existing) existing.remove();
    if (activeToastTimer) clearTimeout(activeToastTimer);

    var toast = document.createElement('div');
    toast.id = 'undo-toast';
    toast.className = 'undo-toast';
    toast.innerHTML =
      '<span class="undo-toast-msg"></span>' +
      '<button type="button" class="btn btn-sm btn-light undo-toast-btn">Undo</button>' +
      '<button type="button" class="btn-close btn-close-white undo-toast-close" aria-label="Dismiss"></button>';
    toast.querySelector('.undo-toast-msg').textContent = message;

    document.body.appendChild(toast);

    function dismiss() {
      if (activeToastTimer) clearTimeout(activeToastTimer);
      toast.classList.add('undo-toast-out');
      setTimeout(function () { if (toast.parentNode) toast.remove(); }, 200);
    }

    toast.querySelector('.undo-toast-btn').addEventListener('click', function () {
      dismiss();
      if (typeof onUndo === 'function') onUndo();
    });
    toast.querySelector('.undo-toast-close').addEventListener('click', dismiss);

    // Auto-dismiss after 7 seconds (long enough to react, short enough to not linger)
    activeToastTimer = setTimeout(dismiss, 7000);
  }

  document.addEventListener('DOMContentLoaded', init);
}());

/**
 * nav_edit.js  (Stage 2 of navigation editing)
 *
 * Two features, both staff-only (body.edit-mode):
 *
 * 1. Page-status panel: a floating card showing whether the current page is
 *    published and whether it's in the navbar/footer, with action buttons:
 *    "Publish & add to navbar" (the headline shortcut), plus granular
 *    publish/unpublish, add/remove navbar, add to footer.
 *
 * 2. Live nav editing: hovering a nav link shows edit (rename) and delete
 *    controls; an "Add link" button appends a custom link. Reorder via the
 *    existing drag patterns is left to a later pass; this covers add/rename/
 *    delete which is the core of "same as sections".
 *
 * Relies on showUndoToast from structural_edit.js if present (loaded first).
 */
(function () {
  'use strict';

  function getCsrf() {
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function postJson(url, bodyObj) {
    var opts = { method: 'POST', headers: { 'X-CSRFToken': getCsrf() } };
    if (bodyObj) {
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

  function toast(msg, onUndo) {
    if (typeof window.showUndoToast === 'function') {
      window.showUndoToast(msg, onUndo);
    }
  }

  // -------------------------------------------------------------------------
  // Focus hint: when a new item is added we want the page reload to land with
  // that item already in rename mode. sessionStorage survives the reload but
  // not a navigation away from the site.
  // -------------------------------------------------------------------------
  var FOCUS_HINT_KEY = 'cbl:focus-hint';

  function setFocusHint(hint) {
    try {
      sessionStorage.setItem(FOCUS_HINT_KEY, JSON.stringify(hint));
    } catch (e) {
      /* sessionStorage disabled; the user just won't get auto-focus */
    }
  }
  window.cblSetFocusHint = setFocusHint;

  function consumeFocusHint() {
    var raw = null;
    try { raw = sessionStorage.getItem(FOCUS_HINT_KEY); } catch (e) { return; }
    if (!raw) return;
    try { sessionStorage.removeItem(FOCUS_HINT_KEY); } catch (e) {}
    var hint;
    try { hint = JSON.parse(raw); } catch (e) { return; }
    if (!hint || !hint.kind || !hint.id) return;

    // Defer so the DOM (and our own wiring) is in place
    setTimeout(function () {
      if (hint.kind === 'nav-link') {
        var li = document.querySelector('.nav-editable[data-navlink-id="' + hint.id + '"]');
        if (li) startInlineRename(li, 'nav-link', hint.id);
      } else if (hint.kind === 'nav-child') {
        var child = document.querySelector('.nav-editable-child[data-navlink-id="' + hint.id + '"]');
        if (child) startInlineRename(child, 'nav-child', hint.id);
      } else if (hint.kind === 'footer-column') {
        var col = document.querySelector('.footer-col-editable[data-footercol-id="' + hint.id + '"]');
        if (col) startInlineRename(col, 'footer-column', hint.id);
      } else if (hint.kind === 'footer-link') {
        var fl = document.querySelector('.footer-link-editable[data-footerlink-id="' + hint.id + '"]');
        if (fl) startInlineRename(fl, 'footer-link', hint.id);
      }
    }, 50);
  }

  // -------------------------------------------------------------------------
  // Inline rename: replace the text node inside an existing element with an
  // input, save on Enter/blur, cancel on Escape. Works for nav links, nav
  // dropdown children, footer column headings, and footer links.
  // -------------------------------------------------------------------------
  function startInlineRename(el, kind, id) {
    if (!el || el.dataset.renaming === '1') return;
    el.dataset.renaming = '1';

    // Find the text-bearing element for each kind
    var target;
    if (kind === 'nav-link') {
      target = el.querySelector(':scope > a');
    } else if (kind === 'nav-child') {
      target = el.querySelector('a.dropdown-item');
    } else if (kind === 'footer-column') {
      target = el.querySelector('h5, h4, h6');
    } else if (kind === 'footer-link') {
      target = el.querySelector('a');
    }
    if (!target) { el.dataset.renaming = '0'; return; }

    var originalLabel = (target.textContent || '').trim();
    // Stash everything inside so we can restore on cancel or update on save
    var originalHTML = target.innerHTML;

    // Build the input
    var input = document.createElement('input');
    input.type = 'text';
    input.value = originalLabel;
    input.className = 'cbl-inline-rename';
    input.setAttribute('aria-label', 'Rename');

    // Replace text content with the input. For anchors, keep child nodes that
    // aren't text (e.g. <i> icons) - but most of our targets are text-only.
    target.textContent = '';
    target.appendChild(input);
    // Click on the parent shouldn't navigate while renaming
    var clickGuard = function (ev) { ev.preventDefault(); };
    target.addEventListener('click', clickGuard);

    input.focus();
    input.select();

    function cleanup(restoreHtml) {
      el.dataset.renaming = '0';
      target.removeEventListener('click', clickGuard);
      if (restoreHtml) target.innerHTML = originalHTML;
    }

    function save() {
      var next = (input.value || '').trim();
      if (!next || next === originalLabel) {
        cleanup(true);
        return;
      }
      var url, isChild = false;
      if (kind === 'nav-link') {
        url = '/edit/nav-link/' + id + '/update/';
      } else if (kind === 'nav-child') {
        url = '/edit/nav-link/' + id + '/update/';
        isChild = true;
      } else if (kind === 'footer-column') {
        url = '/edit/footer-column/' + id + '/update/';
      } else if (kind === 'footer-link') {
        url = '/edit/footer-link/' + id + '/update/';
      }
      postJson(url, { field: kind === 'footer-column' ? 'heading' : 'label', value: next })
        .then(function () {
          cleanup(false);
          target.textContent = next;
          // Sync data attributes + other DOM instances (e.g. mobile clones)
          if (kind === 'nav-link') {
            updateNavLabelsEverywhere(id, next, false);
          } else if (kind === 'nav-child') {
            updateNavLabelsEverywhere(id, next, true);
          } else if (kind === 'footer-link') {
            el.dataset.footerlinkLabel = next;
          }
        })
        .catch(function (err) {
          alert(err.message);
          cleanup(true);
        });
    }

    function cancel() {
      cleanup(true);
    }

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); save(); }
      else if (e.key === 'Escape') { e.preventDefault(); cancel(); }
    });
    input.addEventListener('blur', function () {
      // Save on blur (matches users' expectation; cancel must be explicit via Esc)
      save();
    });
  }

  function trackNavbarHeight() {
    var region = document.getElementById('navbar-region');
    var sidebar = document.getElementById('edit-sidebar');
    if (!region || !sidebar) return;
    function update() {
      // Use ceil so we always round up; add 12px buffer for shadow + breathing room
      var h = Math.ceil(region.getBoundingClientRect().height) + 12;
      sidebar.style.top = h + 'px';
      sidebar.style.maxHeight = 'calc(100vh - ' + h + 'px - 1rem)';
    }
    update();
    // Re-measure after full load (fonts/images can affect navbar height)
    window.addEventListener('load', update, { once: true });
    if (window.ResizeObserver) {
      new ResizeObserver(update).observe(region);
    }
  }

  function init() {
    if (!document.body.classList.contains('edit-mode')) return;
    trackNavbarHeight();
    wireChromeHoverAdd();
    wireHoverAddButtons();
    setupPageStatusPanel();
    setupNavEditing();
    setupBrandEditing();
    setupNavBlockDragReorder();
    setupNavDragReorder();
    setupFooterEditing();
    consumeFocusHint();
  }

  // -------------------------------------------------------------------------
  // Chrome-hover-add: the Settings / Hide / Delete-all controls that sit
  // next to the "Add item" dropdown on the navbar and footer regions.
  // -------------------------------------------------------------------------
  function wireChromeHoverAdd() {
    // Hide / show toggle
    document.querySelectorAll('[data-chrome-toggle]').forEach(function (btn) {
      if (btn.dataset.wired === '1') return;
      btn.dataset.wired = '1';
      btn.addEventListener('click', function () {
        var field = btn.dataset.chromeToggle;
        var current = btn.dataset.chromeCurrent === '1';
        postJson('/edit/site-chrome/update/', { field: field, value: current ? '0' : '1' })
          .then(function () { window.location.reload(); })
          .catch(function (err) { alert(err.message); });
      });
    });

    // Delete-all (clear)
    document.querySelectorAll('[data-chrome-clear]').forEach(function (btn) {
      if (btn.dataset.wired === '1') return;
      btn.dataset.wired = '1';
      btn.addEventListener('click', function () {
        var kind = btn.dataset.chromeClear;
        if (!confirm('Delete ALL ' + kind + ' items? This cannot be undone from here.')) return;
        var url = (kind === 'navbar') ? '/edit/navbar/clear/' : '/edit/footer/clear/';
        postJson(url)
          .then(function () { window.location.reload(); })
          .catch(function (err) { alert(err.message); });
      });
    });

    // Footer: Add column (single-action, no dropdown)
    document.querySelectorAll('[data-chrome-add-footer-column]').forEach(function (btn) {
      if (btn.dataset.wired === '1') return;
      btn.dataset.wired = '1';
      btn.addEventListener('click', function () {
        postJson('/edit/footer-column/add/', { heading: 'New Column' })
          .then(function (resp) {
            // Stash the new column id so inline rename auto-focuses after reload
            if (resp && resp.id) {
              setFocusHint({ kind: 'footer-column', id: resp.id });
            }
            window.location.reload();
          })
          .catch(function (err) { alert(err.message); });
      });
    });
  }

  function wireHoverAddButtons() {
    document.querySelectorAll('.chrome-hover-add-menu [data-nav-add-action]').forEach(function (actionBtn) {
      if (actionBtn.dataset.wired === '1') return;
      actionBtn.dataset.wired = '1';
      actionBtn.addEventListener('click', function () {
        var action = actionBtn.dataset.navAddAction;
        if (action === 'link') {
          if (typeof window.cblShowNewNavLinkPanel === 'function') {
            window.cblShowNewNavLinkPanel(false);
          } else {
            addNavLinkFlow(false);
          }
          return;
        }
        if (action === 'button') {
          if (typeof window.cblShowNewNavLinkPanel === 'function') {
            window.cblShowNewNavLinkPanel(true);
          } else {
            addNavLinkFlow(true);
          }
          return;
        }
        if (action === 'dropdown') {
          addDropdownFlow();
          return;
        }
        if (action === 'search') {
          addSearchFlow();
          return;
        }
        if (action === 'auth') {
          addAuthFlow();
          return;
        }
        if (action === 'cta') {
          addCtaFlow();
        }
      });
    });
  }

  function setChromeField(field, value) {
    return postJson('/edit/site-chrome/update/', { field: field, value: value });
  }

  function createNavLink(opts) {
    return postJson('/edit/nav-link/add/', {
      label: opts.label,
      url: opts.url,
      slot: opts.slot || 'left',
      is_button: opts.isButton ? '1' : '0',
      parent_id: opts.parentId || ''
    });
  }

  function addNavLinkFlow(isButton) {
    var label = isButton ? 'Get Started' : 'New Link';
    var url = '/';
    var slot = 'left';
    createNavLink({
      label: label,
      url: url,
      slot: slot,
      isButton: !!isButton
    })
      .then(function (resp) {
        // Auto-focus the newly-created link's inline rename input after reload
        if (resp && resp.id) {
          setFocusHint({ kind: 'nav-link', id: resp.id });
        }
        window.location.reload();
      })
      .catch(function (err) { alert(err.message); });
  }

  function addDropdownFlow() {
    var parentLabel = 'Menu';
    var childLabel = 'New item';
    var childUrl = '/';
    var slot = 'left';

    createNavLink({
      label: parentLabel,
      url: '#',
      slot: slot,
      isButton: false
    })
      .then(function (parentResp) {
        return createNavLink({
          label: childLabel,
          url: childUrl,
          slot: slot,
          isButton: false,
          parentId: parentResp.id
        }).then(function (childResp) {
          // Focus the parent so the user names the menu first
          if (parentResp && parentResp.id) {
            setFocusHint({ kind: 'nav-link', id: parentResp.id });
          }
          return childResp;
        });
      })
      .then(function () {
        window.location.reload();
      })
      .catch(function (err) { alert(err.message); });
  }

  function addSearchFlow() {
    var slot = 'right';
    setChromeField('show_nav_search', '1')
      .then(function () { return setChromeField('nav_search_slot', slot); })
      .then(function () { window.location.reload(); })
      .catch(function (err) { alert(err.message); });
  }

  function addAuthFlow() {
    var slot = 'right';
    setChromeField('show_nav_login', '1')
      .then(function () { return setChromeField('show_nav_register', '1'); })
      .then(function () { return setChromeField('show_nav_profile', '1'); })
      .then(function () { return setChromeField('nav_auth_slot', slot); })
      .then(function () { window.location.reload(); })
      .catch(function (err) { alert(err.message); });
  }

  function addCtaFlow() {
    var label = 'Get Started';
    var url = '/';
    var slot = 'right';
    setChromeField('nav_cta_label', label)
      .then(function () { return setChromeField('nav_cta_url', url); })
      .then(function () { return setChromeField('nav_cta_slot', slot); })
      .then(function () { window.location.reload(); })
      .catch(function (err) { alert(err.message); });
  }

  // -------------------------------------------------------------------------
  // 1. Page-status panel
  // -------------------------------------------------------------------------
  function setupPageStatusPanel() {
    var ps = document.getElementById('page-sections');
    if (!ps) return;

    if (document.getElementById('edit-sidebar-body')) return;

    var pageId = ps.dataset.pageId;
    var slug = ps.dataset.pageSlug;
    var state = {
      published: ps.dataset.pagePublished === '1',
      inNavbar: ps.dataset.pageInNavbar === '1',
      inFooter: ps.dataset.pageInFooter === '1',
      isHome: slug === 'home',
    };

    var panel = document.createElement('div');
    panel.id = 'page-status-panel';
    document.body.appendChild(panel);

    function render() {
      var rows = [];
      rows.push('<div class="psp-header"><i class="bi bi-file-earmark-text me-1"></i> Page status</div>');

      // Status badges
      rows.push('<div class="psp-badges">' +
        badge(state.published ? 'Published' : 'Draft', state.published ? 'success' : 'secondary') +
        badge(state.inNavbar ? 'In navbar' : 'Not in navbar', state.inNavbar ? 'primary' : 'light') +
        badge(state.inFooter ? 'In footer' : 'Not in footer', state.inFooter ? 'primary' : 'light') +
        '</div>');

      // Headline shortcut (only when it would change something)
      if (!state.published || !state.inNavbar) {
        rows.push('<button type="button" class="btn btn-success btn-sm w-100 mb-2 psp-publish-nav">' +
          '<i class="bi bi-rocket-takeoff me-1"></i> Publish &amp; add to navbar</button>');
      }

      // Granular actions
      rows.push('<div class="psp-actions">');
      if (state.published) {
        if (!state.isHome) {
          rows.push('<button type="button" class="btn btn-outline-secondary btn-sm psp-unpublish">Unpublish</button>');
        }
      } else {
        rows.push('<button type="button" class="btn btn-outline-success btn-sm psp-publish">Publish</button>');
      }
      if (state.inNavbar) {
        rows.push('<button type="button" class="btn btn-outline-danger btn-sm psp-remove-nav">Remove from navbar</button>');
      } else {
        rows.push('<button type="button" class="btn btn-outline-primary btn-sm psp-add-nav">Add to navbar</button>');
      }
      if (!state.inFooter) {
        rows.push('<button type="button" class="btn btn-outline-primary btn-sm psp-add-footer">Add to footer</button>');
      }
      rows.push('</div>');

      panel.innerHTML = rows.join('');
      wire();
    }

    function badge(text, variant) {
      return '<span class="badge text-bg-' + variant + ' me-1">' + text + '</span>';
    }

    function wire() {
      var map = [
        ['.psp-publish-nav', '/edit/page/' + pageId + '/publish-and-nav/', function (d) {
          state.published = true; state.inNavbar = true;
          toast('Published and added to navbar.');
        }],
        ['.psp-publish', '/edit/page/' + pageId + '/publish/', function (d) {
          state.published = true; toast('Page published.');
        }],
        ['.psp-unpublish', '/edit/page/' + pageId + '/unpublish/', function (d) {
          state.published = false; toast('Page set to draft.');
        }],
        ['.psp-add-nav', '/edit/page/' + pageId + '/add-to-navbar/', function (d) {
          state.inNavbar = true; toast('Added to navbar. Reload to see it.');
        }],
        ['.psp-remove-nav', '/edit/page/' + pageId + '/remove-from-navbar/', function (d) {
          state.inNavbar = false; toast('Removed from navbar. Reload to update.');
        }],
        ['.psp-add-footer', '/edit/page/' + pageId + '/add-to-footer/', function (d) {
          state.inFooter = true; toast('Added to footer. Reload to see it.');
        }],
      ];
      map.forEach(function (entry) {
        var btn = panel.querySelector(entry[0]);
        if (!btn) return;
        btn.addEventListener('click', function () {
          btn.disabled = true;
          postJson(entry[1])
            .then(function (d) { entry[2](d); render(); })
            .catch(function (err) { alert(err.message); btn.disabled = false; });
        });
      });
    }

    render();
  }

  // -------------------------------------------------------------------------
  // 2. Live nav editing
  // -------------------------------------------------------------------------
  function setupNavEditing() {
    document.querySelectorAll('.nav-editable').forEach(wireNavItem);
    document.querySelectorAll('.nav-editable-child').forEach(wireNavChildItem);
    // The "Add ..." UI is the chrome-hover-add dropdown in base.html.
    // There is no longer a separate "+" button appended to the nav <ul>;
    // it duplicated the dropdown and confused the UX.
  }

  function navInstances(id, child) {
    var cls = child ? '.nav-editable-child' : '.nav-editable';
    return Array.prototype.slice.call(
      document.querySelectorAll(cls + '[data-navlink-id="' + id + '"]')
    );
  }

  function updateNavLabelsEverywhere(id, nextLabel, child) {
    navInstances(id, child).forEach(function (el) {
      el.dataset.navlinkLabel = nextLabel;
      var a = child ? el.querySelector('a.dropdown-item') : el.querySelector(':scope > a');
      if (!a) return;
      if (child) {
        a.textContent = nextLabel;
      } else {
        a.childNodes.forEach(function (n) {
          if (n.nodeType === 3) n.textContent = '';
        });
        a.appendChild(document.createTextNode(nextLabel));
      }
    });
  }

  function hideNavEverywhere(id, child) {
    navInstances(id, child).forEach(function (el) { el.style.display = 'none'; });
  }

  function showNavEverywhere(id, child) {
    navInstances(id, child).forEach(function (el) { el.style.display = ''; });
  }

  function wireNavItem(li) {
    if (li.dataset.navWired === '1') return;
    li.dataset.navWired = '1';

    var id = li.dataset.navlinkId;
    if (!id) return;

    // Defensive cleanup: if this script was previously loaded or partial DOM was
    // re-rendered with existing controls, keep only one control cluster per item.
    li.querySelectorAll(':scope > .nav-edit-controls').forEach(function (existing) {
      existing.remove();
    });

    var controls = document.createElement('span');
    controls.className = 'nav-edit-controls';

    var editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'nav-edit-btn';
    editBtn.title = 'Rename link';
    editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
    editBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      startInlineRename(li, 'nav-link', id);
    });

    var delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'nav-edit-btn nav-edit-del';
    delBtn.title = 'Delete link';
    delBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
    delBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      postJson('/edit/nav-link/' + id + '/delete/')
        .then(function (d) {
          hideNavEverywhere(id, false);
          (d.child_ids || []).forEach(function (childId) {
            hideNavEverywhere(childId, true);
          });
          toast('Nav item removed.', function () {
            postJson('/edit/nav-link/' + id + '/undo/')
              .then(function () {
                showNavEverywhere(id, false);
                (d.child_ids || []).forEach(function (childId) {
                  showNavEverywhere(childId, true);
                });
              })
              .catch(function (err) { alert(err.message); });
          });
        })
        .catch(function (err) { alert(err.message); });
    });

    controls.appendChild(editBtn);
    if (li.classList.contains('dropdown')) {
      var addChildBtn = document.createElement('button');
      addChildBtn.type = 'button';
      addChildBtn.className = 'nav-edit-btn nav-edit-add-child';
      addChildBtn.title = 'Add dropdown item';
      addChildBtn.innerHTML = '<i class="bi bi-plus-lg"></i>';
      addChildBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        if (addChildBtn.dataset.busy === '1') return;
        addChildBtn.dataset.busy = '1';
        addChildBtn.disabled = true;
        postJson('/edit/nav-link/add/', {
          label: 'New item',
          url: '/',
          parent_id: id,
          slot: li.dataset.navlinkSlot || 'left'
        })
          .then(function (resp) {
            if (resp && resp.id) {
              setFocusHint({ kind: 'nav-child', id: resp.id });
            }
            window.location.reload();
          })
          .catch(function (err) {
            addChildBtn.dataset.busy = '0';
            addChildBtn.disabled = false;
            alert(err.message);
          });
      });
      controls.appendChild(addChildBtn);
    }
    controls.appendChild(delBtn);
    li.appendChild(controls);
  }

  function wireNavChildItem(li) {
    if (li.dataset.navWired === '1') return;
    li.dataset.navWired = '1';

    var id = li.dataset.navlinkId;
    if (!id) return;

    li.querySelectorAll(':scope > .nav-edit-controls-child').forEach(function (existing) {
      existing.remove();
    });

    var controls = document.createElement('span');
    controls.className = 'nav-edit-controls nav-edit-controls-child';

    var editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'nav-edit-btn';
    editBtn.title = 'Rename dropdown item';
    editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
    editBtn.addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      startInlineRename(li, 'nav-child', id);
    });

    var delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'nav-edit-btn nav-edit-del';
    delBtn.title = 'Delete dropdown item';
    delBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
    delBtn.addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      postJson('/edit/nav-link/' + id + '/delete/')
        .then(function () {
          hideNavEverywhere(id, true);
          toast('Dropdown item removed.', function () {
            postJson('/edit/nav-link/' + id + '/undo/')
              .then(function () { showNavEverywhere(id, true); })
              .catch(function (err) { alert(err.message); });
          });
        })
        .catch(function (err) { alert(err.message); });
    });

    controls.appendChild(editBtn);
    controls.appendChild(delBtn);
    li.appendChild(controls);
  }

  function setupBrandEditing() {
    document.querySelectorAll('.brand-editable').forEach(function (el) {
      if (el.dataset.brandWired === '1') return;
      el.dataset.brandWired = '1';

      el.querySelectorAll(':scope > .brand-edit-controls').forEach(function (existing) {
        existing.remove();
      });

      var controls = document.createElement('span');
      controls.className = 'nav-edit-controls brand-edit-controls';

      var editBtn = document.createElement('button');
      editBtn.type = 'button';
      editBtn.className = 'nav-edit-btn';
      editBtn.title = 'Rename brand';
      editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
      editBtn.addEventListener('click', function (e) {
        e.preventDefault(); e.stopPropagation();
        startBrandRename(el);
      });

      var toggleBtn = document.createElement('button');
      toggleBtn.type = 'button';
      toggleBtn.className = 'nav-edit-btn nav-edit-del';
      var showName = (el.dataset.brandShowName || '1') === '1';
      toggleBtn.title = showName ? 'Hide brand text' : 'Show brand text';
      toggleBtn.innerHTML = showName ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-plus-lg"></i>';
      toggleBtn.addEventListener('click', function (e) {
        e.preventDefault(); e.stopPropagation();
        postJson('/edit/site-brand/update/', {
          field: 'show_brand_name',
          value: showName ? '0' : '1'
        })
          .then(function () { window.location.reload(); })
          .catch(function (err) { alert(err.message); });
      });

      controls.appendChild(editBtn);
      controls.appendChild(toggleBtn);
      el.appendChild(controls);
    });
  }

  function setupChromeSlotEditing() {
    var targets = document.querySelectorAll('[data-chrome-slot-field]');
    targets.forEach(function (el) {
      if (el.dataset.chromeSlotWired === '1') return;
      el.dataset.chromeSlotWired = '1';

      // Keep controls anchored to this block.
      el.style.position = 'relative';

      var controls = document.createElement('span');
      controls.className = 'nav-edit-controls chrome-slot-edit-controls';

      function slotOrder() {
        return ['left', 'center', 'right'];
      }

      function neighborSlot(delta) {
        var current = (el.dataset.chromeSlotValue || 'left').toLowerCase();
        var order = slotOrder();
        var index = order.indexOf(current);
        if (index < 0) index = 0;
        var nextIndex = index + delta;
        if (nextIndex < 0 || nextIndex >= order.length) return null;
        return order[nextIndex];
      }

      function makeBtn(delta, icon, title) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'nav-edit-btn nav-edit-slot-btn';
        btn.title = title;
        btn.innerHTML = '<i class="bi ' + icon + '"></i>';
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          var field = el.dataset.chromeSlotField;
          var slot = neighborSlot(delta);
          if (!slot) return;
          setChromeField(field, slot)
            .then(function () {
              moveChromeBlockToSlot(field, slot);
              syncChromeSlotState(field, slot);
            })
            .catch(function (err) { alert(err.message); });
        });
        return btn;
      }

      var btnL = makeBtn(-1, 'bi-arrow-left-short', 'Move left');
      var btnR = makeBtn(1, 'bi-arrow-right-short', 'Move right');
      controls.appendChild(btnL);
      controls.appendChild(btnR);

      btnL.disabled = (neighborSlot(-1) === null);
      btnR.disabled = (neighborSlot(1) === null);

      el.appendChild(controls);
    });
  }

  function setupNavBlockDragReorder() {
    normalizeNavBlocks();
    var zones = document.querySelectorAll('.cbl-navbar-desktop .cbl-navbar-zone');
    zones.forEach(function (zone) {
      initNavBlockZone(zone);
    });
  }

  function normalizeNavBlocks() {
    var zones = document.querySelectorAll('.cbl-navbar-desktop .cbl-navbar-zone');
    zones.forEach(function (zone) {
      var children = Array.prototype.slice.call(zone.children || []);
      children.forEach(function (child) {
        if (!child || !child.getAttribute) return;
        if (child.hasAttribute('data-nav-block-kind')) return;
        if (!child.hasAttribute('data-chrome-slot-field')) return;
        var field = child.getAttribute('data-chrome-slot-field') || '';
        var kind = field === 'nav_search_slot' ? 'search'
          : field === 'nav_auth_slot' ? 'auth'
          : field === 'nav_cta_slot' ? 'cta'
          : '';
        if (!kind) return;
        var wrap = document.createElement('div');
        wrap.className = 'cbl-nav-block cbl-nav-block-' + kind;
        wrap.setAttribute('data-nav-block-kind', kind);
        wrap.setAttribute('data-nav-block-slot', zoneSlot(zone));
        zone.insertBefore(wrap, child);
        wrap.appendChild(child);
      });
    });
  }

  function initNavBlockZone(zone) {
    if (!zone) return;
    Array.prototype.slice.call(zone.children || []).forEach(function (block) {
      if (!block || !block.getAttribute || !block.hasAttribute('data-nav-block-kind')) return;
      if (block.dataset.blockDragWired === '1') return;
      block.dataset.blockDragWired = '1';
      block.setAttribute('draggable', 'false');

      // The links block already has per-link controls. A second block-level
      // control cluster makes the navbar look duplicated and noisy.
      if ((block.dataset.navBlockKind || '').toLowerCase() === 'links') {
        block.querySelectorAll(':scope > .chrome-slot-edit-controls').forEach(function (existing) {
          existing.remove();
        });
        return;
      }

      var controlClusters = Array.prototype.slice.call(block.querySelectorAll(':scope > .chrome-slot-edit-controls'));
      var controls = controlClusters.shift();
      controlClusters.forEach(function (extra) { extra.remove(); });
      if (!controls) {
        controls = document.createElement('span');
        controls.className = 'nav-edit-controls chrome-slot-edit-controls';
        block.appendChild(controls);
      }
      if (controls.dataset.blockControlsWired !== '1') {
        controls.dataset.blockControlsWired = '1';
        var kind = (block.dataset.navBlockKind || '').toLowerCase();

        var editBtn = document.createElement('button');
        editBtn.type = 'button';
        editBtn.className = 'nav-edit-btn';
        editBtn.title = 'Edit block settings';
        editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
        editBtn.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          if (kind === 'brand') {
            var brand = block.querySelector('.brand-editable');
            if (brand) startBrandRename(brand);
            return;
          }
          window.location.href = '/cbl/settings/';
        });
        controls.appendChild(editBtn);

        var delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.className = 'nav-edit-btn nav-edit-del';
        delBtn.title = 'Delete/hide block';
        delBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
        delBtn.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopPropagation();
          hideNavBlock(kind, block);
        });
        controls.appendChild(delBtn);

      }
      var handle = document.createElement('button');
      handle.type = 'button';
      handle.className = 'nav-edit-btn nav-edit-slot-btn nav-block-drag-handle';
      handle.title = 'Drag to reorder';
      handle.innerHTML = '<i class="bi bi-grip-vertical"></i>';
      handle.addEventListener('mousedown', function (e) {
        e.preventDefault();
        e.stopPropagation();
        block.setAttribute('draggable', 'true');
      });
      handle.addEventListener('mouseup', function () {
        block.setAttribute('draggable', 'false');
      });
      controls.appendChild(handle);

      block.addEventListener('dragstart', function (e) {
        block.classList.add('nav-dragging');
        e.dataTransfer.effectAllowed = 'move';
      });
      block.addEventListener('dragend', function () {
        block.classList.remove('nav-dragging');
        block.setAttribute('draggable', 'false');
        var parentZone = block.closest('.cbl-navbar-zone');
        var slot = zoneSlot(parentZone);
        var kind = (block.dataset.navBlockKind || '').toLowerCase();
        block.dataset.navBlockSlot = slot;
        persistBlockSlot(kind, slot, block);
        persistZoneBlockOrder(parentZone);
      });
      block.addEventListener('dragover', function (e) {
        e.preventDefault();
        var dragging = document.querySelector('.cbl-nav-block.nav-dragging');
        if (!dragging || dragging === block) return;
        var rect = block.getBoundingClientRect();
        var pivot = rect.top + rect.height / 2;
        if (e.clientY < pivot) {
          zone.insertBefore(dragging, block);
        } else {
          zone.insertBefore(dragging, block.nextSibling);
        }
      });
    });

    if (zone.dataset.blockZoneWired !== '1') {
      zone.dataset.blockZoneWired = '1';
      zone.addEventListener('dragover', function (e) {
        e.preventDefault();
        var dragging = document.querySelector('.cbl-nav-block.nav-dragging');
        if (!dragging) return;
        if (zone.lastElementChild !== dragging) {
          zone.appendChild(dragging);
        }
      });
    }
  }

  function hideNavBlock(kind, block) {
    if (!kind) return;
    var req = null;
    if (kind === 'search') {
      req = setChromeField('show_nav_search', '0');
    } else if (kind === 'auth') {
      req = Promise.all([
        setChromeField('show_nav_login', '0'),
        setChromeField('show_nav_register', '0'),
        setChromeField('show_nav_profile', '0')
      ]);
    } else if (kind === 'cta') {
      req = Promise.all([
        setChromeField('nav_cta_label', ''),
        setChromeField('nav_cta_url', '')
      ]);
    } else if (kind === 'brand') {
      req = postJson('/edit/site-brand/update/', { field: 'show_brand_name', value: '0' });
    } else if (kind === 'links') {
      if (!confirm('Delete all navbar menu links?')) return;
      req = postJson('/edit/navbar/clear/');
    }
    if (!req) return;
    Promise.resolve(req)
      .then(function () {
        if (block && block.parentElement) {
          block.parentElement.removeChild(block);
        } else {
          window.location.reload();
        }
      })
      .catch(function (err) { alert(err.message); });
  }

  function zoneSlot(zone) {
    if (!zone) return 'left';
    if (zone.classList.contains('cbl-navbar-center')) return 'center';
    if (zone.classList.contains('cbl-navbar-right')) return 'right';
    return 'left';
  }

  function persistZoneBlockOrder(zone) {
    if (!zone) return;
    var slot = zoneSlot(zone);
    var order = [];
    Array.prototype.slice.call(zone.children || []).forEach(function (el) {
      if (!el || !el.getAttribute || !el.hasAttribute('data-nav-block-kind')) return;
      order.push(el.dataset.navBlockKind);
    });
    if (!order.length) return;
    postJson('/edit/navbar/block-order/update/', {
      slot: slot,
      order: order.join(',')
    }).catch(function (err) { console.warn('Block order save failed:', err.message); });
  }

  function persistBlockSlot(kind, slot, blockEl) {
    if (!kind || !slot) return;
    var req;
    if (kind === 'brand') {
      req = postJson('/edit/site-brand/update/', { field: 'brand_position', value: slot });
    } else if (kind === 'search') {
      req = setChromeField('nav_search_slot', slot);
    } else if (kind === 'auth') {
      req = setChromeField('nav_auth_slot', slot);
    } else if (kind === 'cta') {
      req = setChromeField('nav_cta_slot', slot);
    } else if (kind === 'links') {
      var ids = [];
      blockEl.querySelectorAll('.nav-editable[data-navlink-id]').forEach(function (li) {
        ids.push(li.dataset.navlinkId);
      });
      req = Promise.all(ids.map(function (id) {
        return postJson('/edit/nav-link/' + id + '/update/', { field: 'slot', value: slot });
      }));
    } else {
      return;
    }
    Promise.resolve(req).then(function () {
      syncChromeSlotState(kind === 'search' ? 'nav_search_slot' :
        kind === 'auth' ? 'nav_auth_slot' :
        kind === 'cta' ? 'nav_cta_slot' : '', slot);
    }).catch(function (err) { console.warn('Slot save failed:', err.message); });
  }

  function slotZoneSelector(slot) {
    if (slot === 'center') return '.cbl-navbar-center';
    if (slot === 'right') return '.cbl-navbar-right';
    return '.cbl-navbar-left';
  }

  function moveChromeBlockToSlot(field, slot) {
    var blocks = document.querySelectorAll('.cbl-navbar-desktop [data-chrome-slot-field="' + field + '"]');
    if (!blocks.length) return;
    var zone = document.querySelector('.cbl-navbar-desktop ' + slotZoneSelector(slot));
    if (!zone) return;
    blocks.forEach(function (el) {
      zone.appendChild(el);
      el.dataset.chromeSlotValue = slot;
    });
  }

  function syncChromeSlotState(field, slot) {
    var blocks = document.querySelectorAll('[data-chrome-slot-field="' + field + '"]');
    blocks.forEach(function (el) {
      el.dataset.chromeSlotValue = slot;
      var controls = el.querySelector('.chrome-slot-edit-controls');
      if (!controls) return;
      controls.querySelectorAll('.nav-edit-slot-btn').forEach(function (btn) {
        btn.classList.remove('nav-edit-slot-active');
        if ((btn.dataset.slot || '').toLowerCase() === slot) {
          btn.classList.add('nav-edit-slot-active');
        }
      });
    });
  }

  function startBrandRename(el) {
    if (!el || el.dataset.renaming === '1') return;
    var span = el.querySelector('span');
    if (!span) return;
    el.dataset.renaming = '1';
    var originalText = span.textContent.trim();
    var input = document.createElement('input');
    input.type = 'text';
    input.value = originalText;
    input.className = 'cbl-inline-rename';
    input.setAttribute('aria-label', 'Rename brand');
    var originalHTML = span.innerHTML;
    span.textContent = '';
    span.appendChild(input);
    var clickGuard = function (ev) { ev.preventDefault(); };
    el.addEventListener('click', clickGuard);
    input.focus();
    input.select();

    function cleanup(restore) {
      el.dataset.renaming = '0';
      el.removeEventListener('click', clickGuard);
      if (restore) span.innerHTML = originalHTML;
    }
    function save() {
      var next = (input.value || '').trim();
      if (!next || next === originalText) { cleanup(true); return; }
      postJson('/edit/site-brand/update/', { field: 'name', value: next })
        .then(function () {
          cleanup(false);
          span.textContent = next;
          el.dataset.brandName = next;
        })
        .catch(function (err) { alert(err.message); cleanup(true); });
    }
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); save(); }
      else if (e.key === 'Escape') { e.preventDefault(); cleanup(true); }
    });
    input.addEventListener('blur', save);
  }

  // -------------------------------------------------------------------------
  // 3. Drag-to-reorder nav links (native HTML5 drag, top level only)
  // -------------------------------------------------------------------------
  function setupNavDragReorder() {
    var desktopLists = document.querySelectorAll('.cbl-navbar-desktop ul.cbl-navbar-links');
    desktopLists.forEach(function (ul) {
      initDragList(ul, '.nav-editable', null);
    });

    var dropdownParents = document.querySelectorAll('.cbl-navbar-desktop .nav-editable.dropdown');
    dropdownParents.forEach(function (parentLi) {
      var menu = parentLi.querySelector(':scope > ul.dropdown-menu');
      if (!menu) return;
      initDragList(menu, '.nav-editable-child', parentLi.dataset.navlinkId || null);
    });
  }

  var currentDragSourceList = null;

  function initDragList(ul, itemSelector, parentId) {
    var items = ul.querySelectorAll(':scope > ' + itemSelector);
    if (!items.length) return;

    items.forEach(function (li) {
      if (li.dataset.dragWired === '1') return;
      li.dataset.dragWired = '1';
      li.setAttribute('draggable', 'false');

      var handle = document.createElement('span');
      handle.className = 'nav-drag-handle';
      handle.title = 'Drag to reorder';
      handle.innerHTML = '<i class="bi bi-grip-vertical"></i>';
      handle.addEventListener('mousedown', function () { li.setAttribute('draggable', 'true'); });
      handle.addEventListener('mouseup', function () { li.setAttribute('draggable', 'false'); });
      li.appendChild(handle);

      li.addEventListener('dragstart', function (e) {
        li.classList.add('nav-dragging');
        currentDragSourceList = ul;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', li.dataset.navlinkId || '');
      });
      li.addEventListener('dragend', function () {
        li.classList.remove('nav-dragging');
        li.setAttribute('draggable', 'false');
        var destList = li.parentElement;
        if (currentDragSourceList && currentDragSourceList !== destList) {
          saveNavOrder(currentDragSourceList, itemSelector, parentId);
          if (!parentId) {
            syncTopLevelSlot(li, destList);
          }
        }
        saveNavOrder(destList || ul, itemSelector, parentId);
        currentDragSourceList = null;
      });
      li.addEventListener('dragover', function (e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        var dragging = document.querySelector('.nav-dragging');
        if (!dragging || dragging === li) return;
        var rect = li.getBoundingClientRect();
        var pivot = rect.top + rect.height / 2;
        if (e.clientY < pivot) {
          ul.insertBefore(dragging, li);
        } else {
          ul.insertBefore(dragging, li.nextSibling);
        }
      });

    });

    if (ul.dataset.dragContainerWired !== '1') {
      ul.dataset.dragContainerWired = '1';
      ul.addEventListener('dragover', function (e) {
        e.preventDefault();
        var dragging = document.querySelector('.nav-dragging');
        if (!dragging) return;
        if (ul.lastElementChild !== dragging) {
          ul.appendChild(dragging);
        }
      });
    }
  }

  function syncTopLevelSlot(li, listEl) {
    if (!li || !listEl) return;
    var zone = listEl.closest('.cbl-navbar-zone');
    if (!zone) return;
    var slot = 'left';
    if (zone.classList.contains('cbl-navbar-center')) slot = 'center';
    if (zone.classList.contains('cbl-navbar-right')) slot = 'right';
    var id = li.dataset.navlinkId;
    if (!id) return;
    postJson('/edit/nav-link/' + id + '/update/', { field: 'slot', value: slot })
      .catch(function (err) { console.warn('Slot update failed:', err.message); });
  }

  function saveNavOrder(ul, itemSelector, parentId) {
    var ids = [];
    ul.querySelectorAll(':scope > ' + itemSelector).forEach(function (li) {
      ids.push(li.dataset.navlinkId);
    });
    if (!ids.length) return;
    postJson('/edit/nav-links/reorder/', {
      order: ids.join(','),
      parent_id: parentId || ''
    })
      .catch(function (err) { console.warn('Reorder failed:', err.message); });
  }

  // -------------------------------------------------------------------------
  // 4. Footer link editing: same hover-controls pattern as the navbar.
  // -------------------------------------------------------------------------
  function setupFooterEditing() {
    document.querySelectorAll('.footer-link-editable').forEach(wireFooterLink);
    document.querySelectorAll('.footer-col-editable').forEach(wireFooterColumn);
    // "Add column" is handled by the footer chrome-hover-add button in base.html
  }

  function wireFooterLink(li) {
    if (li.dataset.footerWired === '1') return;
    li.dataset.footerWired = '1';

    var id = li.dataset.footerlinkId;
    var controls = document.createElement('span');
    controls.className = 'footer-edit-controls';

    var editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'nav-edit-btn';
    editBtn.title = 'Rename';
    editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
    editBtn.addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      startInlineRename(li, 'footer-link', id);
    });

    var delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'nav-edit-btn nav-edit-del';
    delBtn.title = 'Delete link';
    delBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
    delBtn.addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      postJson('/edit/footer-link/' + id + '/delete/')
        .then(function () {
          li.style.display = 'none';
          toast('Link removed.', function () {
            postJson('/edit/footer-link/' + id + '/undo/')
              .then(function () { li.style.display = ''; })
              .catch(function (err) { alert(err.message); });
          });
        })
        .catch(function (err) { alert(err.message); });
    });

    controls.appendChild(editBtn);
    controls.appendChild(delBtn);
    li.appendChild(controls);
  }

  function wireFooterColumn(col) {
    if (col.dataset.footerColWired === '1') return;
    col.dataset.footerColWired = '1';

    var id = col.dataset.footercolId;
    var ul = col.querySelector('ul');
    if (!ul) return;

    // Add-link button at the bottom of each column. No prompts: create a
    // placeholder, then auto-focus its inline rename input after reload.
    if (!ul.querySelector('.footer-add-link')) {
      var li = document.createElement('li');
      li.className = 'nav-item footer-add-link';
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'footer-add-btn';
      btn.title = 'Add a link to this column';
      btn.innerHTML = '<i class="bi bi-plus-lg"></i> Add link';
      btn.addEventListener('click', function () {
        if (btn.dataset.busy === '1') return;
        btn.dataset.busy = '1';
        postJson('/edit/footer-column/' + id + '/link/add/', {
          label: 'New Link', url: '/',
        })
          .then(function (resp) {
            if (resp && resp.id) {
              setFocusHint({ kind: 'footer-link', id: resp.id });
            }
            window.location.reload();
          })
          .catch(function (err) {
            btn.dataset.busy = '0';
            alert(err.message);
          });
      });
      li.appendChild(btn);
      ul.appendChild(li);
    }

    // Click the column heading to inline-rename it.
    var heading = col.querySelector('h5, h4, h6');
    if (heading && !heading.dataset.colEditWired) {
      heading.dataset.colEditWired = '1';
      heading.style.cursor = 'pointer';
      heading.title = 'Click to rename column';
      heading.addEventListener('click', function () {
        startInlineRename(col, 'footer-column', id);
      });
    }
  }

  // The "Add column" tile inside the footer is replaced by the chrome-hover-add
  // button at the top of the footer region (rendered in base.html). That button
  // creates a placeholder column and the inline rename auto-focuses after reload.

  document.addEventListener('DOMContentLoaded', init);
}());

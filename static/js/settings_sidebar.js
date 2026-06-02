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

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  var PAGE_TEMPLATES = [
    { key: 'landing',   name: 'Landing Page',   icon: 'rocket-takeoff-fill',  description: 'Hero, features, testimonials, call to action.' },
    { key: 'about',     name: 'About Page',      icon: 'people-fill',          description: 'Your story, values, and team highlights.' },
    { key: 'contact',   name: 'Contact Page',    icon: 'envelope-fill',        description: 'Working contact form with your details.' },
    { key: 'services',  name: 'Services Page',   icon: 'briefcase-fill',       description: 'What you offer, how it works, pricing.' },
    { key: 'portfolio',  name: 'Portfolio',   icon: 'images',               description: 'Gallery of your work with CTA.' },
    { key: 'ecommerce', name: 'Shop',        icon: 'bag-fill',             description: 'Storefront with product highlights and checkout.' },
    { key: 'blog',      name: 'Blog',        icon: 'newspaper',            description: 'A blog for articles, news, and updates.' },
    { key: 'blank',     name: 'Blank Page',       icon: 'file-earmark-plus',    description: 'Empty page - add exactly what you need.' },
  ];

  function init() {
    if (!document.body.classList.contains('edit-mode')) return;
    var body = document.getElementById('edit-sidebar-body');
    if (!body) return;

    var state = {
      current: null,
      page: readPageState(),
    };

    function render(selection) {
      state.current = selection;
      body.innerHTML = renderSelection(selection, state.page);
      wireBody(body, selection, state.page);
      markSelected(selection);
    }

    function defaultSelection() {
      render({ kind: 'page' });
    }

    window.cblShowNewNavLinkPanel = function (isButton) {
      var title = document.querySelector('.edit-sidebar-title');
      if (title) title.textContent = isButton ? 'New Button' : 'New Nav Link';
      body.innerHTML = renderNewNavLink(isButton);
      wireNewNavLink(body, isButton);
    };

    document.addEventListener('click', function (event) {
      if (event.target.closest('#edit-sidebar')) return;
      if (event.target.closest('.nav-edit-controls, .section-toolbar, .chrome-hover-add, .edit-pencil-btn, .nav-drag-handle, .item-delete-btn, .footer-edit-controls, .brand-edit-controls, .edit-form')) {
        return;
      }
      // Keep auth actions functional while edit-mode inspector is active.
      // Without this, capture-phase interception blocks logout form submits.
      if (event.target.closest('form[action$="/accounts/logout/"]')) {
        return;
      }

      var iconEdit = event.target.closest('.cbl-icon-edit[data-item-id]');
      if (iconEdit) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'item', el: iconEdit, itemId: iconEdit.dataset.itemId });
        return;
      }

      var itemWrap = event.target.closest('.edit-wrap[data-edit-model="item"]');
      if (itemWrap) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'item', el: itemWrap, itemId: itemWrap.dataset.editId });
        return;
      }

      var child = event.target.closest('.nav-editable-child');
      if (child) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'nav-child', el: child });
        return;
      }

      var navLink = event.target.closest('.nav-editable');
      if (navLink) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'nav-link', el: navLink });
        return;
      }

      var footerLink = event.target.closest('.footer-link-editable');
      if (footerLink) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'footer-link', el: footerLink });
        return;
      }

      var footerCol = event.target.closest('.footer-col-editable');
      if (footerCol) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'footer-column', el: footerCol });
        return;
      }

      var brand = event.target.closest('.brand-editable');
      if (brand) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'brand', el: brand });
        return;
      }

      var navBlock = event.target.closest('.cbl-nav-block');
      if (navBlock && navBlock.dataset.navBlockKind) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'nav-block', el: navBlock, blockKind: navBlock.dataset.navBlockKind });
        return;
      }

      var navZone = event.target.closest('.cbl-navbar-zone');
      if (navZone && !event.target.closest('.nav-editable, .cbl-nav-block, .brand-editable, .nav-edit-controls, .chrome-hover-add')) {
        event.preventDefault();
        event.stopPropagation();
        var zoneName = navZone.classList.contains('cbl-navbar-left') ? 'left'
          : navZone.classList.contains('cbl-navbar-right') ? 'right' : 'center';
        render({ kind: 'nav-zone', el: navZone, zoneName: zoneName });
        return;
      }

      var navbarRegion = event.target.closest('#navbar-region');
      if (navbarRegion) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'navbar' });
        return;
      }

      var footerRegion = event.target.closest('#footer-region');
      if (footerRegion) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'footer' });
        return;
      }

      var sectionWrap = event.target.closest('.section-wrap');
      if (sectionWrap) {
        event.preventDefault();
        event.stopPropagation();
        render({ kind: 'section', el: sectionWrap });
        return;
      }

      var pageSections = event.target.closest('#page-sections');
      if (pageSections) {
        render({ kind: 'page' });
      }
    }, true);

    defaultSelection();
    setupPageNav(state.page);
    setupFollowHint();
  }

  // ---------------------------------------------------------------------------
  // Page navigation select — injected into #staff-toolbar in edit mode
  // ---------------------------------------------------------------------------
  function setupPageNav(page) {
    var toolbar = document.getElementById('staff-toolbar');
    if (!toolbar) return;

    var sel = document.createElement('select');
    sel.id = 'staff-page-nav';
    sel.title = 'Go to page';
    sel.innerHTML = '<option value="">Switch page…</option>';

    fetchPages(function (pages) {
      var currentSlug = page ? page.slug : '';
      pages.forEach(function (p) {
        var opt = document.createElement('option');
        opt.value = p.url;
        opt.textContent = (p.title || p.slug) + (p.published ? '' : ' • draft');
        if (p.slug === currentSlug) opt.selected = true;
        sel.appendChild(opt);
      });
    });

    sel.addEventListener('change', function () {
      if (sel.value) window.location.href = sel.value;
    });

    // Insert before the admin gear link
    var gearLink = toolbar.querySelector('a[href="/admin/"]');
    if (gearLink) toolbar.insertBefore(sel, gearLink);
    else toolbar.appendChild(sel);
  }

  // ---------------------------------------------------------------------------
  // Follow hint — floating "Visit →" badge that appears on hover over any
  // link that edit mode intercepts, so users can still navigate the site.
  // ---------------------------------------------------------------------------
  function setupFollowHint() {
    var hint = document.createElement('a');
    hint.id = 'cbl-follow-hint';
    hint.innerHTML = '<i class="bi bi-arrow-right-short" style="font-size:14px"></i>Visit';
    document.body.appendChild(hint);

    var hideTimer = null;

    function show(el, href) {
      clearTimeout(hideTimer);
      hint.href = href;
      hint.style.display = 'flex';
      var rect = el.getBoundingClientRect();
      var w = hint.offsetWidth || 72;
      hint.style.left = Math.min(rect.right - w, window.innerWidth - w - 8) + 'px';
      hint.style.top  = Math.max(rect.top - 30, 4) + 'px';
    }

    function hide() {
      hideTimer = setTimeout(function () { hint.style.display = 'none'; }, 160);
    }

    hint.addEventListener('mouseenter', function () { clearTimeout(hideTimer); });
    hint.addEventListener('mouseleave', hide);

    document.addEventListener('mouseover', function (e) {
      // Navbar links
      var navEl = e.target.closest('.nav-editable');
      if (navEl) {
        var a = navEl.tagName === 'A' ? navEl : navEl.querySelector('a[href]');
        var href = a && a.getAttribute('href');
        if (href && href !== '#' && !/^javascript/i.test(href)) {
          show(navEl, href);
          navEl.addEventListener('mouseleave', hide, { once: true });
        }
        return;
      }
      // Footer links
      var footEl = e.target.closest('.footer-link-editable');
      if (footEl) {
        var a = footEl.tagName === 'A' ? footEl : footEl.querySelector('a[href]');
        var href = a && a.getAttribute('href');
        if (href && href !== '#' && !/^javascript/i.test(href)) {
          show(footEl, href);
          footEl.addEventListener('mouseleave', hide, { once: true });
        }
        return;
      }
      // CTA buttons (a.edit-wrap)
      var btnEl = e.target.closest('a.edit-wrap[data-edit-model="item"]');
      if (btnEl) {
        var href = btnEl.getAttribute('href');
        if (href && href !== '#' && !/^javascript/i.test(href)) {
          show(btnEl, href);
          btnEl.addEventListener('mouseleave', hide, { once: true });
        }
      }
    });
  }


  function readPageState() {
    var ps = document.getElementById('page-sections');
    if (!ps) return null;
    return {
      id: ps.dataset.pageId || '',
      slug: ps.dataset.pageSlug || '',
      title: ps.dataset.pageTitle || '',
      published: ps.dataset.pagePublished === '1',
      inNavbar: ps.dataset.pageInNavbar === '1',
      inFooter: ps.dataset.pageInFooter === '1',
      ogTitle: ps.dataset.pageOgTitle || '',
      ogDescription: ps.dataset.pageOgDescription || '',
    };
  }

  function markSelected(selection) {
    document.querySelectorAll('.cbl-inspector-selected').forEach(function (el) {
      el.classList.remove('cbl-inspector-selected');
    });
    if (selection && selection.el) {
      selection.el.classList.add('cbl-inspector-selected');
    }
  }

  function renderSelection(selection, page) {
    if (!selection || selection.kind === 'page') return renderPage(page);
    if (selection.kind === 'section') return renderSection(selection.el);
    if (selection.kind === 'nav-link') return renderNavLink(selection.el, false);
    if (selection.kind === 'nav-child') return renderNavLink(selection.el, true);
    if (selection.kind === 'footer-link') return renderFooterLink(selection.el);
    if (selection.kind === 'footer-column') return renderFooterColumn(selection.el);
    if (selection.kind === 'brand') return renderBrand(selection.el);
    if (selection.kind === 'nav-block') return renderNavBlock(selection.el, selection.blockKind);
    if (selection.kind === 'navbar') return renderNavbar();
    if (selection.kind === 'nav-zone') return renderNavZone(selection.zoneName);
    if (selection.kind === 'footer') return renderFooter();
    if (selection.kind === 'item') return renderItem(selection.itemId);
    return renderPage(page);
  }

  function renderPage(page) {
    if (!page) {
      return '<p class="text-body-secondary mb-0">No page selected.</p>';
    }

    var rows = [];
    rows.push(sectionShell('Page',
      '<div class="mb-3">' +
        '<div class="fw-semibold mb-1">' + escapeHtml(page.title || page.slug || 'Page') + '</div>' +
        '<div class="small text-body-secondary">/' + escapeHtml(page.slug || '') + '</div>' +
      '</div>' +
      badges([page.published ? ['Published', 'success'] : ['Draft', 'secondary'],
        page.inNavbar ? ['In navbar', 'primary'] : ['Not in navbar', 'light'],
        page.inFooter ? ['In footer', 'primary'] : ['Not in footer', 'light']]) +
      actionRow([
        page.published ? ['.sidebar-page-action[data-action="unpublish"]', 'Unpublish', 'outline-secondary'] : ['.sidebar-page-action[data-action="publish"]', 'Publish', 'outline-success'],
        page.inNavbar ? ['.sidebar-page-action[data-action="remove-nav"]', 'Remove navbar', 'outline-danger'] : ['.sidebar-page-action[data-action="add-nav"]', 'Add to navbar', 'outline-primary'],
        page.inFooter ? null : ['.sidebar-page-action[data-action="add-footer"]', 'Add to footer', 'outline-primary']
      ]) +
      (page.slug !== 'home' ? '<button type="button" class="btn btn-sm btn-outline-danger w-100 mt-2 sidebar-delete-page">Delete page</button>' : '')
    ));

    rows.push('<div class="edit-sidebar-section">' +
      '<h3>SEO</h3>' +
      '<label class="form-label small mb-1">Page title</label>' +
      '<input type="text" class="form-control form-control-sm mb-2 sidebar-seo-title" value="' + escapeHtml(page.title || '') + '">' +
      '<label class="form-label small mb-1">Social title <span class="text-body-secondary">(og:title)</span></label>' +
      '<input type="text" class="form-control form-control-sm mb-2 sidebar-seo-og-title" placeholder="Defaults to page title" value="' + escapeHtml(page.ogTitle || '') + '">' +
      '<label class="form-label small mb-1">Social description <span class="text-body-secondary">(og:description)</span></label>' +
      '<textarea class="form-control form-control-sm mb-2 sidebar-seo-og-desc" rows="3" placeholder="Defaults to site tagline">' + escapeHtml(page.ogDescription || '') + '</textarea>' +
      '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-seo">Save SEO</button>' +
      '</div>');

    rows.push('<div class="edit-sidebar-section">' +
      '<h3>Theme</h3>' +
      '<div class="sidebar-theme-swatches d-flex flex-wrap gap-2">' +
        '<span class="small text-body-secondary">Loading…</span>' +
      '</div>' +
      '</div>');

    rows.push('<div class="edit-sidebar-section">' +
      '<h3>Pages</h3>' +
      '<div class="sidebar-pages-list mb-2"><span class="small text-body-secondary">Loading…</span></div>' +
      '<button type="button" class="btn btn-sm btn-outline-success w-100 sidebar-new-page-btn">+ New page</button>' +
      '</div>');

    var sectionSpacing = document.body.dataset.sectionSpacing || 'normal';
    var bodyBg = document.body.dataset.bodyBg || '';
    rows.push('<div class="edit-sidebar-section">' +
      '<h3>Page design</h3>' +
      '<label class="form-label small mb-1">Section spacing</label>' +
      '<select class="form-select form-select-sm mb-2 sidebar-section-spacing">' +
        '<option value="compact"'  + (sectionSpacing === 'compact'  ? ' selected' : '') + '>Compact</option>' +
        '<option value="normal"'   + (sectionSpacing === 'normal'   ? ' selected' : '') + '>Normal</option>' +
        '<option value="spacious"' + (sectionSpacing === 'spacious' ? ' selected' : '') + '>Spacious</option>' +
      '</select>' +
      renderColorField('sidebar-body-bg', bodyBg, 'Body background (overrides theme)') +
      '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-page-design">Save page design</button>' +
      '</div>');

    rows.push('<div class="edit-sidebar-section">' +
      '<h3>Switch template</h3>' +
      '<p class="small text-body-secondary mb-2">Choose an industry starter to rebuild your site with fresh pages and content.</p>' +
      '<div class="sidebar-packs-list mb-2"><span class="small text-body-secondary">Loading…</span></div>' +
      '</div>');

    return rows.join('');
  }

  var COLUMN_SECTION_TYPES = ['image_grid', 'feature_list', 'testimonials', 'gallery', 'pricing_table', 'video_embed'];
  var ALLOWED_COLUMNS = [1, 2, 3, 4, 6];

  function renderSection(sectionEl) {
    var sectionId = sectionEl.dataset.sectionId || '';
    var sectionType = sectionEl.dataset.sectionType || '';
    var layout = sectionEl.dataset.sectionLayout || '';
    var layouts = (sectionEl.dataset.sectionLayouts || '').split(',').filter(Boolean);
    var visible = sectionEl.dataset.sectionVisible !== '0';
    var heading = sectionEl.dataset.sectionHeading || '';
    var subheading = sectionEl.dataset.sectionSubheading || '';
    var bg = sectionEl.dataset.sectionBg || '';
    var columns      = sectionEl.dataset.sectionColumns      || '';
    var imageUrl     = sectionEl.dataset.sectionImageUrl     || '';
    var padTop       = sectionEl.dataset.sectionPaddingTop   || '';
    var padBot       = sectionEl.dataset.sectionPaddingBottom || '';
    var padLeft      = sectionEl.dataset.sectionPaddingLeft  || '';
    var padRight     = sectionEl.dataset.sectionPaddingRight || '';
    var marTop       = sectionEl.dataset.sectionMarginTop    || '';
    var marBot       = sectionEl.dataset.sectionMarginBottom || '';
    var borderStyle  = sectionEl.dataset.sectionBorderStyle  || 'none';
    var borderWidth  = sectionEl.dataset.sectionBorderWidth  || '1';
    var borderColor  = sectionEl.dataset.sectionBorderColor  || '';
    var borderRadius = sectionEl.dataset.sectionBorderRadius || '';
    var itemStyle    = sectionEl.dataset.sectionItemStyle    || 'none';
    var showColumns  = COLUMN_SECTION_TYPES.indexOf(sectionType) !== -1;

    var layoutOptions = layouts.map(function (item) {
      return '<option value="' + escapeHtml(item) + '"' + (item === layout ? ' selected' : '') + '>' + escapeHtml(item) + '</option>';
    }).join('');

    var columnsHtml = '';
    if (showColumns) {
      columnsHtml = '<label class="form-label small mb-1">Columns</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-section-columns">' +
        ALLOWED_COLUMNS.map(function (n) {
          return '<option value="' + n + '"' + (String(n) === String(columns) ? ' selected' : '') + '>' + n + ' across</option>';
        }).join('') +
        '</select>';
    }

    var imgHtml = imageUrl
      ? '<img src="' + escapeHtml(imageUrl) + '" alt="" style="max-height:80px;max-width:100%;border-radius:4px;object-fit:cover;" class="mb-2 d-block">'
      : '<p class="small text-body-secondary mb-2">No image.</p>';

    return '<div class="mb-2 fw-semibold">' + escapeHtml(sectionType.replace(/_/g, ' ')) + '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Image</h3>' +
        imgHtml +
        '<input type="file" class="sidebar-section-img-file" accept="image/*" style="display:none">' +
        '<button type="button" class="btn btn-sm btn-outline-primary w-100 mb-1 sidebar-upload-section-img">Upload image</button>' +
        (imageUrl ? '<button type="button" class="btn btn-sm btn-outline-danger w-100 mb-1 sidebar-remove-section-img">Remove image</button>' : '') +
        '<div class="small text-danger sidebar-section-img-status"></div>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Content</h3>' +
        '<label class="form-label small mb-1">Heading</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-section-heading" value="' + escapeHtml(heading) + '">' +
        '<label class="form-label small mb-1">Subheading</label>' +
        renderRichTextEditor('sidebar-section-subheading', subheading) +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-content">Save content</button>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Display</h3>' +
        '<label class="form-label small mb-1">Layout</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-section-layout">' + layoutOptions + '</select>' +
        columnsHtml +
        renderColorField('sidebar-section-bg', bg, 'Background color') +
        '<label class="form-label small mb-1">Border</label>' +
        '<div class="d-flex gap-2 mb-1">' +
          '<select class="form-select form-select-sm sidebar-section-border-style" style="flex:2">' +
            '<option value="none"'   + (borderStyle === 'none'   ? ' selected' : '') + '>None</option>' +
            '<option value="solid"'  + (borderStyle === 'solid'  ? ' selected' : '') + '>Solid</option>' +
            '<option value="dashed"' + (borderStyle === 'dashed' ? ' selected' : '') + '>Dashed</option>' +
            '<option value="dotted"' + (borderStyle === 'dotted' ? ' selected' : '') + '>Dotted</option>' +
          '</select>' +
          '<input type="number" class="form-control form-control-sm sidebar-section-border-width" style="flex:1" min="1" max="20" value="' + escapeHtml(borderWidth) + '" placeholder="px">' +
        '</div>' +
        renderColorField('sidebar-section-border-color', borderColor, 'Border color') +
        '<label class="form-label small mb-1">Corner radius (px)</label>' +
        '<input type="number" class="form-control form-control-sm mb-2 sidebar-section-border-radius" min="0" max="200" value="' + escapeHtml(borderRadius) + '" placeholder="0">' +
        '<label class="form-label small mb-1">Item style</label>' +
        '<div class="btn-group btn-group-sm w-100 mb-2 sidebar-section-item-style-group">' +
          '<input type="radio" class="btn-check" name="item-style-' + escapeHtml(sectionId) + '" id="is-none-'       + escapeHtml(sectionId) + '" value="none"        autocomplete="off"' + (itemStyle === 'none'        ? ' checked' : '') + '><label class="btn btn-outline-secondary" for="is-none-'       + escapeHtml(sectionId) + '">None</label>' +
          '<input type="radio" class="btn-check" name="item-style-' + escapeHtml(sectionId) + '" id="is-bordered-'  + escapeHtml(sectionId) + '" value="bordered"     autocomplete="off"' + (itemStyle === 'bordered'     ? ' checked' : '') + '><label class="btn btn-outline-secondary" for="is-bordered-'  + escapeHtml(sectionId) + '">Bordered</label>' +
          '<input type="radio" class="btn-check" name="item-style-' + escapeHtml(sectionId) + '" id="is-card-'      + escapeHtml(sectionId) + '" value="card"         autocomplete="off"' + (itemStyle === 'card'         ? ' checked' : '') + '><label class="btn btn-outline-secondary" for="is-card-'      + escapeHtml(sectionId) + '">Card</label>' +
          '<input type="radio" class="btn-check" name="item-style-' + escapeHtml(sectionId) + '" id="is-shadow-'    + escapeHtml(sectionId) + '" value="card-shadow"  autocomplete="off"' + (itemStyle === 'card-shadow'  ? ' checked' : '') + '><label class="btn btn-outline-secondary" for="is-shadow-'    + escapeHtml(sectionId) + '">Shadow</label>' +
        '</div>' +
        '<label class="form-label small mb-1">Padding inside (rem)</label>' +
        '<div class="d-flex gap-2 align-items-center mb-1">' +
          '<span class="small text-body-secondary" style="white-space:nowrap">Top</span>' +
          '<input type="number" class="form-control form-control-sm sidebar-section-pad-top" min="0" max="30" step="0.5" value="' + escapeHtml(padTop) + '" placeholder="0">' +
          '<span class="small text-body-secondary" style="white-space:nowrap">Bottom</span>' +
          '<input type="number" class="form-control form-control-sm sidebar-section-pad-bot" min="0" max="30" step="0.5" value="' + escapeHtml(padBot) + '" placeholder="0">' +
        '</div>' +
        '<div class="d-flex gap-2 align-items-center mb-2">' +
          '<span class="small text-body-secondary" style="white-space:nowrap">Left</span>' +
          '<input type="number" class="form-control form-control-sm sidebar-section-pad-left" min="0" max="30" step="0.5" value="' + escapeHtml(padLeft) + '" placeholder="0">' +
          '<span class="small text-body-secondary" style="white-space:nowrap">Right</span>' +
          '<input type="number" class="form-control form-control-sm sidebar-section-pad-right" min="0" max="30" step="0.5" value="' + escapeHtml(padRight) + '" placeholder="0">' +
        '</div>' +
        '<label class="form-label small mb-1">Margin outside (rem)</label>' +
        '<div class="d-flex gap-2 align-items-center mb-2">' +
          '<span class="small text-body-secondary" style="white-space:nowrap">Top</span>' +
          '<input type="number" class="form-control form-control-sm sidebar-section-mar-top" min="0" max="30" step="0.5" value="' + escapeHtml(marTop) + '" placeholder="0">' +
          '<span class="small text-body-secondary" style="white-space:nowrap">Bottom</span>' +
          '<input type="number" class="form-control form-control-sm sidebar-section-mar-bot" min="0" max="30" step="0.5" value="' + escapeHtml(marBot) + '" placeholder="0">' +
        '</div>' +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-display">Save display</button>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Visibility</h3>' +
        '<button type="button" class="btn btn-sm ' + (visible ? 'btn-outline-danger' : 'btn-outline-success') + ' w-100 sidebar-toggle-section">' +
          (visible ? 'Hide section' : 'Show section') +
        '</button>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Structure</h3>' +
        (['hero', 'cta_banner'].indexOf(sectionType) !== -1
          ? '<div class="small text-body-secondary mb-1">Add element</div>' +
            '<div class="d-flex gap-1 mb-2">' +
              '<button type="button" class="btn btn-sm btn-outline-success flex-fill sidebar-add-item" data-item-type="button">+ Button</button>' +
              '<button type="button" class="btn btn-sm btn-outline-success flex-fill sidebar-add-item" data-item-type="text">+ Text</button>' +
              '<button type="button" class="btn btn-sm btn-outline-success flex-fill sidebar-add-item" data-item-type="heading">+ Heading</button>' +
            '</div>'
          : ['text_block', 'video_embed'].indexOf(sectionType) === -1
            ? '<button type="button" class="btn btn-sm btn-outline-success w-100 mb-2 sidebar-add-item">Add item</button>'
            : '') +
        '<button type="button" class="btn btn-sm btn-outline-danger w-100 sidebar-delete-section">Delete section</button>' +
      '</div>';
  }

  function renderNavLink(li, child) {
    var id = li.dataset.navlinkId || '';
    var label = li.dataset.navlinkLabel || '';
    var href = li.dataset.navlinkHref || '';
    var slot = li.dataset.navlinkSlot || 'left';
    var button = li.dataset.navlinkButton === '1';
    var newTab = li.dataset.navlinkNewtab === '1';
    var visible = li.dataset.navlinkVisible !== '0';
    var marL = li.dataset.navlinkMarginLeft || '0';
    var marR = li.dataset.navlinkMarginRight || '0';

    return sectionShell(child ? 'Dropdown Item' : 'Nav Item',
      '<div class="edit-sidebar-section">' +
        '<h3>Content</h3>' +
        '<label class="form-label small mb-1">Label</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-nav-label" value="' + escapeHtml(label) + '">' +
        '<label class="form-label small mb-1">Link to</label>' +
        '<select class="form-select form-select-sm mb-1 sidebar-page-picker"><option value="">Custom URL…</option></select>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-nav-url" placeholder="/path/ or https://…" value="' + escapeHtml(href) + '">' +
        '<div class="form-check mb-1">' +
          '<input class="form-check-input sidebar-nav-newtab" type="checkbox" id="snnt-' + escapeHtml(id) + '"' + (newTab ? ' checked' : '') + '>' +
          '<label class="form-check-label small" for="snnt-' + escapeHtml(id) + '">Open in new tab</label>' +
        '</div>' +
        (!child ?
          '<div class="form-check mb-1">' +
            '<input class="form-check-input sidebar-nav-visible" type="checkbox" id="snv-' + escapeHtml(id) + '"' + (visible ? ' checked' : '') + '>' +
            '<label class="form-check-label small" for="snv-' + escapeHtml(id) + '">Visible in navbar</label>' +
          '</div>' +
          '<div class="form-check mb-2">' +
            '<input class="form-check-input sidebar-nav-button" type="checkbox" id="snb-' + escapeHtml(id) + '"' + (button ? ' checked' : '') + '>' +
            '<label class="form-check-label small" for="snb-' + escapeHtml(id) + '">Render as button</label>' +
          '</div>' +
          '<label class="form-label small mb-1">Item spacing (px)</label>' +
          '<div class="d-flex gap-2 mb-2">' +
            '<input type="number" class="form-control form-control-sm sidebar-nav-margin-left" min="0" max="200" value="' + escapeHtml(marL) + '" placeholder="Left">' +
            '<input type="number" class="form-control form-control-sm sidebar-nav-margin-right" min="0" max="200" value="' + escapeHtml(marR) + '" placeholder="Right">' +
          '</div>'
        : '') +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-nav">Save</button>' +
      '</div>' +
      (!child ?
        '<div class="edit-sidebar-section">' +
          '<h3>Slot</h3>' +
          '<div class="d-flex gap-2">' +
            '<button type="button" class="btn btn-sm btn-outline-secondary flex-fill sidebar-move-left"><i class="bi bi-arrow-left-short"></i></button>' +
            '<button type="button" class="btn btn-sm btn-outline-secondary flex-fill sidebar-move-right"><i class="bi bi-arrow-right-short"></i></button>' +
          '</div>' +
          '<div class="small text-body-secondary mt-2">Current: ' + escapeHtml(slot) + '</div>' +
        '</div>'
      : '') +
      '<div class="edit-sidebar-section">' +
        '<h3>Actions</h3>' +
        (!child ? '<button type="button" class="btn btn-sm btn-outline-success w-100 mb-2 sidebar-add-child">Add dropdown item</button>' : '') +
        '<button type="button" class="btn btn-sm btn-outline-danger w-100 sidebar-delete-nav">Delete</button>' +
      '</div>'
    );
  }

  function renderFooterLink(li) {
    var id      = li.dataset.footerlinkId || '';
    var label   = li.dataset.footerlinkLabel || '';
    var href    = (li.querySelector('a') && li.querySelector('a').getAttribute('href')) || '';
    var newTab  = li.dataset.footerlinkNewtab === '1';
    var visible = li.dataset.footerlinkVisible !== '0';

    return sectionShell('Footer Link',
      '<div class="edit-sidebar-section">' +
        '<h3>Content</h3>' +
        '<label class="form-label small mb-1">Label</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-footer-label" value="' + escapeHtml(label) + '">' +
        '<label class="form-label small mb-1">Link to</label>' +
        '<select class="form-select form-select-sm mb-1 sidebar-footer-page-picker"><option value="">Custom URL…</option></select>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-footer-url" placeholder="/path/ or https://…" value="' + escapeHtml(href) + '">' +
        '<div class="form-check mb-1">' +
          '<input class="form-check-input sidebar-footer-newtab" type="checkbox" id="sfnt-' + escapeHtml(id) + '"' + (newTab ? ' checked' : '') + '>' +
          '<label class="form-check-label small" for="sfnt-' + escapeHtml(id) + '">Open in new tab</label>' +
        '</div>' +
        '<div class="form-check mb-2">' +
          '<input class="form-check-input sidebar-footer-visible" type="checkbox" id="sfv-' + escapeHtml(id) + '"' + (visible ? ' checked' : '') + '>' +
          '<label class="form-check-label small" for="sfv-' + escapeHtml(id) + '">Visible in footer</label>' +
        '</div>' +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-footer-link">Save</button>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Actions</h3>' +
        '<button type="button" class="btn btn-sm btn-outline-danger w-100 sidebar-delete-footer-link">Delete</button>' +
      '</div>'
    );
  }

  var FOOTER_QUICK_LINKS = [
    { label: 'Home',            url: '/' },
    { label: 'About',           url: '/about/' },
    { label: 'Contact',         url: '/contact/' },
    { label: 'Services',        url: '/services/' },
    { label: 'Privacy Policy',  url: '/privacy/' },
    { label: 'Terms of Service', url: '/terms/' },
    { label: 'FAQ',             url: '/faq/' },
    { label: 'Help',            url: '/help/' },
  ];

  function renderFooterColumn(col) {
    var quickBtns = FOOTER_QUICK_LINKS.map(function (item) {
      return '<button type="button" class="btn btn-sm btn-outline-secondary sidebar-quick-footer-link" ' +
        'data-label="' + escapeHtml(item.label) + '" data-url="' + escapeHtml(item.url) + '">' +
        escapeHtml(item.label) + '</button>';
    }).join('');

    return sectionShell('Footer Column',
      '<div class="edit-sidebar-section">' +
        '<h3>Column heading</h3>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-footer-heading" value="' + escapeHtml((col.querySelector('h5, h4, h6') || { textContent: '' }).textContent.trim()) + '">' +
        '<div class="form-check mb-2"><input class="form-check-input sidebar-footer-visible" type="checkbox" id="sidebar-footer-visible" ' + (col.dataset.footercolVisible !== '0' ? 'checked' : '') + '><label class="form-check-label small" for="sidebar-footer-visible">Visible</label></div>' +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-footer-column">Save</button>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Add link</h3>' +
        '<button type="button" class="btn btn-sm btn-outline-success w-100 mb-2 sidebar-add-footer-link">+ Custom link</button>' +
        '<div class="small text-body-secondary mb-1">Quick add:</div>' +
        '<div class="d-flex flex-wrap gap-1 mb-2">' + quickBtns + '</div>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Actions</h3>' +
        '<button type="button" class="btn btn-sm btn-outline-danger w-100 sidebar-delete-footer-column">Delete column</button>' +
      '</div>'
    );
  }

  function renderBrand(brand) {
    var logoUrl    = brand.dataset.brandLogoUrl    || '';
    var logoHeight = brand.dataset.brandLogoHeight || '32';
    var logoHtml = logoUrl
      ? '<img src="' + escapeHtml(logoUrl) + '" alt="Logo" style="max-height:48px;max-width:100%;border-radius:4px;" class="mb-2 d-block">'
      : '<p class="small text-body-secondary mb-2">No logo uploaded.</p>';

    return sectionShell('Brand',
      '<div class="edit-sidebar-section">' +
        '<h3>Logo</h3>' +
        logoHtml +
        '<input type="file" class="sidebar-brand-logo-file" accept="image/*" style="display:none">' +
        '<button type="button" class="btn btn-sm btn-outline-primary w-100 mb-1 sidebar-upload-logo">Upload logo</button>' +
        (logoUrl ? '<button type="button" class="btn btn-sm btn-outline-danger w-100 mb-1 sidebar-remove-logo">Remove logo</button>' : '') +
        '<div class="small text-danger sidebar-logo-status"></div>' +
        '<label class="form-label small mb-1 mt-2">Logo height (px)</label>' +
        '<input type="number" class="form-control form-control-sm mb-2 sidebar-brand-logo-height" min="16" max="120" value="' + escapeHtml(logoHeight) + '">' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Content</h3>' +
        '<label class="form-label small mb-1">Brand text</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-brand-name" value="' + escapeHtml(brand.dataset.brandName || '') + '">' +
        '<label class="form-label small mb-1">Position</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-brand-position">' +
          option('left', 'Left', brand.dataset.brandPosition) +
          option('center', 'Center', brand.dataset.brandPosition) +
          option('right', 'Right', brand.dataset.brandPosition) +
        '</select>' +
        '<div class="form-check mb-1"><input class="form-check-input sidebar-brand-show-logo" type="checkbox" id="sidebar-brand-show-logo" ' + ((brand.dataset.brandShowLogo || '1') === '1' ? 'checked' : '') + '><label class="form-check-label small" for="sidebar-brand-show-logo">Show logo image</label></div>' +
        '<div class="form-check mb-2"><input class="form-check-input sidebar-brand-show-name" type="checkbox" id="sidebar-brand-show-name" ' + ((brand.dataset.brandShowName || '1') === '1' ? 'checked' : '') + '><label class="form-check-label small" for="sidebar-brand-show-name">Show brand text</label></div>' +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-brand">Save</button>' +
      '</div>'
    );
  }

  function renderNavBlock(block, kind) {
    kind = (kind || '').toLowerCase();
    var slot = block.dataset.navBlockSlot || 'left';
    var html = [];
    html.push('<div class="mb-2 fw-semibold">' + escapeHtml(kind) + '</div>');
    html.push('<div class="small text-body-secondary mb-3">Block slot: ' + escapeHtml(slot) + '</div>');

    if (kind === 'search') {
      html.push(sectionShell('Search bar',
        '<div class="edit-sidebar-section">' +
          '<h3>Visibility</h3>' +
          '<button type="button" class="btn btn-sm btn-outline-danger w-100 mb-2 sidebar-toggle-chrome" data-field="show_nav_search">Hide search bar</button>' +
        '</div>' +
        '<div class="edit-sidebar-section">' +
          '<h3>Move</h3>' +
          '<div class="d-flex gap-2">' +
            '<button type="button" class="btn btn-sm btn-outline-secondary flex-fill sidebar-move-chrome-left"><i class="bi bi-arrow-left-short"></i></button>' +
            '<button type="button" class="btn btn-sm btn-outline-secondary flex-fill sidebar-move-chrome-right"><i class="bi bi-arrow-right-short"></i></button>' +
          '</div>' +
        '</div>'
      ));
    } else if (kind === 'cta') {
      html.push(sectionShell('CTA button',
        '<div class="edit-sidebar-section">' +
          '<h3>Content</h3>' +
          '<label class="form-label small mb-1">Label</label>' +
          '<input type="text" class="form-control form-control-sm mb-2 sidebar-cta-label" value="' + escapeHtml(block.querySelector('.cbl-navbar-cta') ? block.querySelector('.cbl-navbar-cta').textContent.trim() : '') + '">' +
          '<label class="form-label small mb-1">URL</label>' +
          '<input type="text" class="form-control form-control-sm mb-2 sidebar-cta-url" value="' + escapeHtml((block.querySelector('.cbl-navbar-cta') && block.querySelector('.cbl-navbar-cta').getAttribute('href')) || '') + '">' +
          '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-cta">Save</button>' +
        '</div>' +
        '<div class="edit-sidebar-section">' +
          '<h3>Move</h3>' +
          '<div class="d-flex gap-2">' +
            '<button type="button" class="btn btn-sm btn-outline-secondary flex-fill sidebar-move-chrome-left"><i class="bi bi-arrow-left-short"></i></button>' +
            '<button type="button" class="btn btn-sm btn-outline-secondary flex-fill sidebar-move-chrome-right"><i class="bi bi-arrow-right-short"></i></button>' +
          '</div>' +
        '</div>'
      ));
    } else if (kind === 'auth') {
      var showLogin    = block.dataset.showLogin    !== '0';
      var showRegister = block.dataset.showRegister === '1';
      var showProfile  = block.dataset.showProfile  !== '0';
      html.push(sectionShell('Login / profile',
        '<div class="edit-sidebar-section">' +
          '<h3>Visibility</h3>' +
          '<div class="form-check mb-1"><input class="form-check-input" type="checkbox" checked disabled><label class="form-check-label small" for="sidebar-auth-login">Show login link <span class="text-body-secondary">(always on)</span></label></div>' +
          '<div class="form-check mb-2"><input class="form-check-input sidebar-auth-register" type="checkbox" id="sidebar-auth-register" ' + (showRegister ? 'checked' : '') + '><label class="form-check-label small" for="sidebar-auth-register">Show register link</label></div>' +
          '<div class="form-check mb-1"><input class="form-check-input" type="checkbox" checked disabled><label class="form-check-label small">Show profile / logout menu <span class="text-body-secondary">(always on for admins)</span></label></div>' +
          '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-auth">Save</button>' +
        '</div>' +
        '<div class="edit-sidebar-section">' +
          '<h3>Move</h3>' +
          '<div class="d-flex gap-2">' +
            '<button type="button" class="btn btn-sm btn-outline-secondary flex-fill sidebar-move-chrome-left"><i class="bi bi-arrow-left-short"></i></button>' +
            '<button type="button" class="btn btn-sm btn-outline-secondary flex-fill sidebar-move-chrome-right"><i class="bi bi-arrow-right-short"></i></button>' +
          '</div>' +
        '</div>'
      ));
    } else {
      html.push(sectionShell('Navigation block', '<p class="text-body-secondary mb-0">This block is selected. Use the move controls to reposition it.</p>'));
    }
    return html.join('');
  }

  function renderNewNavLink(isButton) {
    var templateCards = PAGE_TEMPLATES.map(function (tpl) {
      return '<button type="button" class="cbl-tpl-card sidebar-pick-template" data-tpl-key="' + escapeHtml(tpl.key) + '">' +
        '<i class="bi bi-' + escapeHtml(tpl.icon) + ' cbl-tpl-icon"></i>' +
        '<span class="cbl-tpl-name">' + escapeHtml(tpl.name) + '</span>' +
        '<span class="cbl-tpl-desc">' + escapeHtml(tpl.description) + '</span>' +
      '</button>';
    }).join('');

    var slotSelect = '<select class="form-select form-select-sm sidebar-shared-slot">' +
      '<option value="left">Left</option>' +
      '<option value="center">Center</option>' +
      '<option value="right">Right</option>' +
    '</select>';

    return '<div class="edit-sidebar-section">' +
        '<h3>Slot</h3>' +
        slotSelect +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Link to existing page</h3>' +
        '<select class="form-select form-select-sm mb-2 sidebar-link-page-picker"><option value="">Choose a page…</option></select>' +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-add-page-link" disabled>Add to navbar</button>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Custom link</h3>' +
        '<label class="form-label small mb-1">Label</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-ext-label" placeholder="e.g. Blog">' +
        '<label class="form-label small mb-1">URL</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-ext-url" placeholder="https://…">' +
        '<button type="button" class="btn btn-sm btn-outline-primary w-100 sidebar-add-ext-link">Add link</button>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Create new page</h3>' +
        '<label class="form-label small mb-1">Page title</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-new-page-title" placeholder="e.g. About Us">' +
        '<div class="cbl-tpl-grid mb-2">' + templateCards + '</div>' +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-create-page-link" disabled>Create page &amp; add to nav</button>' +
      '</div>';
  }

  function wireNewNavLink(body, isButton) {
    var selectedKey = null;

    var pagePicker = body.querySelector('.sidebar-link-page-picker');
    var addPageBtn = body.querySelector('.sidebar-add-page-link');
    if (pagePicker) {
      fetchPages(function (pages) {
        pages.forEach(function (p) {
          var opt = document.createElement('option');
          opt.value = String(p.id);
          opt.textContent = p.title + (p.published ? '' : ' (draft)');
          pagePicker.appendChild(opt);
        });
      });
      pagePicker.addEventListener('change', function () {
        if (addPageBtn) addPageBtn.disabled = !pagePicker.value;
      });
    }
    if (addPageBtn) {
      addPageBtn.addEventListener('click', function () {
        var page = (_pagesCache || []).filter(function (p) { return String(p.id) === pagePicker.value; })[0];
        if (!page) return;
        var slotEl = body.querySelector('.sidebar-shared-slot');
        var slot = slotEl ? slotEl.value : 'left';
        addPageBtn.disabled = true;
        postJson('/edit/nav-link/add/', { label: page.title, url: page.url, slot: slot, is_button: isButton ? '1' : '0' })
          .then(function (resp) {
            if (window.cblSetFocusHint) window.cblSetFocusHint({ kind: 'nav-link', id: resp.id });
            window.location.reload();
          }).catch(function (err) { addPageBtn.disabled = false; alertError(err); });
      });
    }

    body.querySelectorAll('.sidebar-pick-template').forEach(function (card) {
      card.addEventListener('click', function () {
        body.querySelectorAll('.sidebar-pick-template').forEach(function (c) { c.classList.remove('cbl-tpl-selected'); });
        card.classList.add('cbl-tpl-selected');
        selectedKey = card.dataset.tplKey;
        var titleInput = body.querySelector('.sidebar-new-page-title');
        if (titleInput && !titleInput.value.trim()) {
          var tpl = PAGE_TEMPLATES.filter(function (t) { return t.key === selectedKey; })[0];
          if (tpl) titleInput.value = tpl.name;
        }
        var createBtn = body.querySelector('.sidebar-create-page-link');
        if (createBtn) createBtn.disabled = false;
      });
    });

    var createBtn = body.querySelector('.sidebar-create-page-link');
    if (createBtn) {
      createBtn.addEventListener('click', function () {
        if (!selectedKey) return;
        var titleEl = body.querySelector('.sidebar-new-page-title');
        var slotEl  = body.querySelector('.sidebar-shared-slot');
        var title = titleEl ? titleEl.value.trim() : '';
        var slot  = slotEl  ? slotEl.value         : 'left';
        createBtn.disabled = true;
        createBtn.textContent = 'Creating…';
        postJson('/edit/nav-link/create-page/', { template_key: selectedKey, title: title, slot: slot })
          .then(function (resp) {
            if (window.cblSetFocusHint) window.cblSetFocusHint({ kind: 'nav-link', id: resp.nav_link_id });
            window.location.reload();
          }).catch(function (err) {
            createBtn.disabled = false;
            createBtn.textContent = 'Create page & add to nav';
            alertError(err);
          });
      });
    }

    var addExtBtn = body.querySelector('.sidebar-add-ext-link');
    if (addExtBtn) {
      addExtBtn.addEventListener('click', function () {
        var labelEl = body.querySelector('.sidebar-ext-label');
        var urlEl   = body.querySelector('.sidebar-ext-url');
        var slotEl  = body.querySelector('.sidebar-shared-slot');
        var label = labelEl ? labelEl.value.trim() : 'New Link';
        var url   = urlEl   ? urlEl.value.trim()   : '/';
        var slot  = slotEl  ? slotEl.value         : 'left';
        if (!label) label = 'New Link';
        if (!url)   url   = '/';
        addExtBtn.disabled = true;
        postJson('/edit/nav-link/add/', { label: label, url: url, slot: slot, is_button: isButton ? '1' : '0' })
          .then(function (resp) {
            if (window.cblSetFocusHint) window.cblSetFocusHint({ kind: 'nav-link', id: resp.id });
            window.location.reload();
          }).catch(function (err) { addExtBtn.disabled = false; alertError(err); });
      });
    }
  }

  function sectionShell(title, innerHtml) {
    return '<div class="edit-sidebar-section"><h3>' + escapeHtml(title) + '</h3>' + innerHtml + '</div>';
  }

  function badges(items) {
    return '<div class="mb-3">' + items.filter(Boolean).map(function (item) {
      return '<span class="badge text-bg-' + escapeHtml(item[1]) + ' me-1">' + escapeHtml(item[0]) + '</span>';
    }).join('') + '</div>';
  }

  function actionRow(buttons) {
    return '<div class="d-grid gap-2">' + buttons.filter(Boolean).map(function (item) {
      var action = item[0].match(/data-action="([^"]+)"/);
      return '<button type="button" class="btn btn-sm btn-' + escapeHtml(item[2]) + ' sidebar-page-action" data-action="' + escapeHtml(action ? action[1] : '') + '">' + escapeHtml(item[1]) + '</button>';
    }).join('') + '</div>';
  }

  function option(value, label, current) {
    return '<option value="' + escapeHtml(value) + '"' + (String(value) === String(current) ? ' selected' : '') + '>' + escapeHtml(label) + '</option>';
  }

  function wireBody(body, selection, page) {
    if (!selection) return;

    if (selection.kind === 'page') {
      wirePage(body, page);
      return;
    }

    if (selection.kind === 'section') {
      wireSection(body, selection.el);
      return;
    }

    if (selection.kind === 'nav-link' || selection.kind === 'nav-child') {
      wireNavLink(body, selection.el, selection.kind === 'nav-child');
      return;
    }

    if (selection.kind === 'footer-link') {
      wireFooterLink(body, selection.el);
      return;
    }

    if (selection.kind === 'footer-column') {
      wireFooterColumn(body, selection.el);
      return;
    }

    if (selection.kind === 'brand') {
      wireBrand(body, selection.el);
      return;
    }

    if (selection.kind === 'nav-block') {
      wireNavBlock(body, selection.el, selection.blockKind);
      return;
    }

    if (selection.kind === 'navbar') {
      wireNavbar(body);
      return;
    }

    if (selection.kind === 'nav-zone') {
      wireNavZone(body);
      return;
    }

    if (selection.kind === 'footer') {
      wireFooter(body);
      return;
    }

    if (selection.kind === 'item') {
      wireItem(body, selection.itemId);
    }
  }

  function wirePage(body, page) {
    wireColorFields(body);
    var bind = function (selector, fn) {
      var el = body.querySelector(selector);
      if (el) el.addEventListener('click', fn);
    };
    bind('.sidebar-page-action[data-action="publish"]', function () {
      postJson('/edit/page/' + page.id + '/publish/').then(function () { window.location.reload(); }).catch(alertError);
    });
    bind('.sidebar-page-action[data-action="unpublish"]', function () {
      postJson('/edit/page/' + page.id + '/unpublish/').then(function () { window.location.reload(); }).catch(alertError);
    });
    bind('.sidebar-page-action[data-action="add-nav"]', function () {
      postJson('/edit/page/' + page.id + '/add-to-navbar/').then(function () { window.location.reload(); }).catch(alertError);
    });
    bind('.sidebar-page-action[data-action="remove-nav"]', function () {
      postJson('/edit/page/' + page.id + '/remove-from-navbar/').then(function () { window.location.reload(); }).catch(alertError);
    });
    bind('.sidebar-page-action[data-action="add-footer"]', function () {
      postJson('/edit/page/' + page.id + '/add-to-footer/').then(function () { window.location.reload(); }).catch(alertError);
    });
    bind('.sidebar-delete-page', function () {
      if (!confirm('Permanently delete this page and all its content?')) return;
      postJson('/edit/page/' + page.id + '/delete/')
        .then(function () { window.location.href = '/'; })
        .catch(alertError);
    });

    var saveSeo = body.querySelector('.sidebar-save-seo');
    if (saveSeo) {
      saveSeo.addEventListener('click', function () {
        var titleEl   = body.querySelector('.sidebar-seo-title');
        var ogTitleEl = body.querySelector('.sidebar-seo-og-title');
        var ogDescEl  = body.querySelector('.sidebar-seo-og-desc');
        postJson('/edit/page/' + page.id + '/field/title/',          { value: titleEl   ? titleEl.value   : '' })
          .then(function () { return postJson('/edit/page/' + page.id + '/field/og_title/',       { value: ogTitleEl ? ogTitleEl.value : '' }); })
          .then(function () { return postJson('/edit/page/' + page.id + '/field/og_description/', { value: ogDescEl  ? ogDescEl.value  : '' }); })
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }

    var pagesList = body.querySelector('.sidebar-pages-list');
    if (pagesList) {
      fetchPages(function (pages) {
        if (!pages.length) { pagesList.innerHTML = '<p class="small text-body-secondary mb-0">No pages found.</p>'; return; }
        pagesList.innerHTML = '';
        pages.forEach(function (p) {
          var isCurrent = page && p.slug === page.slug;
          var a = document.createElement('a');
          a.href = p.url;
          a.className = 'd-flex align-items-center gap-1 text-decoration-none py-1 border-bottom small ' + (isCurrent ? 'fw-semibold text-body' : 'text-body-secondary');
          a.innerHTML = escapeHtml(p.title || p.slug) +
            '<span class="badge text-bg-' + (p.published ? 'success' : 'secondary') + ' ms-auto">' +
            (p.published ? 'Live' : 'Draft') + '</span>';
          pagesList.appendChild(a);
        });
      });
    }
    var newPageBtn = body.querySelector('.sidebar-new-page-btn');
    if (newPageBtn) {
      newPageBtn.addEventListener('click', function () {
        if (typeof window.cblShowNewNavLinkPanel === 'function') window.cblShowNewNavLinkPanel(false);
      });
    }

    var savePageDesign = body.querySelector('.sidebar-save-page-design');
    if (savePageDesign) {
      savePageDesign.addEventListener('click', function () {
        var spacing = body.querySelector('.sidebar-section-spacing');
        var bgInput = body.querySelector('.sidebar-body-bg');
        postJson('/edit/navbar/config/update/', { key: 'section_spacing', value: spacing ? spacing.value : 'normal' })
          .then(function () { return postJson('/edit/navbar/config/update/', { key: 'body_bg_override', value: bgInput ? bgInput.value.trim() : '' }); })
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }

    var swatchContainer = body.querySelector('.sidebar-theme-swatches');
    if (swatchContainer) {
      var currentThemeId = String(document.body.dataset.siteThemeId || '');
      fetchThemes(function (themes) {
        if (!themes.length) {
          swatchContainer.innerHTML = '<span class="small text-body-secondary">No themes found.</span>';
          return;
        }
        swatchContainer.innerHTML = '';
        themes.forEach(function (t) {
          var btn = document.createElement('button');
          btn.type = 'button';
          btn.title = t.name;
          btn.dataset.themeId = String(t.id);
          var isCurrent = String(t.id) === currentThemeId;
          btn.style.cssText = 'width:28px;height:28px;border-radius:50%;background:' + escapeHtml(t.primary) +
            ';border:3px solid ' + (isCurrent ? '#000' : 'transparent') + ';cursor:pointer;outline:none;transition:border-color .15s;';
          btn.addEventListener('mouseenter', function () { if (!isCurrent) btn.style.borderColor = '#999'; });
          btn.addEventListener('mouseleave', function () { if (!isCurrent) btn.style.borderColor = 'transparent'; });
          btn.addEventListener('click', function () {
            postJson('/edit/site/theme/set/', { theme_id: String(t.id) })
              .then(function () { window.location.reload(); })
              .catch(alertError);
          });
          var label = document.createElement('span');
          label.className = 'visually-hidden';
          label.textContent = t.name;
          btn.appendChild(label);
          swatchContainer.appendChild(btn);
        });
      });
    }

    var packsList = body.querySelector('.sidebar-packs-list');
    if (packsList) {
      fetchPacks(function (data) {
        if (!data || !data.packs || !data.packs.length) {
          packsList.innerHTML = '<span class="small text-body-secondary">No templates available.</span>';
          return;
        }
        packsList.innerHTML = '';
        data.packs.forEach(function (pack) {
          var isCurrent = pack.is_current;
          var card = document.createElement('div');
          card.className = 'border rounded p-2 mb-2' + (isCurrent ? ' border-primary bg-primary-subtle' : '');
          card.innerHTML =
            '<div class="d-flex justify-content-between align-items-start gap-2">' +
              '<div>' +
                '<div class="small fw-semibold">' + escapeHtml(pack.name) + (isCurrent ? ' <span class="badge text-bg-primary ms-1">Active</span>' : '') + '</div>' +
                '<div class="small text-body-secondary">' + escapeHtml(pack.description) + '</div>' +
              '</div>' +
              (!isCurrent ? '<button type="button" class="btn btn-outline-secondary btn-sm flex-shrink-0 sidebar-apply-pack" data-pack-key="' + escapeHtml(pack.key) + '">Apply</button>' : '') +
            '</div>';
          if (!isCurrent) {
            card.querySelector('.sidebar-apply-pack').addEventListener('click', function () {
              if (!confirm('Apply the "' + pack.name + '" template?\n\nThis will replace all your pages and content with the template starter. Your site name and theme will also be updated.\n\nThis cannot be undone.')) return;
              postJson('/edit/site/pack/apply/', { pack_key: pack.key })
                .then(function () { window.location.reload(); })
                .catch(alertError);
            });
          }
          packsList.appendChild(card);
        });
      });
    }
  }

  function wireSection(body, sectionEl) {
    var sectionId = sectionEl.dataset.sectionId;

    var uploadImgBtn = body.querySelector('.sidebar-upload-section-img');
    var imgFile      = body.querySelector('.sidebar-section-img-file');
    var removeImgBtn = body.querySelector('.sidebar-remove-section-img');
    var imgStatus    = body.querySelector('.sidebar-section-img-status');

    if (uploadImgBtn && imgFile) {
      uploadImgBtn.addEventListener('click', function () { imgFile.click(); });
      imgFile.addEventListener('change', function () {
        if (!imgFile.files || !imgFile.files.length) return;
        var fd = new FormData();
        fd.append('image', imgFile.files[0]);
        uploadImgBtn.disabled = true;
        uploadImgBtn.textContent = 'Uploading…';
        fetch('/edit/section/' + sectionId + '/image/', {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'X-CSRFToken': getCsrf() },
          body: fd,
        })
          .then(function (r) { return r.json().catch(function () { throw new Error('Server error (' + r.status + ')'); }); })
          .then(function (d) {
            if (d.success) { window.location.reload(); }
            else { throw new Error(d.error || 'Upload failed'); }
          })
          .catch(function (err) {
            if (imgStatus) imgStatus.textContent = err.message || 'Upload failed';
            uploadImgBtn.disabled = false;
            uploadImgBtn.textContent = 'Upload image';
          });
      });
    }
    if (removeImgBtn) {
      removeImgBtn.addEventListener('click', function () {
        if (!confirm('Remove the section image?')) return;
        postJson('/edit/section/' + sectionId + '/image/remove/')
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }

    wireColorFields(body);
    wireRichToolbar(body);

    var saveContent = body.querySelector('.sidebar-save-content');
    if (saveContent) {
      saveContent.addEventListener('click', function () {
        var heading = body.querySelector('.sidebar-section-heading');
        var subheadingVal = getEditorContent(body, '.sidebar-section-subheading');
        var req = postJson('/edit/section/' + sectionId + '/field/heading/', { value: heading ? heading.value : '' });
        req = req.then(function () {
          return postJson('/edit/section/' + sectionId + '/field/subheading/', { value: subheadingVal });
        });
        req.then(function () { window.location.reload(); }).catch(alertError);
      });
    }

    var saveDisplay = body.querySelector('.sidebar-save-display');
    if (saveDisplay) {
      saveDisplay.addEventListener('click', function () {
        var layout  = body.querySelector('.sidebar-section-layout');
        var columns = body.querySelector('.sidebar-section-columns');
        var bg      = body.querySelector('.sidebar-section-bg');
        var padTop  = body.querySelector('.sidebar-section-pad-top');
        var padBot  = body.querySelector('.sidebar-section-pad-bot');
        var padLeft = body.querySelector('.sidebar-section-pad-left');
        var padRight= body.querySelector('.sidebar-section-pad-right');
        var marTop  = body.querySelector('.sidebar-section-mar-top');
        var marBot  = body.querySelector('.sidebar-section-mar-bot');
        var bStyle  = body.querySelector('.sidebar-section-border-style');
        var bWidth  = body.querySelector('.sidebar-section-border-width');
        var bColor  = body.querySelector('.sidebar-section-border-color');
        var bRadius = body.querySelector('.sidebar-section-border-radius');
        var iStyle  = body.querySelector('.sidebar-section-item-style-group input[type="radio"]:checked');
        var req = postJson('/edit/section/' + sectionId + '/layout/', { layout: layout ? layout.value : '' });
        var configPayload = {};
        if (columns) configPayload.columns_desktop  = columns.value;
        if (bg)      configPayload.background_color = bg.value;
        if (padTop)  configPayload.padding_top       = padTop.value;
        if (padBot)  configPayload.padding_bottom    = padBot.value;
        if (padLeft) configPayload.padding_left      = padLeft.value;
        if (padRight)configPayload.padding_right     = padRight.value;
        if (marTop)  configPayload.margin_top        = marTop.value;
        if (marBot)  configPayload.margin_bottom     = marBot.value;
        if (bStyle)  configPayload.border_style      = bStyle.value;
        if (bWidth)  configPayload.border_width      = bWidth.value;
        if (bColor)  configPayload.border_color      = bColor.value;
        if (bRadius) configPayload.border_radius     = bRadius.value;
        if (iStyle)  configPayload.item_style        = iStyle.value;
        if (Object.keys(configPayload).length) {
          req = req.then(function () {
            return postJson('/edit/section/' + sectionId + '/config/', configPayload);
          });
        }
        req.then(function () { window.location.reload(); }).catch(alertError);
      });
    }

    var toggle = body.querySelector('.sidebar-toggle-section');
    if (toggle) {
      toggle.addEventListener('click', function () {
        postJson('/edit/section/' + sectionId + '/visibility/')
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }

    body.querySelectorAll('.sidebar-add-item').forEach(function (addItem) {
      addItem.addEventListener('click', function () {
        var body_ = addItem.dataset.itemType ? { item_type: addItem.dataset.itemType } : null;
        postJson('/edit/section/' + sectionId + '/item/add/', body_)
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    });

    var del = body.querySelector('.sidebar-delete-section');
    if (del) {
      del.addEventListener('click', function () {
        if (!confirm('Delete this section?')) return;
        postJson('/edit/section/' + sectionId + '/delete/')
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }
  }

  var _pagesCache = null;

  function fetchPages(cb) {
    if (_pagesCache) { cb(_pagesCache); return; }
    fetch('/edit/pages/list/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (d) { _pagesCache = d.pages || []; cb(_pagesCache); })
      .catch(function () { cb([]); });
  }

  var _themesCache = null;

  function fetchThemes(cb) {
    if (_themesCache) { cb(_themesCache); return; }
    fetch('/edit/site/themes/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (d) { _themesCache = d.themes || []; cb(_themesCache); })
      .catch(function () { cb([]); });
  }

  var _packsCache = null;

  function fetchPacks(cb) {
    if (_packsCache) { cb(_packsCache); return; }
    fetch('/edit/site/packs/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (d) { _packsCache = d; cb(_packsCache); })
      .catch(function () { cb(null); });
  }

  function wireNavLink(body, li, child) {
    var id = li.dataset.navlinkId;
    var currentPageId = li.dataset.navlinkPageId || '';
    var label = body.querySelector('.sidebar-nav-label');
    var url = body.querySelector('.sidebar-nav-url');
    var picker = body.querySelector('.sidebar-page-picker');
    var newTab = body.querySelector('.sidebar-nav-newtab');
    var visible = body.querySelector('.sidebar-nav-visible');
    var button = body.querySelector('.sidebar-nav-button');
    var save = body.querySelector('.sidebar-save-nav');
    var left = body.querySelector('.sidebar-move-left');
    var right = body.querySelector('.sidebar-move-right');
    var addChild = body.querySelector('.sidebar-add-child');
    var del = body.querySelector('.sidebar-delete-nav');

    if (picker && url) {
      fetchPages(function (pages) {
        pages.forEach(function (p) {
          var opt = document.createElement('option');
          opt.value = String(p.id);
          opt.textContent = p.title + (p.published ? '' : ' (draft)');
          if (String(p.id) === currentPageId) {
            opt.selected = true;
            url.readOnly = true;
            url.classList.add('text-body-secondary');
          }
          picker.appendChild(opt);
        });
      });
      picker.addEventListener('change', function () {
        if (!picker.value) {
          url.readOnly = false;
          url.classList.remove('text-body-secondary');
          url.focus();
        } else {
          var page = (_pagesCache || []).filter(function (p) { return String(p.id) === picker.value; })[0];
          if (page) {
            url.value = page.url;
            url.readOnly = true;
            url.classList.add('text-body-secondary');
          }
        }
      });
    }

    if (save) {
      save.addEventListener('click', function () {
        var selectedPageId = picker ? picker.value : '';
        var req = postJson('/edit/nav-link/' + id + '/update/', { field: 'label', value: label ? label.value : '' });
        if (selectedPageId) {
          req = req.then(function () {
            return postJson('/edit/nav-link/' + id + '/update/', { field: 'page_id', value: selectedPageId });
          });
        } else {
          req = req.then(function () {
            return postJson('/edit/nav-link/' + id + '/update/', { field: 'url', value: url ? url.value : '' });
          });
        }
        if (newTab) {
          req = req.then(function () {
            return postJson('/edit/nav-link/' + id + '/update/', { field: 'open_new_tab', value: newTab.checked ? '1' : '0' });
          });
        }
        if (!child) {
          if (button) {
            req = req.then(function () {
              return postJson('/edit/nav-link/' + id + '/update/', { field: 'is_button', value: button.checked ? '1' : '0' });
            });
          }
          if (visible) {
            req = req.then(function () {
              return postJson('/edit/nav-link/' + id + '/update/', { field: 'is_visible', value: visible.checked ? '1' : '0' });
            });
          }
          var marLeft  = body.querySelector('.sidebar-nav-margin-left');
          var marRight = body.querySelector('.sidebar-nav-margin-right');
          if (marLeft) {
            req = req.then(function () {
              return postJson('/edit/nav-link/' + id + '/update/', { field: 'margin_left', value: marLeft.value || '0' });
            });
          }
          if (marRight) {
            req = req.then(function () {
              return postJson('/edit/nav-link/' + id + '/update/', { field: 'margin_right', value: marRight.value || '0' });
            });
          }
        }
        req.then(function () { window.location.reload(); }).catch(alertError);
      });
    }

    if (left) {
      left.addEventListener('click', function () { moveNavLinkBy(id, li, -1); });
    }
    if (right) {
      right.addEventListener('click', function () { moveNavLinkBy(id, li, 1); });
    }
    if (addChild) {
      addChild.addEventListener('click', function () {
        postJson('/edit/nav-link/add/', { label: 'New item', url: '/', parent_id: id, slot: li.dataset.navlinkSlot || 'left' })
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }
    if (del) {
      del.addEventListener('click', function () {
        postJson('/edit/nav-link/' + id + '/delete/')
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }
  }

  function moveNavLinkBy(id, li, delta) {
    var order = ['left', 'center', 'right'];
    var current = (li.dataset.navlinkSlot || 'left').toLowerCase();
    var index = order.indexOf(current);
    if (index < 0) index = 0;
    var next = order[index + delta];
    if (!next) return;
    postJson('/edit/nav-link/' + id + '/update/', { field: 'slot', value: next })
      .then(function () { window.location.reload(); })
      .catch(alertError);
  }

  function wireFooterLink(body, li) {
    var id      = li.dataset.footerlinkId;
    var pageId  = li.dataset.footerlinkPageId || '';
    var label   = body.querySelector('.sidebar-footer-label');
    var url     = body.querySelector('.sidebar-footer-url');
    var picker  = body.querySelector('.sidebar-footer-page-picker');
    var newTab  = body.querySelector('.sidebar-footer-newtab');
    var visible = body.querySelector('.sidebar-footer-visible');
    var save    = body.querySelector('.sidebar-save-footer-link');
    var del     = body.querySelector('.sidebar-delete-footer-link');

    if (picker && url) {
      fetchPages(function (pages) {
        pages.forEach(function (p) {
          var opt = document.createElement('option');
          opt.value = String(p.id);
          opt.textContent = p.title + (p.published ? '' : ' (draft)');
          if (String(p.id) === pageId) {
            opt.selected = true;
            url.readOnly = true;
            url.classList.add('text-body-secondary');
          }
          picker.appendChild(opt);
        });
      });
      picker.addEventListener('change', function () {
        if (!picker.value) {
          url.readOnly = false;
          url.classList.remove('text-body-secondary');
          url.focus();
        } else {
          var page = (_pagesCache || []).filter(function (p) { return String(p.id) === picker.value; })[0];
          if (page) { url.value = page.url; url.readOnly = true; url.classList.add('text-body-secondary'); }
        }
      });
    }

    if (save) {
      save.addEventListener('click', function () {
        var selectedPageId = picker ? picker.value : '';
        var req = postJson('/edit/footer-link/' + id + '/update/', { field: 'label', value: label ? label.value : '' });
        if (selectedPageId) {
          req = req.then(function () {
            return postJson('/edit/footer-link/' + id + '/update/', { field: 'page_id', value: selectedPageId });
          });
        } else {
          req = req.then(function () {
            return postJson('/edit/footer-link/' + id + '/update/', { field: 'url', value: url ? url.value : '' });
          });
        }
        req = req
          .then(function () { return postJson('/edit/footer-link/' + id + '/update/', { field: 'open_new_tab', value: newTab && newTab.checked ? '1' : '0' }); })
          .then(function () { return postJson('/edit/footer-link/' + id + '/update/', { field: 'is_visible',   value: visible && visible.checked ? '1' : '0' }); });
        req.then(function () { window.location.reload(); }).catch(alertError);
      });
    }
    if (del) {
      del.addEventListener('click', function () {
        postJson('/edit/footer-link/' + id + '/delete/')
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }
  }

  function wireFooterColumn(body, col) {
    var id = col.dataset.footercolId;
    var heading = body.querySelector('.sidebar-footer-heading');
    var visible = body.querySelector('.sidebar-footer-visible');
    var save = body.querySelector('.sidebar-save-footer-column');
    var add = body.querySelector('.sidebar-add-footer-link');
    var del = body.querySelector('.sidebar-delete-footer-column');

    if (save) {
      save.addEventListener('click', function () {
        postJson('/edit/footer-column/' + id + '/update/', { field: 'heading', value: heading ? heading.value : '' })
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }
    if (visible) {
      visible.addEventListener('change', function () {
        postJson('/edit/footer-column/' + id + '/update/', { field: 'is_visible', value: visible.checked ? '1' : '0' })
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }
    if (add) {
      add.addEventListener('click', function () {
        postJson('/edit/footer-column/' + id + '/link/add/', { label: 'New Link', url: '/' })
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }

    body.querySelectorAll('.sidebar-quick-footer-link').forEach(function (btn) {
      btn.addEventListener('click', function () {
        btn.disabled = true;
        postJson('/edit/footer-column/' + id + '/link/add/', {
          label: btn.dataset.label,
          url: btn.dataset.url,
        }).then(function () { window.location.reload(); })
          .catch(function (err) { btn.disabled = false; alertError(err); });
      });
    });

    if (del) {
      del.addEventListener('click', function () {
        if (!confirm('Delete this column and all its links?')) return;
        postJson('/edit/footer-column/' + id + '/delete/')
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }
  }

  function wireBrand(body, brand) {
    var uploadBtn  = body.querySelector('.sidebar-upload-logo');
    var removeBtn  = body.querySelector('.sidebar-remove-logo');
    var fileInput  = body.querySelector('.sidebar-brand-logo-file');
    var logoStatus = body.querySelector('.sidebar-logo-status');

    if (uploadBtn && fileInput) {
      uploadBtn.addEventListener('click', function () { fileInput.click(); });
      fileInput.addEventListener('change', function () {
        if (!fileInput.files || !fileInput.files.length) return;
        var formData = new FormData();
        formData.append('image', fileInput.files[0]);
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading…';
        fetch('/edit/site-logo/upload/', {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'X-CSRFToken': getCsrf() },
          body: formData,
        })
          .then(function (r) {
            return r.json().catch(function () {
              throw new Error('Server error (' + r.status + ') - check the Django terminal');
            });
          })
          .then(function (d) {
            if (d.success) { window.location.reload(); }
            else { throw new Error(d.error || 'Upload failed'); }
          })
          .catch(function (err) {
            if (logoStatus) logoStatus.textContent = err.message || 'Upload failed';
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload logo';
          });
      });
    }

    if (removeBtn) {
      removeBtn.addEventListener('click', function () {
        if (!confirm('Remove the logo?')) return;
        postJson('/edit/site-logo/remove/')
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }

    var save = body.querySelector('.sidebar-save-brand');
    if (!save) return;
    save.addEventListener('click', function () {
      var name       = body.querySelector('.sidebar-brand-name');
      var position   = body.querySelector('.sidebar-brand-position');
      var showLogo   = body.querySelector('.sidebar-brand-show-logo');
      var showName   = body.querySelector('.sidebar-brand-show-name');
      var logoHeight = body.querySelector('.sidebar-brand-logo-height');
      postJson('/edit/site-brand/update/', { field: 'name',             value: name       ? name.value       : '' })
        .then(function () { return postJson('/edit/site-brand/update/', { field: 'brand_position',  value: position   ? position.value   : 'left' }); })
        .then(function () { return postJson('/edit/site-brand/update/', { field: 'show_brand_logo', value: showLogo && showLogo.checked ? '1' : '0' }); })
        .then(function () { return postJson('/edit/site-brand/update/', { field: 'show_brand_name', value: showName && showName.checked ? '1' : '0' }); })
        .then(function () { return postJson('/edit/site-brand/update/', { field: 'brand_logo_height', value: logoHeight ? logoHeight.value : '32' }); })
        .then(function () { window.location.reload(); })
        .catch(alertError);
    });
  }

  function wireNavBlock(body, block, kind) {
    kind = (kind || '').toLowerCase();
    var left = body.querySelector('.sidebar-move-chrome-left');
    var right = body.querySelector('.sidebar-move-chrome-right');
    if (left) {
      left.addEventListener('click', function () { moveChromeSlot(kind, -1); });
    }
    if (right) {
      right.addEventListener('click', function () { moveChromeSlot(kind, 1); });
    }

    if (kind === 'search') {
      var toggle = body.querySelector('.sidebar-toggle-chrome');
      if (toggle) {
        toggle.addEventListener('click', function () {
          postJson('/edit/site-chrome/update/', { field: 'show_nav_search', value: '0' })
            .then(function () { window.location.reload(); })
            .catch(alertError);
        });
      }
    }

    if (kind === 'cta') {
      var save = body.querySelector('.sidebar-save-cta');
      if (save) {
        save.addEventListener('click', function () {
          var label = body.querySelector('.sidebar-cta-label');
          var url = body.querySelector('.sidebar-cta-url');
          postJson('/edit/site-chrome/update/', { field: 'nav_cta_label', value: label ? label.value : '' })
            .then(function () { return postJson('/edit/site-chrome/update/', { field: 'nav_cta_url', value: url ? url.value : '' }); })
            .then(function () { window.location.reload(); })
            .catch(alertError);
        });
      }
    }

    if (kind === 'auth') {
      var saveAuth = body.querySelector('.sidebar-save-auth');
      if (saveAuth) {
        saveAuth.addEventListener('click', function () {
          var reg = body.querySelector('.sidebar-auth-register');
          postJson('/edit/site-chrome/update/', { field: 'show_nav_login', value: '1' })
            .then(function () { return postJson('/edit/site-chrome/update/', { field: 'show_nav_register', value: reg && reg.checked ? '1' : '0' }); })
            .then(function () { return postJson('/edit/site-chrome/update/', { field: 'show_nav_profile', value: '1' }); })
            .then(function () { window.location.reload(); })
            .catch(alertError);
        });
      }
    }
  }

  function moveChromeSlot(kind, delta) {
    var field = null;
    if (kind === 'search') field = 'nav_search_slot';
    else if (kind === 'cta') field = 'nav_cta_slot';
    else if (kind === 'auth') field = 'nav_auth_slot';
    if (!field) return;

    var block = document.querySelector('[data-chrome-slot-field="' + field + '"]');
    if (!block) return;
    var current = (block.dataset.chromeSlotValue || 'left').toLowerCase();
    var order = ['left', 'center', 'right'];
    var index = order.indexOf(current);
    if (index < 0) index = 0;
    var next = order[index + delta];
    if (!next) return;
    postJson('/edit/site-chrome/update/', { field: field, value: next })
      .then(function () { window.location.reload(); })
      .catch(alertError);
  }

  function renderNavZone(zoneName) {
    var r = document.getElementById('navbar-region');
    var rawL = r ? (r.dataset.navZoneLeft   || '') : '';
    var rawC = r ? (r.dataset.navZoneCenter || '') : '';
    var rawR = r ? (r.dataset.navZoneRight  || '') : '';

    function frVal(raw, def) {
      return raw ? parseFloat(raw) : def;
    }
    var leftVal   = frVal(rawL, 1);
    var centerVal = frVal(rawC, 2);
    var rightVal  = frVal(rawR, 1);
    var hasCustom = !!(rawL || rawC || rawR);

    var zoneLabels = { left: 'Left zone', center: 'Center zone', right: 'Right zone' };

    return sectionShell(zoneLabels[zoneName] || 'Zone',
      '<div class="edit-sidebar-section">' +
        '<h3>Quick presets</h3>' +
        '<div class="d-flex gap-1 flex-wrap mb-3">' +
          '<button type="button" class="btn btn-sm btn-outline-secondary sidebar-zone-reset-inline">Auto (default)</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary sidebar-zone-preset" data-l="1" data-c="2" data-r="1">Center heavy</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary sidebar-zone-preset" data-l="1" data-c="1" data-r="1">Equal thirds</button>' +
        '</div>' +
        '<h3>Custom widths <span class="text-body-secondary">(fr units)</span></h3>' +
        '<p class="small text-body-secondary mb-2">Higher number = wider zone. All three values are relative to each other.</p>' +
        '<div class="d-flex gap-2 mb-3">' +
          '<div class="text-center flex-fill">' +
            '<label class="form-label small mb-1 d-block fw-semibold' + (zoneName === 'left' ? ' text-primary' : '') + '">Left</label>' +
            '<input type="number" class="form-control form-control-sm sidebar-zone-left-fr" min="0.5" max="20" step="0.5" value="' + leftVal + '">' +
          '</div>' +
          '<div class="text-center flex-fill">' +
            '<label class="form-label small mb-1 d-block fw-semibold' + (zoneName === 'center' ? ' text-primary' : '') + '">Center</label>' +
            '<input type="number" class="form-control form-control-sm sidebar-zone-center-fr" min="0.5" max="20" step="0.5" value="' + centerVal + '">' +
          '</div>' +
          '<div class="text-center flex-fill">' +
            '<label class="form-label small mb-1 d-block fw-semibold' + (zoneName === 'right' ? ' text-primary' : '') + '">Right</label>' +
            '<input type="number" class="form-control form-control-sm sidebar-zone-right-fr" min="0.5" max="20" step="0.5" value="' + rightVal + '">' +
          '</div>' +
        '</div>' +
        '<button type="button" class="btn btn-sm btn-primary w-100 mb-1 sidebar-save-zone">Apply</button>' +
        '<button type="button" class="btn btn-sm btn-link w-100 sidebar-reset-zone">Reset to auto (default)</button>' +
      '</div>'
    );
  }

  function wireNavZone(body) {
    function doReset() {
      postJson('/edit/navbar/config/update/', { key: 'zone_left_fr',   value: '' })
        .then(function () { return postJson('/edit/navbar/config/update/', { key: 'zone_center_fr', value: '' }); })
        .then(function () { return postJson('/edit/navbar/config/update/', { key: 'zone_right_fr',  value: '' }); })
        .then(function () { window.location.reload(); })
        .catch(alertError);
    }

    body.querySelectorAll('.sidebar-zone-preset').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var leftEl   = body.querySelector('.sidebar-zone-left-fr');
        var centerEl = body.querySelector('.sidebar-zone-center-fr');
        var rightEl  = body.querySelector('.sidebar-zone-right-fr');
        if (leftEl)   leftEl.value   = btn.dataset.l || '1';
        if (centerEl) centerEl.value = btn.dataset.c || '1';
        if (rightEl)  rightEl.value  = btn.dataset.r || '1';
      });
    });

    var resetInline = body.querySelector('.sidebar-zone-reset-inline');
    if (resetInline) resetInline.addEventListener('click', doReset);

    var save = body.querySelector('.sidebar-save-zone');
    if (save) {
      save.addEventListener('click', function () {
        var leftEl   = body.querySelector('.sidebar-zone-left-fr');
        var centerEl = body.querySelector('.sidebar-zone-center-fr');
        var rightEl  = body.querySelector('.sidebar-zone-right-fr');
        var lv = leftEl   ? leftEl.value.trim()   : '';
        var cv = centerEl ? centerEl.value.trim() : '';
        var rv = rightEl  ? rightEl.value.trim()  : '';
        if (!lv || !cv || !rv) { alertError({ message: 'All three zone widths are required.' }); return; }
        postJson('/edit/navbar/config/update/', { key: 'zone_left_fr',   value: lv + 'fr' })
          .then(function () { return postJson('/edit/navbar/config/update/', { key: 'zone_center_fr', value: cv + 'fr' }); })
          .then(function () { return postJson('/edit/navbar/config/update/', { key: 'zone_right_fr',  value: rv + 'fr' }); })
          .then(function () { window.location.reload(); })
          .catch(alertError);
      });
    }

    var reset = body.querySelector('.sidebar-reset-zone');
    if (reset) reset.addEventListener('click', doReset);
  }

  function renderNavbar() {
    var r = document.getElementById('navbar-region');
    var theme     = r ? (r.dataset.navTheme     || 'light')     : 'light';
    var sticky    = r ? r.dataset.navSticky      === '1'        : false;
    var shadow    = r ? r.dataset.navShadow      === '1'        : true;
    var container = r ? (r.dataset.navContainer  || 'container'): 'container';
    var height    = r ? (r.dataset.navHeight     || '76')       : '76';
    var padY      = r ? (r.dataset.navPadY       || '0.4')      : '0.4';
    var gap       = r ? (r.dataset.navGap        || '12')       : '12';
    var bg        = r ? (r.dataset.navBg         || '')         : '';
    var textCol   = r ? (r.dataset.navTextColor  || '')         : '';
    var linkCol   = r ? (r.dataset.navLinkColor  || '')         : '';
    var linkStyle    = r ? (r.dataset.navLinkStyle    || 'pill')     : 'pill';
    var mobileStyle    = r ? (r.dataset.navMobileStyle    || 'collapse') : 'collapse';
    var scrollEffect   = r ? (r.dataset.navScrollEffect   || 'none')    : 'none';
    var dropdownStyle  = r ? (r.dataset.navDropdownStyle  || 'default') : 'default';
    var menuOverflow   = r ? (r.dataset.navOverflow        || 'visible') : 'visible';

    function themeOpt(val, label) {
      return '<option value="' + val + '"' + (theme === val ? ' selected' : '') + '>' + label + '</option>';
    }
    function styleOpt(val, label) {
      return '<option value="' + val + '"' + (linkStyle === val ? ' selected' : '') + '>' + label + '</option>';
    }

    return '<div class="edit-sidebar-section">' +
        '<h3>Style</h3>' +
        '<label class="form-label small mb-1">Theme</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-navbar-theme">' +
          themeOpt('light',       'Light') +
          themeOpt('dark',        'Dark') +
          themeOpt('primary',     'Brand color') +
          themeOpt('transparent', 'Transparent') +
        '</select>' +
        '<label class="form-label small mb-1">Link style</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-navbar-link-style">' +
          styleOpt('pill',      'Pill') +
          styleOpt('underline', 'Underline') +
          styleOpt('plain',     'Plain') +
        '</select>' +
        renderColorField('sidebar-navbar-bg', bg, 'Background (overrides theme)') +
        renderColorField('sidebar-navbar-text-color', textCol, 'Text color (overrides theme)') +
        renderColorField('sidebar-navbar-link-color', linkCol, 'Link color (overrides theme)') +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Layout</h3>' +
        '<label class="form-label small mb-1">Height (px)</label>' +
        '<input type="number" class="form-control form-control-sm mb-2 sidebar-navbar-height" value="' + escapeHtml(height) + '" min="48" max="180">' +
        '<div class="d-flex gap-2 mb-2">' +
          '<div class="flex-fill">' +
            '<label class="form-label small mb-1">Vertical padding (rem)</label>' +
            '<input type="number" class="form-control form-control-sm sidebar-navbar-pad-y" value="' + escapeHtml(padY) + '" min="0" max="3" step="0.1">' +
          '</div>' +
          '<div class="flex-fill">' +
            '<label class="form-label small mb-1">Item spacing (px)</label>' +
            '<input type="number" class="form-control form-control-sm sidebar-navbar-gap" value="' + escapeHtml(gap) + '" min="0" max="64">' +
          '</div>' +
        '</div>' +
        '<label class="form-label small mb-1">Width</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-navbar-container">' +
          '<option value="container"' + (container === 'container' ? ' selected' : '') + '>Contained</option>' +
          '<option value="container-fluid"' + (container === 'container-fluid' ? ' selected' : '') + '>Full width</option>' +
        '</select>' +
        '<label class="form-label small mb-1">Mobile menu</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-navbar-mobile">' +
          '<option value="collapse"' + (mobileStyle === 'collapse' ? ' selected' : '') + '>Collapse (accordion)</option>' +
          '<option value="offcanvas"' + (mobileStyle === 'offcanvas' ? ' selected' : '') + '>Offcanvas drawer</option>' +
        '</select>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Options</h3>' +
        '<div class="form-check mb-1">' +
          '<input class="form-check-input sidebar-navbar-sticky" type="checkbox" id="sna-sticky"' + (sticky ? ' checked' : '') + '>' +
          '<label class="form-check-label small" for="sna-sticky">Sticky (stays at top while scrolling)</label>' +
        '</div>' +
        '<div class="form-check mb-1">' +
          '<input class="form-check-input sidebar-navbar-shadow" type="checkbox" id="sna-shadow"' + (shadow ? ' checked' : '') + '>' +
          '<label class="form-check-label small" for="sna-shadow">Drop shadow</label>' +
        '</div>' +
        '<label class="form-label small mb-1">Scroll effect</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-navbar-scroll-effect">' +
          '<option value="none"'    + (scrollEffect === 'none'    ? ' selected' : '') + '>None</option>' +
          '<option value="fade-in"' + (scrollEffect === 'fade-in' ? ' selected' : '') + '>Transparent → solid on scroll</option>' +
        '</select>' +
        '<label class="form-label small mb-1">Dropdown style</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-navbar-dropdown-style">' +
          '<option value="default"'  + (dropdownStyle === 'default'  ? ' selected' : '') + '>Default (white + shadow)</option>' +
          '<option value="bordered"' + (dropdownStyle === 'bordered' ? ' selected' : '') + '>Bordered (no shadow)</option>' +
          '<option value="dark"'     + (dropdownStyle === 'dark'     ? ' selected' : '') + '>Dark</option>' +
          '<option value="branded"'  + (dropdownStyle === 'branded'  ? ' selected' : '') + '>Branded (primary color)</option>' +
        '</select>' +
        '<label class="form-label small mb-1">Menu overflow</label>' +
        '<select class="form-select form-select-sm mb-3 sidebar-navbar-menu-overflow">' +
          '<option value="visible"'    + (menuOverflow === 'visible'    ? ' selected' : '') + '>Visible (no limit)</option>' +
          '<option value="more-menu"'  + (menuOverflow === 'more-menu'  ? ' selected' : '') + '>More ▼ (auto-hide overflow)</option>' +
          '<option value="second-row"' + (menuOverflow === 'second-row' ? ' selected' : '') + '>Second row</option>' +
        '</select>' +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-navbar">Save</button>' +
      '</div>';
  }

  function wireNavbar(body) {
    wireColorFields(body);
    var save = body.querySelector('.sidebar-save-navbar');
    if (!save) return;
    save.addEventListener('click', function () {
      var theme        = body.querySelector('.sidebar-navbar-theme');
      var linkStyle    = body.querySelector('.sidebar-navbar-link-style');
      var bg           = body.querySelector('.sidebar-navbar-bg');
      var textCol      = body.querySelector('.sidebar-navbar-text-color');
      var linkCol      = body.querySelector('.sidebar-navbar-link-color');
      var height       = body.querySelector('.sidebar-navbar-height');
      var padY         = body.querySelector('.sidebar-navbar-pad-y');
      var gap          = body.querySelector('.sidebar-navbar-gap');
      var container    = body.querySelector('.sidebar-navbar-container');
      var mobile         = body.querySelector('.sidebar-navbar-mobile');
      var sticky         = body.querySelector('.sidebar-navbar-sticky');
      var shadow         = body.querySelector('.sidebar-navbar-shadow');
      var scrollEffect   = body.querySelector('.sidebar-navbar-scroll-effect');
      var dropdownStyle  = body.querySelector('.sidebar-navbar-dropdown-style');
      var menuOverflow   = body.querySelector('.sidebar-navbar-menu-overflow');

      function chrome(field, value) {
        return postJson('/edit/site-chrome/update/', { field: field, value: value });
      }
      function cfg(key, value) {
        return postJson('/edit/navbar/config/update/', { key: key, value: value });
      }

      var req = chrome('navbar_theme',     theme     ? theme.value     : 'light')
        .then(function () { return chrome('navbar_container', container ? container.value : 'container'); })
        .then(function () { return chrome('navbar_sticky',    sticky    ? (sticky.checked ? '1' : '0')    : '0'); })
        .then(function () { return chrome('navbar_shadow',    shadow    ? (shadow.checked ? '1' : '0')    : '1'); })
        .then(function () { return cfg('link_style',      linkStyle    ? linkStyle.value        : 'pill'); })
        .then(function () { return cfg('mobile_menu_style', mobile     ? mobile.value           : 'collapse'); })
        .then(function () { return cfg('scroll_effect',   scrollEffect  ? scrollEffect.value    : 'none'); })
        .then(function () { return cfg('dropdown_style',  dropdownStyle ? dropdownStyle.value   : 'default'); })
        .then(function () { return cfg('menu_overflow',   menuOverflow  ? menuOverflow.value    : 'visible'); })
        .then(function () { return cfg('bg_color',        bg           ? bg.value.trim()        : ''); })
        .then(function () { return cfg('text_color',      textCol      ? textCol.value.trim()   : ''); })
        .then(function () { return cfg('link_color',      linkCol      ? linkCol.value.trim()   : ''); })
        .then(function () { return cfg('height_px',       height       ? height.value           : '76'); })
        .then(function () { return cfg('padding_y',       padY         ? padY.value             : '0.4'); })
        .then(function () { return cfg('gap_px',          gap          ? gap.value              : '12'); });

      req.then(function () { window.location.reload(); }).catch(alertError);
    });
  }

  var NEUTRAL_COLORS = [
    '#ffffff', '#f8f9fa', '#e9ecef', '#dee2e6', '#ced4da',
    '#adb5bd', '#6c757d', '#495057', '#343a40', '#212529', '#000000',
  ];

  function getThemeColors() {
    var style = getComputedStyle(document.documentElement);
    var props = [
      '--bs-primary', '--bs-secondary', '--bs-success',
      '--bs-danger', '--bs-warning', '--bs-info',
    ];
    var out = [];
    props.forEach(function (p) {
      var v = style.getPropertyValue(p).trim();
      if (v) out.push(v);
    });
    var bodyBg = style.getPropertyValue('--cbl-main-bg').trim();
    if (bodyBg && bodyBg !== '#ffffff' && out.indexOf(bodyBg) < 0) out.push(bodyBg);
    return out;
  }

  function renderColorField(inputCls, value, label) {
    var hasBg = !!value;
    var swatchStyle = hasBg
      ? 'background:' + escapeHtml(value) + ';'
      : 'background:repeating-conic-gradient(#e0e0e0 0% 25%,#f5f5f5 0% 50%) 0 0/8px 8px;';
    return '<label class="form-label small mb-1">' + escapeHtml(label) + '</label>' +
      '<div class="cbl-color-field position-relative mb-2">' +
        '<div class="d-flex align-items-center gap-2">' +
          '<button type="button" class="cbl-color-trigger" style="' + swatchStyle + '" title="Choose colour"></button>' +
          '<input type="text" class="form-control form-control-sm ' + escapeHtml(inputCls) + '" placeholder="None" value="' + escapeHtml(value) + '">' +
          (hasBg ? '<button type="button" class="btn btn-link btn-sm p-0 text-body-secondary cbl-color-clear" title="Clear" style="font-size:1.2rem;line-height:1">&times;</button>' : '') +
        '</div>' +
        '<div class="cbl-color-popover d-none">' +
          '<div class="cbl-color-group-label">Theme</div>' +
          '<div class="cbl-color-swatches cbl-theme-swatches"></div>' +
          '<div class="cbl-color-group-label">Neutral</div>' +
          '<div class="cbl-color-swatches cbl-neutral-swatches"></div>' +
          '<div class="cbl-color-group-label">Custom</div>' +
          '<div class="d-flex gap-2 align-items-center">' +
            '<input type="color" class="cbl-native-picker" value="' + escapeHtml(value && value.startsWith('#') && value.length === 7 ? value : '#ffffff') + '">' +
            '<input type="text" class="form-control form-control-sm cbl-hex-input" placeholder="#rrggbb" value="' + escapeHtml(value) + '">' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  function wireColorField(field) {
    var input  = field.querySelector('input[type="text"]');
    var trigger = field.querySelector('.cbl-color-trigger');
    var popover = field.querySelector('.cbl-color-popover');
    var native  = field.querySelector('.cbl-native-picker');
    var hexIn   = field.querySelector('.cbl-hex-input');
    var clearBtn = field.querySelector('.cbl-color-clear');
    var themeSw = field.querySelector('.cbl-theme-swatches');
    var neutSw  = field.querySelector('.cbl-neutral-swatches');
    if (!trigger || !popover || !input) return;

    var transparentBg = 'repeating-conic-gradient(#e0e0e0 0% 25%,#f5f5f5 0% 50%) 0 0/8px 8px';

    function setValue(val) {
      val = (val || '').trim();
      input.value = val;
      trigger.style.background = val || transparentBg;
      if (hexIn) hexIn.value = val;
      if (native && val && /^#[0-9a-fA-F]{6}$/.test(val)) native.value = val;
      field.querySelectorAll('.cbl-color-swatch').forEach(function (s) {
        s.classList.toggle('cbl-swatch-active', s.dataset.color === val);
      });
    }

    function makeSwatch(color, parent, isNone) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'cbl-color-swatch' + (isNone ? ' cbl-color-none-swatch' : '') + (input.value === color ? ' cbl-swatch-active' : '');
      if (!isNone) btn.style.background = color;
      btn.dataset.color = color;
      btn.title = isNone ? 'No background' : color;
      btn.addEventListener('click', function (e) { e.stopPropagation(); setValue(color); closePopover(); });
      parent.appendChild(btn);
    }

    function openPopover() {
      themeSw.innerHTML = '';
      makeSwatch('', themeSw, true);
      getThemeColors().forEach(function (c) { makeSwatch(c, themeSw, false); });
      neutSw.innerHTML = '';
      NEUTRAL_COLORS.forEach(function (c) { makeSwatch(c, neutSw, false); });
      if (hexIn) hexIn.value = input.value;
      popover.classList.remove('d-none');
    }

    function closePopover() { popover.classList.add('d-none'); }

    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      popover.classList.contains('d-none') ? openPopover() : closePopover();
    });

    if (native) {
      native.addEventListener('input', function () { setValue(native.value); });
    }
    if (hexIn) {
      hexIn.addEventListener('change', function () { setValue(hexIn.value.trim()); });
    }
    if (clearBtn) {
      clearBtn.addEventListener('click', function (e) { e.stopPropagation(); setValue(''); closePopover(); });
    }

    document.addEventListener('click', function (e) {
      if (!field.contains(e.target)) closePopover();
    });
  }

  function wireColorFields(container) {
    container.querySelectorAll('.cbl-color-field').forEach(wireColorField);
  }

  // Curated common Bootstrap icons offered in the picker. Power users can still
  // type any valid bootstrap-icons name into the field.
  var ICON_CHOICES = [
    'star-fill', 'heart-fill', 'lightning-charge-fill', 'shield-fill-check',
    'check-circle-fill', 'trophy-fill', 'gem', 'rocket-takeoff-fill',
    'gear-fill', 'people-fill', 'person-fill', 'chat-dots-fill',
    'envelope-fill', 'telephone-fill', 'geo-alt-fill', 'clock-fill',
    'calendar-check-fill', 'cart-fill', 'bag-fill', 'credit-card-fill',
    'graph-up-arrow', 'bar-chart-fill', 'lightbulb-fill', 'award-fill',
    'hand-thumbs-up-fill', 'brush-fill', 'tools', 'truck', 'box-seam-fill',
    'globe', 'wifi', 'lock-fill', 'search', 'bell-fill', 'camera-fill',
    'image-fill', 'play-circle-fill', 'book-fill', 'mortarboard-fill',
    'briefcase-fill', 'building', 'house-fill', 'cup-hot-fill', 'scissors',
    'palette-fill', 'magic', 'stars', 'fire', 'droplet-fill', 'tree-fill',
    'sun-fill', 'moon-fill', 'gift-fill', 'emoji-smile-fill', 'patch-check-fill',
  ];

  function renderIconPicker(currentIcon) {
    currentIcon = currentIcon || '';
    var preview = currentIcon
      ? '<i class="bi bi-' + escapeHtml(currentIcon) + '"></i>'
      : '<span class="text-body-secondary" style="font-size:.7rem">None</span>';
    var grid = ICON_CHOICES.map(function (name) {
      var active = name === currentIcon ? ' cbl-icon-choice-active' : '';
      return '<button type="button" class="cbl-icon-choice' + active + '" data-icon="' + name + '" title="' + name + '">' +
        '<i class="bi bi-' + name + '"></i></button>';
    }).join('');
    return '<label class="form-label small mb-1">Icon</label>' +
      '<div class="cbl-icon-picker mb-2">' +
        '<div class="d-flex align-items-center gap-2 mb-1">' +
          '<span class="cbl-icon-preview">' + preview + '</span>' +
          '<input type="text" class="form-control form-control-sm sidebar-item-icon" placeholder="icon name" value="' + escapeHtml(currentIcon) + '">' +
          '<button type="button" class="btn btn-sm btn-outline-secondary cbl-icon-clear" title="Remove icon">&times;</button>' +
        '</div>' +
        '<input type="text" class="form-control form-control-sm mb-1 cbl-icon-search" placeholder="Search icons…">' +
        '<div class="cbl-icon-grid">' + grid + '</div>' +
        '<div class="form-text">Browse <a href="https://icons.getbootstrap.com/" target="_blank" rel="noopener">all icons</a> and type any name.</div>' +
      '</div>';
  }

  function wireIconPicker(shell) {
    var input   = shell.querySelector('.sidebar-item-icon');
    var preview = shell.querySelector('.cbl-icon-preview');
    var search  = shell.querySelector('.cbl-icon-search');
    var clear   = shell.querySelector('.cbl-icon-clear');
    var grid    = shell.querySelector('.cbl-icon-grid');
    if (!input || !grid) return;

    function refreshPreview() {
      var v = input.value.trim();
      preview.innerHTML = v
        ? '<i class="bi bi-' + escapeHtml(v) + '"></i>'
        : '<span class="text-body-secondary" style="font-size:.7rem">None</span>';
      grid.querySelectorAll('.cbl-icon-choice').forEach(function (b) {
        b.classList.toggle('cbl-icon-choice-active', b.dataset.icon === v);
      });
    }

    grid.querySelectorAll('.cbl-icon-choice').forEach(function (btn) {
      btn.addEventListener('click', function () {
        input.value = btn.dataset.icon;
        refreshPreview();
      });
    });

    input.addEventListener('input', refreshPreview);

    if (clear) {
      clear.addEventListener('click', function () { input.value = ''; refreshPreview(); });
    }

    if (search) {
      search.addEventListener('input', function () {
        var q = search.value.trim().toLowerCase();
        grid.querySelectorAll('.cbl-icon-choice').forEach(function (b) {
          b.style.display = (!q || b.dataset.icon.indexOf(q) !== -1) ? '' : 'none';
        });
      });
    }
  }

  function renderRichTextEditor(cls, value) {
    return '<div class="cbl-rich-editor mb-2">' +
        '<div class="cbl-rich-toolbar btn-group btn-group-sm mb-1">' +
          '<button type="button" class="btn btn-outline-secondary" data-cmd="bold"><strong>B</strong></button>' +
          '<button type="button" class="btn btn-outline-secondary" data-cmd="italic"><em>I</em></button>' +
          '<button type="button" class="btn btn-outline-secondary" data-cmd="insertUnorderedList">&#8226; List</button>' +
        '</div>' +
        '<div class="form-control ' + escapeHtml(cls) + '" contenteditable="true" style="min-height:80px;overflow-y:auto;">' + value + '</div>' +
      '</div>';
  }

  function getEditorContent(container, selector) {
    var el = container.querySelector(selector);
    return el ? el.innerHTML : '';
  }

  function wireRichToolbar(container) {
    container.querySelectorAll('.cbl-rich-toolbar [data-cmd]').forEach(function (btn) {
      btn.addEventListener('mousedown', function (e) {
        e.preventDefault();
        document.execCommand(btn.dataset.cmd, false, null);
      });
    });
    // Tell the browser to insert <p> on Enter (not <div>, which the sanitizer strips)
    container.querySelectorAll('[contenteditable]').forEach(function (el) {
      el.addEventListener('focus', function () {
        try { document.execCommand('defaultParagraphSeparator', false, 'p'); } catch (e) {}
      }, { once: false });
    });
  }

  function renderItem(itemId) {
    return '<div class="edit-sidebar-section sidebar-item-shell" data-item-id="' + escapeHtml(itemId) + '">' +
        '<p class="small text-body-secondary mb-0">Loading item…</p>' +
      '</div>';
  }

  function wireItem(body, itemId) {
    var shell = body.querySelector('.sidebar-item-shell');
    fetch('/edit/item/' + itemId + '/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!shell) return;
        var imgHtml = d.image_url
          ? '<img src="' + escapeHtml(d.image_url) + '" alt="" style="max-height:60px;max-width:100%;border-radius:4px;object-fit:cover;" class="mb-2 d-block">'
          : '<p class="small text-body-secondary mb-1">No image.</p>';
        var cfg = d.link_config || {};
        function cfgSel(key, val) { return cfg[key] === val ? ' selected' : ''; }
        function cfgIs(key, val)  { return cfg[key] === val; }

        shell.innerHTML =
          '<h3>Item</h3>' +
          '<div class="mb-2">' + imgHtml +
            '<input type="file" class="sidebar-item-img-file" accept="image/*" style="display:none">' +
            '<button type="button" class="btn btn-sm btn-outline-primary w-100 mb-1 sidebar-upload-item-img">Upload image</button>' +
            '<div class="small text-danger sidebar-item-img-status"></div>' +
          '</div>' +
          '<label class="form-label small mb-1">Title</label>' +
          '<input type="text" class="form-control form-control-sm mb-2 sidebar-item-title" value="' + escapeHtml(d.title || '') + '">' +
          '<label class="form-label small mb-1">Text</label>' +
          renderRichTextEditor('sidebar-item-text', d.text || '') +
          renderIconPicker(d.icon || '') +

          '<hr class="my-2">' +
          '<div class="small fw-semibold mb-2 text-body-secondary text-uppercase" style="letter-spacing:.05em;font-size:.7rem">Button</div>' +

          '<label class="form-label small mb-1">Link URL</label>' +
          '<input type="text" class="form-control form-control-sm mb-2 sidebar-item-link-url" value="' + escapeHtml(d.link_url || '') + '">' +
          '<label class="form-label small mb-1">Button text</label>' +
          '<input type="text" class="form-control form-control-sm mb-2 sidebar-item-link-text" value="' + escapeHtml(d.link_text || '') + '">' +

          '<label class="form-label small mb-1">Color</label>' +
          '<select class="form-select form-select-sm mb-2 sidebar-item-link-style">' +
            '<option value=""'                      + (!d.link_style                          ? ' selected' : '') + '>Default (auto)</option>' +
            '<option value="btn-primary"'           + (d.link_style === 'btn-primary'           ? ' selected' : '') + '>Primary</option>' +
            '<option value="btn-secondary"'         + (d.link_style === 'btn-secondary'         ? ' selected' : '') + '>Secondary</option>' +
            '<option value="btn-outline-primary"'   + (d.link_style === 'btn-outline-primary'   ? ' selected' : '') + '>Outline — Primary</option>' +
            '<option value="btn-outline-secondary"' + (d.link_style === 'btn-outline-secondary' ? ' selected' : '') + '>Outline — Secondary</option>' +
            '<option value="btn-light"'             + (d.link_style === 'btn-light'             ? ' selected' : '') + '>Light</option>' +
            '<option value="btn-outline-light"'     + (d.link_style === 'btn-outline-light'     ? ' selected' : '') + '>Outline — Light</option>' +
            '<option value="btn-dark"'              + (d.link_style === 'btn-dark'              ? ' selected' : '') + '>Dark</option>' +
            '<option value="btn-outline-dark"'      + (d.link_style === 'btn-outline-dark'      ? ' selected' : '') + '>Outline — Dark</option>' +
            '<option value="btn-success"'           + (d.link_style === 'btn-success'           ? ' selected' : '') + '>Green</option>' +
            '<option value="btn-danger"'            + (d.link_style === 'btn-danger'            ? ' selected' : '') + '>Red</option>' +
            '<option value="btn-warning"'           + (d.link_style === 'btn-warning'           ? ' selected' : '') + '>Yellow</option>' +
            '<option value="btn-link"'              + (d.link_style === 'btn-link'              ? ' selected' : '') + '>Plain link</option>' +
          '</select>' +

          '<div class="d-flex gap-2 mb-2">' +
            '<div class="flex-fill">' +
              '<label class="form-label small mb-1">Size</label>' +
              '<select class="form-select form-select-sm sidebar-item-cfg-size">' +
                '<option value=""'  + cfgSel('size', '')   + '>Large</option>' +
                '<option value="md"'+ cfgSel('size', 'md') + '>Regular</option>' +
                '<option value="sm"'+ cfgSel('size', 'sm') + '>Small</option>' +
              '</select>' +
            '</div>' +
            '<div class="flex-fill">' +
              '<label class="form-label small mb-1">Shape</label>' +
              '<select class="form-select form-select-sm sidebar-item-cfg-shape">' +
                '<option value=""'      + cfgSel('shape', '')       + '>Default</option>' +
                '<option value="pill"'  + cfgSel('shape', 'pill')   + '>Pill</option>' +
                '<option value="square"'+ cfgSel('shape', 'square') + '>Square</option>' +
              '</select>' +
            '</div>' +
          '</div>' +

          '<div class="d-flex gap-2 mb-2">' +
            '<div class="flex-fill">' +
              '<label class="form-label small mb-1">Shadow</label>' +
              '<select class="form-select form-select-sm sidebar-item-cfg-shadow">' +
                '<option value=""'  + cfgSel('shadow', '')   + '>None</option>' +
                '<option value="sm"'+ cfgSel('shadow', 'sm') + '>Small</option>' +
                '<option value="md"'+ cfgSel('shadow', 'md') + '>Medium</option>' +
                '<option value="lg"'+ cfgSel('shadow', 'lg') + '>Large</option>' +
              '</select>' +
            '</div>' +
            '<div class="flex-fill">' +
              '<label class="form-label small mb-1">Hover effect</label>' +
              '<select class="form-select form-select-sm sidebar-item-cfg-hover">' +
                '<option value=""'       + cfgSel('hover', '')       + '>None</option>' +
                '<option value="lift"'   + cfgSel('hover', 'lift')   + '>Lift</option>' +
                '<option value="glow"'   + cfgSel('hover', 'glow')   + '>Glow</option>' +
                '<option value="pulse"'  + cfgSel('hover', 'pulse')  + '>Pulse</option>' +
              '</select>' +
            '</div>' +
          '</div>' +

          '<div class="form-check mb-2">' +
            '<input type="checkbox" class="form-check-input sidebar-item-cfg-fullwidth" id="sifw-' + escapeHtml(String(itemId)) + '"' + (cfg.full_width ? ' checked' : '') + '>' +
            '<label class="form-check-label small" for="sifw-' + escapeHtml(String(itemId)) + '">Full width</label>' +
          '</div>' +
          '<label class="form-label small mb-1">Margin around button (px)</label>' +
          '<input type="number" class="form-control form-control-sm mb-3 sidebar-item-cfg-margin" min="0" max="100" value="' + escapeHtml(String(cfg.margin || '')) + '" placeholder="0">' +

          '<button type="button" class="btn btn-sm btn-primary w-100 mb-2 sidebar-save-item">Save</button>' +
          '<button type="button" class="btn btn-sm btn-outline-danger w-100 sidebar-delete-item">Delete item</button>';

        wireRichToolbar(shell);
        wireIconPicker(shell);

        var save = shell.querySelector('.sidebar-save-item');
        if (save) {
          save.addEventListener('click', function () {
            var title     = shell.querySelector('.sidebar-item-title');
            var text      = getEditorContent(shell, '.sidebar-item-text');
            var icon      = shell.querySelector('.sidebar-item-icon');
            var linkUrl   = shell.querySelector('.sidebar-item-link-url');
            var linkTxt   = shell.querySelector('.sidebar-item-link-text');
            var linkStyle = shell.querySelector('.sidebar-item-link-style');
            var cfgSize   = shell.querySelector('.sidebar-item-cfg-size');
            var cfgShape  = shell.querySelector('.sidebar-item-cfg-shape');
            var cfgShadow = shell.querySelector('.sidebar-item-cfg-shadow');
            var cfgHover  = shell.querySelector('.sidebar-item-cfg-hover');
            var cfgFull   = shell.querySelector('.sidebar-item-cfg-fullwidth');
            var cfgMargin = shell.querySelector('.sidebar-item-cfg-margin');
            postJson('/edit/item/' + itemId + '/field/title/',      { value: title     ? title.value     : '' })
              .then(function () { return postJson('/edit/item/' + itemId + '/field/text/',       { value: text }); })
              .then(function () { return postJson('/edit/item/' + itemId + '/field/icon/',       { value: icon      ? icon.value      : '' }); })
              .then(function () { return postJson('/edit/item/' + itemId + '/field/link_url/',   { value: linkUrl   ? linkUrl.value   : '' }); })
              .then(function () { return postJson('/edit/item/' + itemId + '/field/link_text/',  { value: linkTxt   ? linkTxt.value   : '' }); })
              .then(function () { return postJson('/edit/item/' + itemId + '/field/link_style/', { value: linkStyle ? linkStyle.value : '' }); })
              .then(function () { return postJson('/edit/item/' + itemId + '/config/', {
                size:       cfgSize   ? cfgSize.value   : '',
                shape:      cfgShape  ? cfgShape.value  : '',
                shadow:     cfgShadow ? cfgShadow.value : '',
                hover:      cfgHover  ? cfgHover.value  : '',
                full_width: cfgFull && cfgFull.checked ? '1' : '0',
                margin:     cfgMargin ? cfgMargin.value : '',
              }); })
              .then(function () { window.location.reload(); })
              .catch(alertError);
          });
        }

        var uploadBtn = shell.querySelector('.sidebar-upload-item-img');
        var imgFile   = shell.querySelector('.sidebar-item-img-file');
        var imgStatus = shell.querySelector('.sidebar-item-img-status');
        if (uploadBtn && imgFile) {
          uploadBtn.addEventListener('click', function () { imgFile.click(); });
          imgFile.addEventListener('change', function () {
            if (!imgFile.files || !imgFile.files.length) return;
            var fd = new FormData();
            fd.append('image', imgFile.files[0]);
            uploadBtn.disabled = true; uploadBtn.textContent = 'Uploading…';
            fetch('/edit/item/' + itemId + '/image/', {
              method: 'POST', credentials: 'same-origin',
              headers: { 'X-CSRFToken': getCsrf() }, body: fd,
            })
              .then(function (r) { return r.json().catch(function () { throw new Error('Server error (' + r.status + ')'); }); })
              .then(function (d2) { if (d2.success) { window.location.reload(); } else { throw new Error(d2.error || 'Upload failed'); } })
              .catch(function (err) {
                if (imgStatus) imgStatus.textContent = err.message || 'Upload failed';
                uploadBtn.disabled = false; uploadBtn.textContent = 'Upload image';
              });
          });
        }

        var del = shell.querySelector('.sidebar-delete-item');
        if (del) {
          del.addEventListener('click', function () {
            if (!confirm('Delete this item?')) return;
            postJson('/edit/item/' + itemId + '/delete/')
              .then(function () { window.location.reload(); })
              .catch(alertError);
          });
        }
      })
      .catch(function () {
        if (shell) shell.innerHTML = '<p class="text-danger small mb-0">Failed to load item.</p>';
      });
  }

  function renderFooter() {
    var r = document.getElementById('footer-region');
    var variant   = r ? (r.dataset.footerVariant   || 'footer_1') : 'footer_1';
    var copyright = r ? (r.dataset.footerCopyright || '')         : '';
    var facebook  = r ? (r.dataset.footerFacebook  || '')         : '';
    var instagram = r ? (r.dataset.footerInstagram || '')         : '';
    var twitter   = r ? (r.dataset.footerTwitter   || '')         : '';
    var linkedin  = r ? (r.dataset.footerLinkedin  || '')         : '';

    function vOpt(val, label) {
      return '<option value="' + val + '"' + (variant === val ? ' selected' : '') + '>' + label + '</option>';
    }

    return '<div class="edit-sidebar-section">' +
        '<h3>Layout</h3>' +
        '<label class="form-label small mb-1">Footer style</label>' +
        '<select class="form-select form-select-sm mb-2 sidebar-footer-layout">' +
          vOpt('footer_1', 'Logo center with nav') +
          vOpt('footer_2', 'Brand left, social right') +
          vOpt('footer_3', 'Centered minimal') +
          vOpt('footer_4', 'Multi-column sections') +
          vOpt('footer_5', 'Newsletter signup') +
        '</select>' +
      '</div>' +
      '<div class="edit-sidebar-section">' +
        '<h3>Content</h3>' +
        '<label class="form-label small mb-1">Copyright text</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-footer-copyright" value="' + escapeHtml(copyright) + '">' +
        '<label class="form-label small mb-1">Facebook URL</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-footer-fb" placeholder="https://facebook.com/…" value="' + escapeHtml(facebook) + '">' +
        '<label class="form-label small mb-1">Instagram URL</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-footer-ig" placeholder="https://instagram.com/…" value="' + escapeHtml(instagram) + '">' +
        '<label class="form-label small mb-1">Twitter / X URL</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-footer-tw" placeholder="https://x.com/…" value="' + escapeHtml(twitter) + '">' +
        '<label class="form-label small mb-1">LinkedIn URL</label>' +
        '<input type="text" class="form-control form-control-sm mb-2 sidebar-footer-li" placeholder="https://linkedin.com/…" value="' + escapeHtml(linkedin) + '">' +
        '<button type="button" class="btn btn-sm btn-primary w-100 sidebar-save-footer-design">Save</button>' +
      '</div>';
  }

  function wireFooter(body) {
    var save = body.querySelector('.sidebar-save-footer-design');
    if (!save) return;
    save.addEventListener('click', function () {
      var layout    = body.querySelector('.sidebar-footer-layout');
      var copyright = body.querySelector('.sidebar-footer-copyright');
      var fb = body.querySelector('.sidebar-footer-fb');
      var ig = body.querySelector('.sidebar-footer-ig');
      var tw = body.querySelector('.sidebar-footer-tw');
      var li = body.querySelector('.sidebar-footer-li');

      function chrome(field, value) {
        return postJson('/edit/site-chrome/update/', { field: field, value: value });
      }

      chrome('footer_variant',   layout    ? layout.value    : 'footer_1')
        .then(function () { return chrome('copyright_text', copyright ? copyright.value : ''); })
        .then(function () { return chrome('facebook_url',   fb ? fb.value.trim() : ''); })
        .then(function () { return chrome('instagram_url',  ig ? ig.value.trim() : ''); })
        .then(function () { return chrome('twitter_url',    tw ? tw.value.trim() : ''); })
        .then(function () { return chrome('linkedin_url',   li ? li.value.trim() : ''); })
        .then(function () { window.location.reload(); })
        .catch(alertError);
    });
  }

  function alertError(err) {
    alert(err && err.message ? err.message : 'Request failed');
  }

  window.cblInitInspectorSidebar = init;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

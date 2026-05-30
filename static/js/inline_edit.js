/**
 * inline_edit.js
 *
 * Front-end inline editing for staff/admin users.
 * Activated only when <body class="edit-mode"> is present (set by base.html
 * for authenticated staff users).
 *
 * Template convention -- wrap any editable element like this:
 *
 *   Text field:
 *     <div class="edit-wrap"
 *          data-edit-model="section|item"
 *          data-edit-id="<pk>"
 *          data-edit-field="<field_name>"
 *          data-edit-type="text|textarea">   <!-- default: "text" -->
 *       <h2 class="... edit-content">{{ section.heading }}</h2>
 *     </div>
 *
 *   Multiline with server-side formatting (linebreaks filter):
 *     <div class="edit-wrap" ... data-edit-type="textarea">
 *       <div class="... edit-content"
 *            data-edit-value="{{ section.subheading }}">   <!-- raw text for textarea -->
 *         {{ section.subheading|linebreaks }}
 *       </div>
 *     </div>
 *
 *   Image field:
 *     <div class="edit-wrap"
 *          data-edit-model="section|item"
 *          data-edit-id="<pk>"
 *          data-edit-field="primary_image|image"
 *          data-edit-type="image">
 *       <img ...> or placeholder div.edit-img-placeholder
 *     </div>
 *
 * Keyboard shortcuts inside text editors:
 *   Enter         -- save (single-line inputs)
 *   Ctrl+Enter    -- save (textareas)
 *   Escape        -- cancel
 */

(function () {
  'use strict';

  // -------------------------------------------------------------------------
  // CSRF helpers (Django sets the csrftoken cookie by default)
  // -------------------------------------------------------------------------
  function getCsrf() {
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  // -------------------------------------------------------------------------
  // Entry point
  // -------------------------------------------------------------------------
  function init() {
    if (!document.body.classList.contains('edit-mode')) return;

    wireUnwiredWraps();
    renderToolbar();
  }

  // Wire up any .edit-wrap that doesn't already have a pencil button.
  // Safe to call repeatedly (after new markup is injected by structural_edit.js).
  function wireUnwiredWraps() {
    document.querySelectorAll('.edit-wrap').forEach(function (wrap) {
      if (wrap.dataset.editWired === '1') return;
      setupWrap(wrap);
      wrap.dataset.editWired = '1';
    });
  }

  // Exposed so structural_edit.js can re-wire freshly injected sections/items.
  window.reinitInlineEdit = wireUnwiredWraps;

  // -------------------------------------------------------------------------
  // Wire up a single editable wrapper
  // -------------------------------------------------------------------------
  function setupWrap(wrap) {
    const type = wrap.dataset.editType || 'text';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'edit-pencil-btn';
    btn.setAttribute('aria-label', type === 'image' ? 'Change image' : 'Edit');
    btn.innerHTML = type === 'image'
      ? '<i class="bi bi-camera-fill"></i>'
      : '<i class="bi bi-pencil-fill"></i>';

    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (wrap.classList.contains('is-editing') || wrap.classList.contains('is-uploading')) return;
      if (type === 'image') {
        startImageEdit(wrap);
      } else {
        startTextEdit(wrap, type === 'textarea');
      }
    });

    wrap.appendChild(btn);
  }

  // -------------------------------------------------------------------------
  // Text editing
  // -------------------------------------------------------------------------
  function startTextEdit(wrap, isMultiline) {
    wrap.classList.add('is-editing');

    const contentEl = wrap.querySelector('.edit-content');

    // For multiline fields whose templates apply |linebreaks, the rendered
    // innerHTML differs from the raw stored text. Templates should store the
    // raw value in data-edit-value so we can populate the textarea correctly.
    const rawValue = contentEl.dataset.editValue !== undefined
      ? contentEl.dataset.editValue
      : contentEl.textContent.trim();

    // Hide the display element; insert edit form before it
    contentEl.hidden = true;
    const form = buildTextForm(rawValue, isMultiline);
    wrap.insertBefore(form, contentEl);

    const input      = form.querySelector('.edit-input');
    const saveBtn    = form.querySelector('.edit-save');
    const cancelBtn  = form.querySelector('.edit-cancel');
    const feedbackEl = form.querySelector('.edit-feedback');

    input.focus();
    if (!isMultiline) input.select();

    cancelBtn.addEventListener('click', function () {
      form.remove();
      contentEl.hidden = false;
      wrap.classList.remove('is-editing');
    });

    saveBtn.addEventListener('click', function () {
      doSaveText(wrap, contentEl, form, saveBtn, feedbackEl, input.value);
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        e.preventDefault();
        cancelBtn.click();
      }
      if (e.key === 'Enter' && !isMultiline && !e.shiftKey) {
        e.preventDefault();
        saveBtn.click();
      }
      if (e.key === 'Enter' && isMultiline && e.ctrlKey) {
        e.preventDefault();
        saveBtn.click();
      }
    });
  }

  function doSaveText(wrap, contentEl, form, saveBtn, feedbackEl, value) {
    const model = wrap.dataset.editModel;
    const id    = wrap.dataset.editId;
    const field = wrap.dataset.editField;
    const url   = '/edit/' + model + '/' + id + '/field/' + field + '/';

    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving…';
    feedbackEl.textContent = '';
    feedbackEl.className = 'edit-feedback ms-2 small';

    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrf(),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'value=' + encodeURIComponent(value),
    })
    .then(function (resp) {
      if (!resp.ok) {
        return resp.json().catch(function () { return {}; }).then(function (data) {
          throw new Error(data.error || 'Save failed (' + resp.status + ')');
        });
      }
      return resp.json();
    })
    .then(function (data) {
      // Update the display element
      contentEl.innerHTML = data.html || escHtml(data.value);

      // Keep the raw value attribute in sync for future edits
      if (contentEl.dataset.editValue !== undefined) {
        contentEl.dataset.editValue = data.value;
      }

      form.remove();
      contentEl.hidden = false;
      wrap.classList.remove('is-editing');
      flashSaved(wrap);
    })
    .catch(function (err) {
      feedbackEl.textContent = err.message || 'Save failed. Try again.';
      feedbackEl.className = 'edit-feedback ms-2 small text-danger';
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save';
    });
  }

  function buildTextForm(value, isMultiline) {
    const div = document.createElement('div');
    div.className = 'edit-form';

    var inputHtml = isMultiline
      ? '<textarea class="form-control edit-input mb-2" rows="4"></textarea>'
      : '<input type="text" class="form-control edit-input mb-2">';

    div.innerHTML =
      inputHtml +
      '<div class="edit-actions">' +
        '<button type="button" class="btn btn-sm btn-primary edit-save">Save</button>' +
        '<button type="button" class="btn btn-sm btn-outline-secondary edit-cancel">Cancel</button>' +
        '<span class="edit-feedback ms-2 small"></span>' +
      '</div>';

    div.querySelector('.edit-input').value = value;
    return div;
  }

  // -------------------------------------------------------------------------
  // Image editing
  // -------------------------------------------------------------------------
  function startImageEdit(wrap) {
    var fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);

    fileInput.addEventListener('change', function () {
      if (!fileInput.files[0]) {
        cleanupFileInput(fileInput);
        return;
      }
      doUploadImage(wrap, fileInput.files[0], fileInput);
    });

    // If the user dismisses the dialog without picking a file the 'change'
    // event won't fire; clean up on focus return to the window.
    window.addEventListener('focus', function onFocus() {
      window.removeEventListener('focus', onFocus);
      setTimeout(function () { cleanupFileInput(fileInput); }, 300);
    }, { once: true });

    fileInput.click();
  }

  function doUploadImage(wrap, file, fileInput) {
    var model = wrap.dataset.editModel;
    var id    = wrap.dataset.editId;
    var url   = '/edit/' + model + '/' + id + '/image/';

    wrap.classList.add('is-uploading');

    var formData = new FormData();
    formData.append('image', file);

    fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() },
      body: formData,
    })
    .then(function (resp) {
      if (!resp.ok) {
        return resp.json().catch(function () { return {}; }).then(function (data) {
          throw new Error(data.error || 'Upload failed (' + resp.status + ')');
        });
      }
      return resp.json();
    })
    .then(function (data) {
      // Replace existing <img> src, or swap a placeholder for a real <img>
      var img = wrap.querySelector('img');
      if (img) {
        img.src = data.url;
      } else {
        var placeholder = wrap.querySelector('.edit-img-placeholder');
        if (placeholder) {
          var newImg = document.createElement('img');
          newImg.src = data.url;
          newImg.alt = '';
          newImg.className = 'img-fluid rounded';
          placeholder.replaceWith(newImg);
        }
      }
      flashSaved(wrap);
    })
    .catch(function (err) {
      // Keep it simple -- alert is fine for an error the admin needs to act on.
      alert('Image upload failed: ' + (err.message || 'Unknown error') +
            '\n\nCheck that your Cloudinary credentials are set correctly.');
    })
    .finally(function () {
      wrap.classList.remove('is-uploading');
      cleanupFileInput(fileInput);
    });
  }

  function cleanupFileInput(fileInput) {
    if (fileInput && fileInput.parentNode) {
      fileInput.parentNode.removeChild(fileInput);
    }
  }

  // -------------------------------------------------------------------------
  // Edit mode toolbar
  // -------------------------------------------------------------------------
  function renderToolbar() {
    // No-op. The staff toolbar is rendered server-side in base.html so it is
    // present even when edit mode is off (so staff can turn it back on).
    // Kept as a function for backward compatibility with the boot sequence.
  }

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------
  function flashSaved(wrap) {
    wrap.classList.remove('edit-saved');
    void wrap.offsetWidth; // force reflow so animation restarts
    wrap.classList.add('edit-saved');
    setTimeout(function () { wrap.classList.remove('edit-saved'); }, 1500);
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // -------------------------------------------------------------------------
  // Boot
  // -------------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', init);

}());

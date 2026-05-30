/**
 * staff_toolbar.js
 *
 * - Toggles edit mode for staff users.
 * - Lets staff drag the floating toolbar to any screen position.
 * - Persists toolbar position in localStorage.
 * - Double-click the label to reset position.
 */
(function () {
  'use strict';

  function getCsrf() {
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function enableToolbarDrag(toolbar) {
    var handle = toolbar.querySelector('.staff-toolbar-label') || toolbar;
    var key = 'cbl_staff_toolbar_pos_v1';
    var dragging = false;
    var startX = 0;
    var startY = 0;
    var baseLeft = 0;
    var baseTop = 0;

    try {
      var raw = localStorage.getItem(key);
      if (raw) {
        var pos = JSON.parse(raw);
        if (typeof pos.left === 'number' && typeof pos.top === 'number') {
          toolbar.style.left = pos.left + 'px';
          toolbar.style.top = pos.top + 'px';
          toolbar.style.right = 'auto';
        }
      }
    } catch (e) {}

    function clampAndApply(left, top) {
      var margin = 8;
      var maxLeft = Math.max(margin, window.innerWidth - toolbar.offsetWidth - margin);
      var maxTop = Math.max(margin, window.innerHeight - toolbar.offsetHeight - margin);
      var x = Math.min(maxLeft, Math.max(margin, left));
      var y = Math.min(maxTop, Math.max(margin, top));
      toolbar.style.left = x + 'px';
      toolbar.style.top = y + 'px';
      toolbar.style.right = 'auto';
      try {
        localStorage.setItem(key, JSON.stringify({ left: x, top: y }));
      } catch (e) {}
    }

    handle.addEventListener('pointerdown', function (e) {
      if (e.button !== 0) return;
      dragging = true;
      startX = e.clientX;
      startY = e.clientY;
      var rect = toolbar.getBoundingClientRect();
      baseLeft = rect.left;
      baseTop = rect.top;
      handle.setPointerCapture(e.pointerId);
      toolbar.classList.add('is-dragging');
      e.preventDefault();
    });

    handle.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      clampAndApply(baseLeft + (e.clientX - startX), baseTop + (e.clientY - startY));
    });

    function endDrag(e) {
      if (!dragging) return;
      dragging = false;
      toolbar.classList.remove('is-dragging');
      try { handle.releasePointerCapture(e.pointerId); } catch (_) {}
    }

    handle.addEventListener('pointerup', endDrag);
    handle.addEventListener('pointercancel', endDrag);

    handle.addEventListener('dblclick', function () {
      toolbar.style.left = '';
      toolbar.style.top = '';
      toolbar.style.right = '';
      try { localStorage.removeItem(key); } catch (e) {}
    });
  }

  function init() {
    var toolbar = document.getElementById('staff-toolbar');
    var btn = document.getElementById('staff-toggle-edit');
    if (!toolbar || !btn) return;

    btn.addEventListener('click', function () {
      btn.disabled = true;
      btn.textContent = 'Switching...';

      fetch('/edit/toggle-mode/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() },
      })
        .then(function (resp) {
          if (!resp.ok) throw new Error('Could not switch mode');
          window.location.reload();
        })
        .catch(function (err) {
          alert(err.message);
          btn.disabled = false;
        });
    });

    enableToolbarDrag(toolbar);
  }

  document.addEventListener('DOMContentLoaded', init);
}());

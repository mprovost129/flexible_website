/**
 * navbar_overflow.js
 *
 * "More ▼" auto-overflow for .cbl-navbar-links lists.
 * Only activates when data-overflow-mode="more-menu" is set on the navbar header.
 * Does not run in edit mode (body.edit-mode), where all items must stay visible.
 */
(function () {
  'use strict';

  if (document.body.classList.contains('edit-mode')) return;

  function initMoreMenu(ul) {
    if (ul.dataset.moreWired) return;
    ul.dataset.moreWired = '1';

    // Inject "More" dropdown as the last list item (hidden by default)
    var moreLi = document.createElement('li');
    moreLi.className = 'nav-item dropdown cbl-nav-more';
    moreLi.style.display = 'none';
    moreLi.innerHTML =
      '<button class="nav-link dropdown-toggle" type="button"' +
      ' data-bs-toggle="dropdown" aria-expanded="false">More</button>' +
      '<ul class="dropdown-menu dropdown-menu-end cbl-nav-more-menu"></ul>';
    ul.appendChild(moreLi);

    var moreMenu = moreLi.querySelector('.cbl-nav-more-menu');

    // Snapshot original items (excluding the More button itself)
    var allItems = Array.prototype.slice.call(ul.children).filter(function (el) {
      return el !== moreLi;
    });

    function isOverflowing() {
      var containerRight = ul.getBoundingClientRect().right;
      // Find the last VISIBLE item
      for (var i = allItems.length - 1; i >= 0; i--) {
        if (allItems[i].style.display !== 'none') {
          return allItems[i].getBoundingClientRect().right > containerRight + 2;
        }
      }
      return false;
    }

    function reflow() {
      // 1. Restore all items and hide More
      allItems.forEach(function (li) { li.style.display = ''; });
      moreLi.style.display = 'none';
      moreMenu.innerHTML = '';

      // 2. If nothing overflows, done
      if (!isOverflowing()) return;

      // 3. Show More button (it takes space) and find overflow point
      moreLi.style.display = '';

      for (var i = allItems.length - 1; i >= 0; i--) {
        if (!isOverflowing()) break;
        // Move item i into More dropdown
        allItems[i].style.display = 'none';

        // Build a simplified dropdown-item for the More menu
        var anchor = allItems[i].querySelector('a, button');
        if (anchor) {
          var mi = document.createElement('li');
          var a = document.createElement('a');
          a.className = 'dropdown-item';
          a.href = anchor.getAttribute('href') || '#';
          a.textContent = anchor.textContent.trim();
          mi.appendChild(a);
          moreMenu.insertBefore(mi, moreMenu.firstChild);
        }
      }

      // If everything was hidden and More is still overflowing, nothing we can do
      var anyVisible = allItems.some(function (li) { return li.style.display !== 'none'; });
      if (!anyVisible) {
        allItems.forEach(function (li) { li.style.display = ''; });
        moreLi.style.display = 'none';
      }
    }

    // Watch for container size changes
    if (window.ResizeObserver) {
      new ResizeObserver(function () { requestAnimationFrame(reflow); }).observe(ul);
    } else {
      window.addEventListener('resize', function () { requestAnimationFrame(reflow); }, { passive: true });
    }

    requestAnimationFrame(reflow);
  }

  function init() {
    var header = document.querySelector('.cbl-navbar-shell[data-overflow-mode="more-menu"]');
    if (!header) return;

    header.querySelectorAll('.cbl-navbar-desktop ul.cbl-navbar-links').forEach(initMoreMenu);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

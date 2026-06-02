/**
 * color_field.js
 *
 * Progressive enhancement for dashboard color inputs. Any
 *   <input type="text" class="cbl-color-input">
 * is upgraded into the same swatch + popover + native-picker widget used by the
 * live edit sidebar (reusing the .cbl-color-* styles from main.css). The
 * original <input> is preserved (name/id/value intact) so the form submits
 * exactly as before — this only adds UI around it.
 */
(function () {
    'use strict';

    var NEUTRAL_COLORS = [
        '#ffffff', '#f8f9fa', '#e9ecef', '#dee2e6', '#ced4da',
        '#adb5bd', '#6c757d', '#495057', '#343a40', '#212529', '#000000',
    ];
    var TRANSPARENT_BG = 'repeating-conic-gradient(#e0e0e0 0% 25%,#f5f5f5 0% 50%) 0 0/8px 8px';

    function getThemeColors() {
        var style = getComputedStyle(document.documentElement);
        var props = ['--bs-primary', '--bs-secondary', '--bs-success', '--bs-danger', '--bs-warning', '--bs-info'];
        var out = [];
        props.forEach(function (p) {
            var v = style.getPropertyValue(p).trim();
            if (v) out.push(v);
        });
        return out;
    }

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/"/g, '&quot;')
            .replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function enhance(input) {
        if (input.dataset.cblColorWired === '1') return;
        input.dataset.cblColorWired = '1';

        var value = (input.value || '').trim();
        var isHex = /^#[0-9a-fA-F]{6}$/.test(value);

        var field = document.createElement('div');
        field.className = 'cbl-color-field position-relative';

        var row = document.createElement('div');
        row.className = 'd-flex align-items-center gap-2';

        var trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'cbl-color-trigger';
        trigger.title = 'Choose colour';

        var clear = document.createElement('button');
        clear.type = 'button';
        clear.className = 'btn btn-link btn-sm p-0 text-body-secondary cbl-color-clear';
        clear.title = 'Clear';
        clear.style.cssText = 'font-size:1.2rem;line-height:1';
        clear.innerHTML = '&times;';

        var popover = document.createElement('div');
        popover.className = 'cbl-color-popover d-none';
        popover.innerHTML =
            '<div class="cbl-color-group-label">Theme</div>' +
            '<div class="cbl-color-swatches cbl-theme-swatches"></div>' +
            '<div class="cbl-color-group-label">Neutral</div>' +
            '<div class="cbl-color-swatches cbl-neutral-swatches"></div>' +
            '<div class="cbl-color-group-label">Custom</div>' +
            '<div class="d-flex gap-2 align-items-center">' +
                '<input type="color" class="cbl-native-picker" value="' + (isHex ? esc(value) : '#ffffff') + '">' +
                '<input type="text" class="form-control form-control-sm cbl-hex-input" placeholder="#rrggbb" value="' + esc(value) + '">' +
            '</div>';

        // Wrap: insert field where the input was, then move the input inside.
        input.parentNode.insertBefore(field, input);
        row.appendChild(trigger);
        row.appendChild(input);     // preserves name / id / value
        row.appendChild(clear);
        field.appendChild(row);
        field.appendChild(popover);
        if (!input.getAttribute('placeholder')) input.setAttribute('placeholder', 'None');

        var native  = popover.querySelector('.cbl-native-picker');
        var hexIn   = popover.querySelector('.cbl-hex-input');
        var themeSw = popover.querySelector('.cbl-theme-swatches');
        var neutSw  = popover.querySelector('.cbl-neutral-swatches');

        function setValue(val) {
            val = (val || '').trim();
            input.value = val;
            trigger.style.background = val || TRANSPARENT_BG;
            if (hexIn) hexIn.value = val;
            if (native && /^#[0-9a-fA-F]{6}$/.test(val)) native.value = val;
            field.querySelectorAll('.cbl-color-swatch').forEach(function (s) {
                s.classList.toggle('cbl-swatch-active', s.dataset.color === val);
            });
            clear.style.display = val ? '' : 'none';
        }

        function makeSwatch(color, parent, isNone) {
            var b = document.createElement('button');
            b.type = 'button';
            b.className = 'cbl-color-swatch' + (isNone ? ' cbl-color-none-swatch' : '') + (input.value === color ? ' cbl-swatch-active' : '');
            if (!isNone) b.style.background = color;
            b.dataset.color = color;
            b.title = isNone ? 'No color' : color;
            b.addEventListener('click', function (e) { e.stopPropagation(); setValue(color); closePopover(); });
            parent.appendChild(b);
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
        if (native) native.addEventListener('input', function () { setValue(native.value); });
        if (hexIn)  hexIn.addEventListener('change', function () { setValue(hexIn.value.trim()); });
        input.addEventListener('change', function () { setValue(input.value.trim()); });
        clear.addEventListener('click', function (e) { e.stopPropagation(); setValue(''); });
        document.addEventListener('click', function (e) { if (!field.contains(e.target)) closePopover(); });

        setValue(value);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('input.cbl-color-input').forEach(enhance);
    });
})();

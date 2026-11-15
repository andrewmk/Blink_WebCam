// format.js - Locale-aware formatting helpers (the page's single formatting point)
//
// Locale, timezone, and temperature unit come from window.BlinkConfig, which
// the server populates from the machine's system locale. All times render in
// 24-hour format regardless of the locale's default.
//
// Load AFTER the inline window.BlinkConfig script and BEFORE every other module.

(function () {
    'use strict';

    const cfg = window.BlinkConfig || {};
    const LOCALE = cfg.LOCALE || 'en-US';
    const TEMP_UNIT = cfg.TEMP_UNIT === 'C' ? 'C' : 'F';

    // Validate the server-detected IANA timezone; an unknown name makes
    // Intl throw, so fall back to the browser's local zone.
    let TIMEZONE = cfg.TIMEZONE || null;
    if (TIMEZONE) {
        try {
            new Intl.DateTimeFormat('en-US', { timeZone: TIMEZONE });
        } catch (e) {
            console.warn('Unknown timezone from server, using browser local zone:', TIMEZONE, e);
            TIMEZONE = null;
        }
    }

    function makeFormatter(options, useZone) {
        const opts = useZone && TIMEZONE ? Object.assign({ timeZone: TIMEZONE }, options) : options;
        try {
            return new Intl.DateTimeFormat(LOCALE, opts);
        } catch (e) {
            console.warn('Locale formatting failed, falling back to en-US:', LOCALE, e);
            return new Intl.DateTimeFormat('en-US', opts);
        }
    }

    const clockFmt = makeFormatter({
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    }, true);

    const dateTimeFmt = makeFormatter({
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    }, true);

    const timeFmt = makeFormatter({
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    }, true);

    // Wall-clock variant for times that carry no timezone information
    // (image filenames). Formatted in the browser's local zone, which is the
    // machine's zone in kiosk use.
    const wallDateTimeFmt = makeFormatter({
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    }, false);

    window.formatDateTime = {
        clock: function (date) {
            return clockFmt.format(date);
        },
        // Accepts a Date or an ISO string
        dateTime: function (dateLike) {
            return dateTimeFmt.format(typeof dateLike === 'string' ? new Date(dateLike) : dateLike);
        },
        time: function (date) {
            return timeFmt.format(date);
        },
        wallDateTime: function (date) {
            return wallDateTimeFmt.format(date);
        }
    };

    // Temperatures arriving from the server are Fahrenheit (Blink camera
    // values and the weather API); convert for display when the locale is metric.
    window.formatTempF = function (valueF) {
        const v = parseFloat(valueF);
        if (isNaN(v)) return valueF; // "N/A" and friends pass through
        const value = TEMP_UNIT === 'C' ? Math.round((v - 32) * 5 / 9) : Math.round(v);
        return value + '\u00B0' + TEMP_UNIT;
    };

    window.localeSettings = {
        LOCALE: LOCALE,
        TIMEZONE: TIMEZONE,
        TEMP_UNIT: TEMP_UNIT
    };
})();

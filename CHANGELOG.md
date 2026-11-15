# Changelog

All notable changes to Blink WebCam Monitor are documented here.

---

## [Unreleased]

### Added

- **Locale-aware dashboard display** -- the web server detects the machine's
  locale settings (timezone from the `TZ` env var or the `/etc/localtime`
  symlink, locale from `LC_ALL`/`LC_TIME`/`LANGUAGE`/`LANG` with an `en-US`
  fallback, temperature unit from the locale region -- US, Liberia and
  Myanmar use °F, everything else °C) and passes them to the page via
  `window.BlinkConfig`. All times on the page (header clock, camera image
  timestamps, refresh timestamps, snooze "Until" badge and modal expiry)
  now render in the locale's date format with a **24-hour clock**, and
  camera temperatures show a unit symbol (e.g. `72°F` or `22°C`).
  Formatting happens client-side in a new `static/js/format.js` (the page's
  single formatting point); API timestamps are now offset-aware ISO strings
  so the display stays correct regardless of the browser's own timezone.

### Changed

- `alert_snooze.json` entries are stored as offset-aware ISO strings; legacy
  naive entries still parse and are treated as local time
- `/api/cameras/refresh` no longer returns the server-formatted US-style
  `last_update_formatted`; the client formats `last_update` itself

### Removed

- **Weather and alert widgets from the dashboard** -- the weather card
  (Tomorrow.io), animated radar card (RainViewer + Mapbox), NWS severe
  weather alerts, and NHC hurricane alerts are gone from the page header.
  The web server no longer exposes the weather/radar/NWS/NHC API endpoints,
  runs no background NWS/NHC polling, and writes no alert logs.
- `nws_alerts.py` and `nhc_alerts.py` standalone alert tools
- Weather/radar/NWS/NHC (and location) sections from
  `blink_config_setup.py`; existing config keys are simply ignored now and
  drop out on the next setup re-run
- README API Keys section, weather/radar/NWS troubleshooting entries, and
  related docs
  (note: `requests` stays in requirements.txt -- it is no longer used by
  project code, but `blinkpy 0.25.9` declares it as a dependency)

---

## [1.2.0] - 2026-11-15

### Added

- **12-hour polling interval** -- the setup wizard's Polling Interval menu now offers
  `[720] Every 12 hours` alongside the existing 1–60 minute options. The engine needed no
  changes: the interval math pins snapshots to the hour exactly 12 hours apart (first
  snapshot 12 hours after the top of the startup hour), and the dashboard's stale threshold
  scales with the interval (3x = 36 hours).
- `README.md` updated with the new interval option

### Fixed

- **Sign-in failure for accounts using two-factor authentication** -- Blink now
  signals a 2FA challenge as HTTP 202 with a TSV body instead of HTTP 412, which
  `blinkpy 0.25.5` misread as a generic "Login failed", so the 2FA code prompt
  never appeared. `blink_token.py` then crashed with an unhelpful `AttributeError`
  on `blink.urls.base_url`; it now exits with a clear, actionable error whenever
  login or 2FA setup fails.

### Changed

- `requirements.txt`: `blinkpy` 0.25.5 → 0.25.9 (handles the new 2FA 202+TSV
  response and logs the HTTP status + body on failed sign-in); `aiohttp`
  3.13.5 → 3.14.5, `requests` 2.32.5 → 2.34.2, `yarl` 1.23.0 → 1.25.1 to
  satisfy blinkpy 0.25.9 minimums

---

## [1.1.0] - 2026-06-28

### Fixed

- **Startup failure after power outage** -- thin client boots faster than
  router, leaving no network when the camera service starts. Fixed by adding
  an `ExecStartPre` ping gate to `blink-webcam.service` that loops on
  `ping 8.8.8.8` every 5 seconds until internet is reachable before allowing
  the Python process to launch. Also added `StartLimitIntervalSec=0` to
  prevent systemd from giving up on repeated restart attempts.

- **Camera service dying on startup network error** -- `Blink_Web_Cam.py`
  would call `return` and exit permanently if `setup_post_verify()` failed
  on first connect. Replaced with a `while True` retry loop that waits
  30 seconds and retries until the Blink cloud is reachable.

- **Weather widget stuck on "Service unavailable" after power outage** --
  `weather.js` fetched weather once on page load with no retry. If the
  fetch failed at boot (no network yet), the widget stayed in error state
  permanently. Fixed by adding a retry loop that retries every 30 seconds
  up to 10 times on failure, and a 30-minute polling interval to keep
  weather data fresh once recovered.

### Changed

- `Autostart/blink-webcam.service` updated with ping gate and
  `StartLimitIntervalSec=0`
- `README.md` updated with power outage notes in Autostart section
  and new Troubleshooting entry

---

## [1.0.0] - Initial Release

- Initial release of Blink WebCam Monitor
- Sequential camera snapshot polling via blinkpy
- Flask/Waitress web dashboard with camera carousel
- Tomorrow.io weather widget
- RainViewer + Mapbox animated radar
- NWS severe weather alerts
- NHC hurricane alerts
- Per-camera alert snooze
- Arm/disarm Blink system from dashboard
- Automatic photo and log retention/cleanup

---
id: blink-webcam-architecture
type: architecture-design
status: draft
title: Blink Web Cam — photo store and dashboard image display
---

## Drivers

- Saved photos under `cameras/` are the only record of what each camera captured; the
  dashboard must let the viewer tell **which camera** and **when** each displayed photo is.
  A downed camera must stay identifiable — the name shows in every card state,
  including offline.
- The saved files must stay raw camera bytes — the user explicitly declined burning any
  overlay into the JPEGs ("just overlay in html on the images when displayed on the web
  page"), so photos archived, moved, or shared off-machine are unchanged.

## Decisions

- **Presentation-only decoration.** All on-image annotation happens in the dashboard
  (HTML/CSS/JS over the `<img>`). No component re-encodes or annotates saved files —
  besides user intent, this is load-bearing: `camera_processor.check_duplicate()` hashes
  raw downloaded bytes against the hashes of saved files, so re-encoding would break
  duplicate detection.
- **Overlay chips.** Chips float over the image area — white text on a slightly opaque
  dark chip, `pointer-events: none`. The **name chip (top-left) renders on every card**;
  it is the card's only name display — the card's header bar was removed once the name
  moved onto the image. The **time chip (top-right)** renders only on cards with images
  and shows the **active** photo's capture time; offline cards show the name chip next
  to the OFFLINE badge.
- **Chip time source and format.** The time is parsed from the photo filename
  (`<name>_<YYYYMMDD_HHMMSS>.jpg`) and rendered as the filename's own zero-padded digits:
  `YYYY-MM-DD HH:MM:SS`. Deliberately NOT routed through the locale-aware `format.js`
  helpers (the page's single formatting point for everything else) — the fixed shape was
  a user choice for the chips.
- **Corner ownership on the image.** Chips are the base layer of the top corners
  (z-index below the alert badges). The snooze badge sits at top:48px on every card so
  it clears the name chip; the stale badge cascade (top:96px) sits below it. Top-right
  additionally stacks the offline/duplicate badges below the time chip; bottom-center is
  the carousel dots, bottom-right the snooze button.

## Invariants

- Files under `cameras/` are never written by any component except the capture loop's
  initial save; their bytes are the camera's own.
- A card has no header bar or caption: the name chip is the only name display and the
  top-right chip the only capture-time display. Stale/offline card state is signalled by
  the badges, the card border, and image dimming — not by header colouring.

## Out of scope

- Burning overlays into new or existing saved photos (explicitly declined by the user).
- Server-side per-image timestamps in the API — the filename already carries the time.

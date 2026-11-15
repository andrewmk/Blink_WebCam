---
id: blink-webcam-architecture
type: architecture-design
status: draft
title: Blink Web Cam — photo store and dashboard image display
---

## Drivers

- Saved photos under `cameras/` are the only record of what each camera captured; the
  dashboard must let the viewer tell **which camera** and **when** each displayed photo is.
- The saved files must stay raw camera bytes — the user explicitly declined burning any
  overlay into the JPEGs ("just overlay in html on the images when displayed on the web
  page"), so photos archived, moved, or shared off-machine are unchanged.

## Decisions

- **Presentation-only decoration.** All on-image annotation happens in the dashboard
  (HTML/CSS/JS over the `<img>`). No component re-encodes or annotates saved files —
  besides user intent, this is load-bearing: `camera_processor.check_duplicate()` hashes
  raw downloaded bytes against the hashes of saved files, so re-encoding would break
  duplicate detection.
- **Overlay chips.** Each card with images shows two chips floating over the displayed
  image: camera display name (top-left) and the **active** photo's capture time
  (top-right) — white text on a slightly opaque dark chip, `pointer-events: none`.
  Offline cards (no images) show no chips.
- **Chip time source and format.** The time is parsed from the photo filename
  (`<name>_<YYYYMMDD_HHMMSS>.jpg`) and rendered as the filename's own zero-padded digits:
  `YYYY-MM-DD HH:MM:SS`. Deliberately NOT routed through the locale-aware `format.js`
  helpers (the page's single formatting point for everything else) — the fixed shape was
  a user choice for the chips.
- **Corner ownership on the image.** Chips are the base layer of the top corners
  (z-index below the alert badges). The snooze badge shifts down (top:48px) on cards
  that show images so it clears the name chip; the stale badge cascade shifts with it.
  Top-right additionally stacks the offline/duplicate badges below the time chip;
  bottom-center is the carousel dots, bottom-right the snooze button.

## Invariants

- Files under `cameras/` are never written by any component except the capture loop's
  initial save; their bytes are the camera's own.
- The top-right chip is the only place a card shows a photo's capture time — the
  per-image caption in the card header was removed with the chips.

## Out of scope

- Burning overlays into new or existing saved photos (explicitly declined by the user).
- Server-side per-image timestamps in the API — the filename already carries the time.

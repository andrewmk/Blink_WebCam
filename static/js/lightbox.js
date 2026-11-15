// lightbox.js - Click-to-zoom image lightbox for dashboard photos
//
// Presentation-only: the lightbox reuses the card photos' own /image/... URLs.
// It snapshots the camera's photo list when opened, so a background refresh
// cannot disturb the photo being viewed (old files stay on disk).

// ============================================================================
// STATE
// ============================================================================

const lightboxState = {
    isOpen: false,
    cameraName: null,
    photos: [], // [{src, filename, alt}] snapshot taken when the lightbox opened
    index: 0
};

let lightboxEls = null; // element refs, grabbed on DOM ready

// ============================================================================
// CAPTION (camera name + capture time)
// ============================================================================

// Render the capture time exactly like the card's time chip: the filename's
// own zero-padded digits (YYYY-MM-DD HH:MM:SS), deliberately not routed
// through the locale-aware format.js helpers.
function formatLightboxTime(filename) {
    let filenameOnly = filename;
    if (filenameOnly.includes('/')) {
        filenameOnly = filenameOnly.split('/').pop();
    }
    const match = filenameOnly.match(/_(\d{8})_(\d{6})/);
    if (!match) return '';
    const dateStr = match[1];
    const timeStr = match[2];
    return dateStr.substring(0, 4) + '-' + dateStr.substring(4, 6) + '-' + dateStr.substring(6, 8) +
        ' ' + timeStr.substring(0, 2) + ':' + timeStr.substring(2, 4) + ':' + timeStr.substring(4, 6);
}

function showLightboxPhoto() {
    const photo = lightboxState.photos[lightboxState.index];
    if (!photo) return;

    lightboxEls.image.src = photo.src;
    lightboxEls.image.alt = photo.alt;

    const time = formatLightboxTime(photo.filename);
    lightboxEls.caption.textContent = time ? `${photo.alt}  \u00B7  ${time}` : photo.alt;

    // Arrows only make sense with more than one photo
    const multi = lightboxState.photos.length > 1;
    lightboxEls.prev.style.display = multi ? '' : 'none';
    lightboxEls.next.style.display = multi ? '' : 'none';
}

// ============================================================================
// OPEN / CLOSE / STEP
// ============================================================================

function openLightbox(cameraName, index) {
    const cam = window.cameras[cameraName];
    if (!cam || cam.images.length === 0) return;

    // Snapshot the carousel's photos at the moment of opening
    lightboxState.photos = Array.from(cam.images).map(img => ({
        src: img.src,
        filename: img.dataset.filename || '',
        alt: img.alt || cameraName
    }));
    lightboxState.index = Math.max(0, Math.min(index, lightboxState.photos.length - 1));
    lightboxState.cameraName = cameraName;
    lightboxState.isOpen = true;

    showLightboxPhoto();

    lightboxEls.overlay.classList.add('show');
    lightboxEls.overlay.setAttribute('aria-hidden', 'false');
    document.body.classList.add('lightbox-open');
    lightboxEls.close.focus();
}

function closeLightbox() {
    if (!lightboxState.isOpen) return;
    lightboxState.isOpen = false;
    lightboxState.cameraName = null;
    lightboxState.photos = [];
    lightboxState.index = 0;

    lightboxEls.overlay.classList.remove('show');
    lightboxEls.overlay.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('lightbox-open');
}

function stepLightbox(delta) {
    if (!lightboxState.isOpen || lightboxState.photos.length < 2) return;
    lightboxState.index = (lightboxState.index + delta + lightboxState.photos.length) % lightboxState.photos.length;
    showLightboxPhoto();
}

// ============================================================================
// WIRING
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    lightboxEls = {
        overlay: document.getElementById('lightbox'),
        image: document.getElementById('lightbox-image'),
        caption: document.getElementById('lightbox-caption'),
        close: document.getElementById('lightbox-close'),
        prev: document.getElementById('lightbox-prev'),
        next: document.getElementById('lightbox-next')
    };
    if (!lightboxEls.overlay) {
        console.warn('Lightbox elements not found; lightbox disabled');
        return;
    }

    // Click any card photo to open the lightbox on that photo.
    // The name/time chips are pointer-events:none, so clicks land on the img;
    // nav dots and the snooze button are separate elements and never trigger.
    document.addEventListener('click', function(e) {
        if (e.target.classList && e.target.classList.contains('camera-image')) {
            openLightbox(e.target.dataset.camera, parseInt(e.target.dataset.index, 10) || 0);
        }
    });

    // Dismiss: close X, backdrop click (outside the photo), or Esc
    lightboxEls.close.addEventListener('click', closeLightbox);
    lightboxEls.overlay.addEventListener('click', function(e) {
        if (e.target === lightboxEls.overlay) closeLightbox();
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeLightbox();
    });

    // Step through the camera's photos
    lightboxEls.prev.addEventListener('click', function() { stepLightbox(-1); });
    lightboxEls.next.addEventListener('click', function() { stepLightbox(1); });

    // Touch swipe: a decisive horizontal swipe steps one photo
    let touchStartX = null;
    let touchStartY = null;
    lightboxEls.overlay.addEventListener('touchstart', function(e) {
        if (e.touches.length === 1) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }
    }, {passive: true});
    lightboxEls.overlay.addEventListener('touchend', function(e) {
        if (touchStartX === null) return;
        const dx = e.changedTouches[0].clientX - touchStartX;
        const dy = e.changedTouches[0].clientY - touchStartY;
        touchStartX = null;
        touchStartY = null;
        if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
            stepLightbox(dx < 0 ? 1 : -1);
        }
    }, {passive: true});
});

// ============================================================================
// EXPOSE FOR USE BY OTHER MODULES
// ============================================================================

window.openLightbox = openLightbox;
window.closeLightbox = closeLightbox;
window.stepLightbox = stepLightbox;

/* Admin media: picker modal, image pickers, video source toggle, async video upload */
var AdminMedia = (function () {
  'use strict';

  // ── Video source type toggle ─────────────────────────────────────────────

  function initVideoToggle() {
    var sel = document.getElementById('video_source_type');
    if (!sel) return;
    updateVideoFields(sel.value);
    sel.addEventListener('change', function () { updateVideoFields(this.value); });
  }

  function updateVideoFields(type) {
    document.querySelectorAll('.js-video-id').forEach(function (el) {
      el.style.display = (type === 'youtube' || type === 'vimeo') ? '' : 'none';
    });
    document.querySelectorAll('.js-video-upload').forEach(function (el) {
      el.style.display = (type === 'upload') ? '' : 'none';
    });
    document.querySelectorAll('.js-video-subs').forEach(function (el) {
      el.style.display = type ? '' : 'none';
    });
  }

  // ── Image picker modal ───────────────────────────────────────────────────

  var _pickerTarget  = null;
  var _pickerPreview = null;
  var _quillTarget   = null;

  function buildModal() {
    if (!document.getElementById('mediaPickerOverlay')) {
      var overlay = document.createElement('div');
      overlay.id        = 'mediaPickerOverlay';
      overlay.className = 'media-picker-overlay';
      overlay.style.display = 'none';           // ← CRITICAL: hidden until explicitly opened
      overlay.innerHTML =
        '<div class="media-picker-modal">' +
          '<div class="media-picker-header">' +
            '<span>Seleccionar imagen</span>' +
            '<button type="button" class="media-picker-close" id="mediaPickerClose">&#x2715;</button>' +
          '</div>' +
          '<div class="media-picker-grid" id="mediaPickerGrid">' +
            '<p class="media-picker-loading">Cargando&hellip;</p>' +
          '</div>' +
        '</div>';
      document.body.appendChild(overlay);
    }

    // Wire events every time — guarded by ._wired flag to avoid duplicates
    var overlay = document.getElementById('mediaPickerOverlay');
    var closeBtn = document.getElementById('mediaPickerClose');
    if (closeBtn && !closeBtn._wired) {
      closeBtn._wired = true;
      closeBtn.addEventListener('click', closeModal);
    }
    if (overlay && !overlay._wired) {
      overlay._wired = true;
      overlay.addEventListener('click', function (e) {
        if (e.target === overlay) closeModal();
      });
    }
  }

  function openModal(targetId, previewId) {
    _pickerTarget  = targetId  || null;
    _pickerPreview = previewId || null;
    _quillTarget   = null;
    buildModal();
    document.getElementById('mediaPickerOverlay').style.display = 'flex';
    loadImages();
  }

  function openPickerForQuill(quillInstance) {
    _quillTarget   = quillInstance;
    _pickerTarget  = null;
    _pickerPreview = null;
    buildModal();
    document.getElementById('mediaPickerOverlay').style.display = 'flex';
    loadImages();
  }

  function closeModal() {
    var overlay = document.getElementById('mediaPickerOverlay');
    if (overlay) overlay.style.display = 'none';
    _quillTarget = null;
  }

  function loadImages() {
    var grid = document.getElementById('mediaPickerGrid');
    if (!grid) return;
    grid.innerHTML = '<p class="media-picker-loading">Cargando&hellip;</p>';

    fetch('/admin/media/api/images')
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (images) {
        if (!images.length) {
          grid.innerHTML = '<p class="media-picker-loading">No hay imágenes aún.</p>';
          return;
        }
        grid.innerHTML = '';
        images.forEach(function (img) {
          var label = img.title_es || img.title_en || img.filename;
          var item  = document.createElement('button');
          item.type      = 'button';
          item.className = 'media-picker-item';
          item.innerHTML =
            '<img src="' + img.thumbnail_url + '" alt="' + escAttr(img.alt_text_es || label) + '" />' +
            '<span>' + escText(label) + '</span>';
          item.addEventListener('click', function () { pickImage(img); });
          grid.appendChild(item);
        });
      })
      .catch(function (err) {
        grid.innerHTML = '<p class="media-picker-loading">Error al cargar imágenes: ' + escText(String(err)) + '</p>';
      });
  }

  function pickImage(imgData) {
    if (_quillTarget) {
      var range = _quillTarget.getSelection(true);
      var alt   = imgData.alt_text_es || imgData.alt_text_en || '';
      _quillTarget.clipboard.dangerouslyPasteHTML(
        range.index,
        '<img src="' + escAttr(imgData.url) + '" alt="' + escAttr(alt) + '">'
      );
    } else if (_pickerTarget) {
      var input = document.getElementById(_pickerTarget);
      if (input) input.value = imgData.url;
      if (_pickerPreview) showPreview(_pickerPreview, imgData.url);
    }
    closeModal();
  }

  // ── Image picker widget in forms ─────────────────────────────────────────

  function showPreview(previewId, url) {
    var preview = document.getElementById(previewId);
    if (!preview) return;
    preview.innerHTML = url ? '<img src="' + escAttr(url) + '" alt="" />' : '';
    var wrap     = preview.closest('.image-picker-wrap');
    var clearBtn = wrap && wrap.querySelector('.js-clear-image');
    if (clearBtn) clearBtn.style.display = url ? '' : 'none';
  }

  function initImagePickers() {
    document.querySelectorAll('.js-open-picker').forEach(function (btn) {
      btn.addEventListener('click', function () {
        openModal(this.dataset.target, this.dataset.preview);
      });
    });

    document.querySelectorAll('.js-quick-image-upload').forEach(function (input) {
      input.addEventListener('change', function () {
        var targetId  = this.dataset.target;
        var previewId = this.dataset.preview;
        var file = this.files[0];
        if (!file) return;
        var fd = new FormData();
        fd.append('file', file);
        fetch('/admin/media/upload', { method: 'POST', body: fd })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.url) {
              var urlInput = document.getElementById(targetId);
              if (urlInput) urlInput.value = data.url;
              if (previewId) showPreview(previewId, data.url);
            } else if (data.error) {
              alert(data.error);
            }
          });
        this.value = '';
      });
    });

    document.querySelectorAll('.js-clear-image').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var urlInput = document.getElementById(this.dataset.target);
        if (urlInput) urlInput.value = '';
        if (this.dataset.preview) showPreview(this.dataset.preview, '');
      });
    });

    // Show clear button on load if URL is already set
    document.querySelectorAll('.js-clear-image').forEach(function (btn) {
      var input = document.getElementById(btn.dataset.target);
      if (input && input.value) btn.style.display = '';
    });
  }

  // ── Async video upload with XHR progress ─────────────────────────────────

  function initVideoUpload(formId) {
    var fileInput = document.getElementById('videoFileInput');
    if (!fileInput) return;

    fileInput.addEventListener('change', function () {
      var file = this.files[0];
      if (!file) return;
      uploadVideoFile(file, formId);
    });
  }

  function uploadVideoFile(file, formId) {
    var statusDiv  = document.getElementById('videoUploadStatus');
    var bar        = document.getElementById('videoUploadBar');
    var text       = document.getElementById('videoUploadText');
    var valueInput = document.getElementById('video_source_value');  // hidden text input
    var submitBtn  = document.getElementById('formSubmitBtn');

    // Reset UI
    if (statusDiv) statusDiv.style.display = '';
    if (bar)  { bar.style.width = '0%'; bar.style.background = ''; }
    if (text) { text.textContent = 'Subiendo video… 0%'; text.style.color = ''; }
    if (submitBtn) { submitBtn.disabled = true; submitBtn.style.opacity = '.45'; }

    var xhr = new XMLHttpRequest();
    var fd  = new FormData();
    fd.append('file', file);

    // Upload progress (data flying to server: 0 → 100%)
    xhr.upload.addEventListener('progress', function (e) {
      if (!e.lengthComputable) return;
      var pct = Math.round(e.loaded / e.total * 100);
      if (bar)  bar.style.width = pct + '%';
      if (text) {
        text.textContent = pct < 100
          ? 'Subiendo video… ' + pct + '%'
          : 'Procesando video, espere un momento...';
      }
    });

    // Server response arrived (ffmpeg finished)
    xhr.addEventListener('load', function () {
      if (bar) bar.style.width = '100%';
      var data;
      try { data = JSON.parse(xhr.responseText); } catch (_) { data = {}; }

      if (xhr.status === 200 && data.url) {
        if (valueInput) valueInput.value = data.url;
        if (bar)  bar.style.background = '#2d6a2d';
        if (text) { text.textContent = '✓ Video subido correctamente'; text.style.color = '#1a5c1a'; }
        if (submitBtn) { submitBtn.disabled = false; submitBtn.style.opacity = ''; }
      } else {
        var msg = (data && data.error) ? data.error : 'Error desconocido (HTTP ' + xhr.status + ')';
        if (bar)  bar.style.background = '#8b1a1a';
        if (text) { text.textContent = 'Error: ' + msg; text.style.color = '#8b1a1a'; }
        if (submitBtn) { submitBtn.disabled = false; submitBtn.style.opacity = ''; }
      }
    });

    xhr.addEventListener('error', function () {
      if (bar)  bar.style.background = '#8b1a1a';
      if (text) { text.textContent = 'Error de red. Intenta de nuevo.'; text.style.color = '#8b1a1a'; }
      if (submitBtn) { submitBtn.disabled = false; submitBtn.style.opacity = ''; }
    });

    xhr.open('POST', '/admin/media/upload-video');
    xhr.send(fd);
  }

  // ── Tiny XSS-safe helpers ────────────────────────────────────────────────

  function escAttr(s) {
    return String(s).replace(/"/g, '&quot;').replace(/</g, '&lt;');
  }
  function escText(s) {
    return String(s).replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // ── Public API ───────────────────────────────────────────────────────────

  function init(formId) {
    buildModal();           // inject modal (hidden) + wire close handlers
    initVideoToggle();      // show/hide video fields based on source type
    initImagePickers();     // "select from library" + quick upload buttons
    initVideoUpload(formId); // XHR video upload with progress bar
  }

  return {
    init:              init,
    openPickerForQuill: openPickerForQuill,
  };
}());

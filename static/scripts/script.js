document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('loaded');

  // ── AI status check ──────────────────────────────────────────────
  const aiToggle = document.getElementById('use_ai_cleanup');
  const aiBadge  = document.getElementById('ai-badge');
  if (aiToggle) {
    fetch('/api/status')
      .then(r => r.json())
      .then(data => {
        if (data.ai_available) {
          aiToggle.disabled = false;
          aiBadge.textContent = 'Available';
          aiBadge.className = 'badge bg-success small';
        } else {
          aiBadge.textContent = 'Set OPENAI_API_KEY to enable';
          aiBadge.className = 'badge bg-secondary small';
          aiBadge.style.fontSize = '0.6rem';
        }
      })
      .catch(() => {
        aiBadge.textContent = 'Unavailable';
        aiBadge.className = 'badge bg-secondary small';
      });
  }

  // ── WaveSurfer player (post-upload state) ────────────────────────
  const waveformEl = document.getElementById('waveform');
  if (waveformEl && typeof WaveSurfer !== 'undefined') {
    const wavesurfer = WaveSurfer.create({
      container: '#waveform',
      waveColor: 'rgba(240, 234, 214, 0.45)',
      progressColor: '#2e7d32',
      cursorColor: '#F0EAD6',
      barWidth: 2,
      barGap: 1,
      height: 80,
      url: waveformEl.dataset.audioUrl,
    });

    const playBtn     = document.getElementById('play-pause');
    const timeDisplay = document.getElementById('time-display');
    const speedSelect = document.getElementById('speed-select');

    playBtn.addEventListener('click', () => wavesurfer.playPause());
    wavesurfer.on('play',   () => { playBtn.innerHTML = '&#9646;&#9646; Pause'; });
    wavesurfer.on('pause',  () => { playBtn.innerHTML = '&#9654; Play'; });
    wavesurfer.on('finish', () => { playBtn.innerHTML = '&#9654; Play'; });

    const fmt = s => {
      const m = Math.floor(s / 60);
      return `${m}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
    };
    wavesurfer.on('timeupdate', t => {
      timeDisplay.textContent = `${fmt(t)} / ${fmt(wavesurfer.getDuration())}`;
    });

    if (speedSelect) {
      speedSelect.addEventListener('change', () => {
        wavesurfer.setPlaybackRate(parseFloat(speedSelect.value));
      });
    }
  }

  // ── Reset button (post-upload state) ─────────────────────────────
  const resetBtn = document.getElementById('btn_reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      await fetch('/reset', { method: 'POST' }).catch(() => {});
      window.location.href = '/';
    });
  }

  // ── Upload form (pre-upload state) ───────────────────────────────
  const uploadForm = document.getElementById('uploadForm');
  if (!uploadForm) return;

  const dropZone       = document.getElementById('drop-zone');
  const fileInput      = document.getElementById('doc_pdf');
  const filenameEl     = document.getElementById('selected-filename');
  const previewSection = document.getElementById('preview-section');
  const previewText    = document.getElementById('preview-text');
  const previewCount   = document.getElementById('preview-word-count');
  const cancelBtn      = document.getElementById('btn-cancel');
  const progressOverlay = document.getElementById('progress-overlay');
  const progressBar    = document.getElementById('progress-bar');
  const progressStatus = document.getElementById('progress-status');

  let selectedFile = null;

  // Drag-and-drop handlers
  dropZone.addEventListener('click', e => {
    if (e.target.tagName === 'LABEL' || e.target.tagName === 'INPUT') return;
    fileInput.click();
  });
  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });
  dropZone.addEventListener('dragleave', e => {
    if (!dropZone.contains(e.relatedTarget)) {
      dropZone.classList.remove('drag-over');
    }
  });
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelected(file);
  });
  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleFileSelected(fileInput.files[0]);
  });

  async function handleFileSelected(file) {
    const MAX_BYTES = 16 * 1024 * 1024;
    const ALLOWED   = ['pdf', 'txt', 'docx'];
    const ext       = file.name.split('.').pop().toLowerCase();

    if (file.size > MAX_BYTES) {
      showError('File too large. Maximum size is 16 MB.');
      return;
    }
    if (!ALLOWED.includes(ext)) {
      showError('Unsupported file type. Please upload a PDF, DOCX, or TXT file.');
      return;
    }

    selectedFile = file;
    filenameEl.textContent = `✔ ${file.name}`;
    filenameEl.classList.remove('d-none');
    previewSection.classList.add('d-none');

    const fd = new FormData();
    fd.append('doc_pdf', file);

    try {
      const resp = await fetch('/preview', { method: 'POST', body: fd });
      const data = await resp.json();
      if (data.success) {
        previewText.textContent  = data.preview || '(No readable text found)';
        previewCount.textContent = `~${data.word_count.toLocaleString()} words`;
        previewSection.classList.remove('d-none');
      } else {
        previewText.textContent  = '(Preview unavailable — you can still convert)';
        previewCount.textContent = '';
        previewSection.classList.remove('d-none');
      }
    } catch {
      previewText.textContent  = '(Preview unavailable — you can still convert)';
      previewCount.textContent = '';
      previewSection.classList.remove('d-none');
    }
  }

  cancelBtn.addEventListener('click', async () => {
    await fetch('/reset', { method: 'POST' }).catch(() => {});
    selectedFile = null;
    fileInput.value = '';
    filenameEl.textContent = '';
    filenameEl.classList.add('d-none');
    previewSection.classList.add('d-none');
    previewText.textContent = '';
  });

  // Form submit → SSE flow
  uploadForm.addEventListener('submit', async e => {
    e.preventDefault();

    if (!selectedFile) {
      showError('Please select a file first.');
      return;
    }

    const formData = new FormData(uploadForm);
    formData.set('doc_pdf', selectedFile);
    formData.set(
      'use_ai_cleanup',
      document.getElementById('use_ai_cleanup').checked ? 'true' : 'false'
    );

    progressOverlay.style.display = 'flex';
    setProgress(0, 'Uploading…');

    let jobId;
    try {
      const resp = await fetch('/upload', { method: 'POST', body: formData });
      const data = await resp.json();
      if (!resp.ok) {
        hideProgress();
        showError(data.message || 'Upload failed.');
        return;
      }
      jobId = data.job_id;
    } catch {
      hideProgress();
      showError('Upload failed. Please try again.');
      return;
    }

    // Open SSE stream for progress
    const evtSource = new EventSource(`/progress/${jobId}`);

    evtSource.onmessage = e => {
      const data = JSON.parse(e.data);

      if (data.error) {
        evtSource.close();
        hideProgress();
        showError(data.error);
      } else if (data.status === 'cleaning') {
        setProgress(5, 'Cleaning text with AI…');
      } else if (data.done) {
        evtSource.close();
        setProgress(100, 'Done!');
        setTimeout(() => { window.location.href = '/'; }, 400);
      } else if (data.chunk !== undefined) {
        const pct = Math.round((data.chunk / data.total) * 100);
        setProgress(pct, `Converting chunk ${data.chunk} of ${data.total}…`);
      }
    };

    evtSource.onerror = () => {
      evtSource.close();
      hideProgress();
      showError('Connection lost during processing. Please try again.');
    };
  });

  function setProgress(pct, label) {
    progressBar.style.width   = `${pct}%`;
    progressStatus.textContent = label;
  }

  function hideProgress() {
    progressOverlay.style.display = 'none';
  }

  function showError(msg) {
    document.getElementById('error-detail').textContent = msg || '';
    new bootstrap.Modal(document.getElementById('failureModal')).show();
  }
});

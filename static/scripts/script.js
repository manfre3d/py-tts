/* ─── MojiEyes ──────────────────────────────────────────────────────
   Natural blinking at random intervals (3.5–7s), occasional double-blink.
   Animates the eye ellipse ry via RAF rather than CSS to keep full control.
─────────────────────────────────────────────────────────────────── */
class MojiEyes {
  constructor(prefix) {
    this.l = document.getElementById(`${prefix}-eye-l`);
    this.r = document.getElementById(`${prefix}-eye-r`);
    this._baseRy = 6.5;
    this._timer  = null;
  }

  start() {
    setTimeout(() => this._schedule(), 1800 + Math.random() * 2000);
  }

  stop() {
    clearTimeout(this._timer);
    this.l?.setAttribute('ry', this._baseRy);
    this.r?.setAttribute('ry', this._baseRy);
  }

  _schedule() {
    this._timer = setTimeout(() => {
      this._blink(() => {
        if (Math.random() < 0.2) {
          setTimeout(() => this._blink(() => this._schedule()), 180);
        } else {
          this._schedule();
        }
      });
    }, 3500 + Math.random() * 3800);
  }

  _blink(onDone) {
    if (!this.l) { onDone?.(); return; }
    const DURATION = 130;
    const start = performance.now();
    const step = (now) => {
      const p = Math.min((now - start) / DURATION, 1);
      const ry = p < 0.38 ? this._baseRy * (1 - p / 0.38)
               : p < 0.58 ? 0
               : this._baseRy * ((p - 0.58) / 0.42);
      this.l.setAttribute('ry', ry.toFixed(2));
      this.r.setAttribute('ry', ry.toFixed(2));
      if (p < 1) requestAnimationFrame(step);
      else {
        this.l.setAttribute('ry', this._baseRy);
        this.r.setAttribute('ry', this._baseRy);
        onDone?.();
      }
    };
    requestAnimationFrame(step);
  }
}

/* ─── MojiMouth ─────────────────────────────────────────────────────
   Two modes:
   1. Fake oscillator  — used during conversion (no audio yet)
   2. Peaks playback   — real lip-sync driven by WaveSurfer's decoded
                         amplitude data, sampled per-frame via RAF with
                         linear interpolation between peak samples.

   Why peaks instead of AudioContext + AnalyserNode:
   AudioContext created outside a user gesture is immediately suspended
   by browser autoplay policy. Resuming it asynchronously inside a play
   handler is unreliable across Chrome/Safari/Firefox. WaveSurfer already
   decoded the audio — exportPeaks() gives us the same amplitude signal
   without touching AudioContext at all.
─────────────────────────────────────────────────────────────────── */
class MojiMouth {
  constructor(prefix) {
    this.mouth  = document.getElementById(`${prefix}-mouth`);
    this.teeth  = document.getElementById(`${prefix}-teeth`);
    this.cavity = document.getElementById(`${prefix}-cavity`);
    this._raf    = null;
    this._phase  = 0;
    this._smooth = 0;
    this._peaks  = null;
    this._ws     = null;
  }

  /* Morph the mouth. t = 0 (closed smile) → 1 (wide open).
     Single closed path: upper-lip arc → lower-lip arc → Z.
     No split-path seam, no two-halves artefact. */
  set(t) {
    if (!this.mouth) return;
    t = Math.max(0, Math.min(1, t));

    const cy = 67;
    const lx = (37 - t).toFixed(2);        // corners spread slightly as mouth opens
    const rx = (63 + t).toFixed(2);
    const uc = (64 - t * 4).toFixed(2);    // upper control rises:  64 → 60
    const lc = (75 + t * 5).toFixed(2);    // lower control drops:  75 → 80

    // One continuous closed shape — upper arc then lower arc, connected at corners
    this.mouth.setAttribute('d',
      `M${lx},${cy} Q50,${uc} ${rx},${cy} Q50,${lc} ${lx},${cy} Z`);

    // Teeth appear after 10% open, cavity after 35%
    if (this.teeth)
      this.teeth.setAttribute('ry', (Math.max(0, (t - 0.10) / 0.90) * 5).toFixed(2));
    if (this.cavity) {
      this.cavity.setAttribute('ry', (Math.max(0, (t - 0.35) / 0.65) * 4.5).toFixed(2));
      this.cavity.setAttribute('cy', (72 + t * 1.5).toFixed(2));
    }
  }

  /* ── Mode 1: fake oscillator (during conversion) ── */
  startFake() {
    this.stopAll();
    this._phase = Math.random() * Math.PI * 2;
    const tick = () => {
      this._phase += 0.095;
      const raw = Math.sin(this._phase) * 0.35 + Math.sin(this._phase * 2.3) * 0.22 + 0.28;
      this._smooth = this._smooth * 0.78 + raw * 0.22;
      this.set(Math.max(0, this._smooth));
      this._raf = requestAnimationFrame(tick);
    };
    this._raf = requestAnimationFrame(tick);
  }

  /* ── Mode 2: peaks-driven playback ── */
  setupPeaks(ws) {
    this._ws = ws;
    try {
      // Request 800 samples for smooth interpolation across typical TTS lengths
      const raw = ws.exportPeaks({ maxLength: 800 });
      // exportPeaks returns number[][] (one array per channel)
      const ch = (Array.isArray(raw[0])) ? raw[0] : raw;
      this._peaks = ch;
    } catch (e) {
      this._peaks = null;
    }
  }

  startPeaks() {
    if (!this._peaks || !this._ws) return;
    this.stopAll();
    const peaks = this._peaks;
    const ws    = this._ws;

    const tick = () => {
      const duration = ws.getDuration();
      if (duration > 0) {
        const progress = ws.getCurrentTime() / duration;
        // Linear interpolation between adjacent peak samples → no stepping
        const exactIdx = progress * (peaks.length - 1);
        const lo  = Math.floor(exactIdx);
        const hi  = Math.min(lo + 1, peaks.length - 1);
        const raw = Math.abs(peaks[lo] || 0) * (1 - (exactIdx - lo))
                  + Math.abs(peaks[hi] || 0) * (exactIdx - lo);
        // Smooth to hide low peak resolution; scale up since TTS peaks ~0.2-0.6
        this._smooth = this._smooth * 0.80 + raw * 0.20;
        this.set(Math.min(this._smooth * 2.2, 1));
      }
      this._raf = requestAnimationFrame(tick);
    };
    this._raf = requestAnimationFrame(tick);
  }

  pausePeaks() {
    cancelAnimationFrame(this._raf);
    this._raf = null;
    this._smooth = 0;
    this.set(0);
  }

  stopAll() {
    cancelAnimationFrame(this._raf);
    this._raf = null;
    this._smooth = 0;
    this.set(0);
  }
}

/* ─── Boot ──────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('loaded');

  const heroWrapper = document.getElementById('hero-wrapper');
  const heroMouth   = new MojiMouth('hero');
  const heroEyes    = new MojiEyes('hero');
  const ovMouth     = new MojiMouth('ov');
  const ovEyes      = new MojiEyes('ov');

  heroEyes.start();
  ovEyes.start();

  function setHeroState(state) {
    if (!heroWrapper) return;
    heroWrapper.classList.remove('talking', 'done');
    if (state) heroWrapper.classList.add(state);
  }

  // ── AI status ────────────────────────────────────────────────────
  const aiToggle = document.getElementById('use_ai_cleanup');
  const aiBadge  = document.getElementById('ai-badge');
  if (aiToggle) {
    fetch('/api/status')
      .then(r => r.json())
      .then(d => {
        if (d.ai_available) {
          aiToggle.disabled   = false;
          aiBadge.textContent = 'Available';
          aiBadge.className   = 'badge bg-success';
        } else {
          aiBadge.textContent = 'Set OPENAI_API_KEY';
          aiBadge.className   = 'badge bg-secondary';
        }
      })
      .catch(() => { aiBadge.textContent = 'Unavailable'; aiBadge.className = 'badge bg-secondary'; });
  }

  // ── WaveSurfer player ─────────────────────────────────────────────
  const waveformEl = document.getElementById('waveform');
  if (waveformEl && typeof WaveSurfer !== 'undefined') {
    const wavesurfer = WaveSurfer.create({
      container: '#waveform',
      waveColor: 'rgba(167,139,250,0.38)',
      progressColor: '#7C3AED',
      cursorColor: '#A78BFA',
      barWidth: 2,
      barGap: 1,
      height: 80,
      url: waveformEl.dataset.audioUrl,
    });

    const playBtn     = document.getElementById('play-pause');
    const timeDisplay = document.getElementById('time-display');
    const speedSelect = document.getElementById('speed-select');

    // Extract amplitude peaks once the audio is decoded
    wavesurfer.on('ready', () => {
      heroMouth.setupPeaks(wavesurfer);
    });

    playBtn.addEventListener('click', () => wavesurfer.playPause());

    wavesurfer.on('play', () => {
      playBtn.innerHTML = '&#9646;&#9646; Pause';
      setHeroState('talking');
      heroMouth.startPeaks();
    });

    wavesurfer.on('pause', () => {
      playBtn.innerHTML = '&#9654; Play';
      setHeroState(null);
      heroMouth.pausePeaks();
    });

    wavesurfer.on('finish', () => {
      playBtn.innerHTML = '&#9654; Play';
      heroMouth.pausePeaks();
      setHeroState('done');
      setTimeout(() => setHeroState(null), 750);
    });

    const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
    wavesurfer.on('timeupdate', t => {
      timeDisplay.textContent = `${fmt(t)} / ${fmt(wavesurfer.getDuration())}`;
    });

    if (speedSelect) {
      speedSelect.addEventListener('change', () => {
        wavesurfer.setPlaybackRate(parseFloat(speedSelect.value));
      });
    }
  }

  // ── Reset button ──────────────────────────────────────────────────
  const resetBtn = document.getElementById('btn_reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      heroMouth.stopAll();
      heroEyes.stop();
      await fetch('/reset', { method: 'POST' }).catch(() => {});
      window.location.href = '/';
    });
  }

  // ── Upload form ───────────────────────────────────────────────────
  const uploadForm = document.getElementById('uploadForm');
  if (!uploadForm) return;

  const dropZone        = document.getElementById('drop-zone');
  const fileInput       = document.getElementById('doc_pdf');
  const filenameEl      = document.getElementById('selected-filename');
  const previewSection  = document.getElementById('preview-section');
  const previewText     = document.getElementById('preview-text');
  const previewCount    = document.getElementById('preview-word-count');
  const cancelBtn       = document.getElementById('btn-cancel');
  const progressOverlay = document.getElementById('progress-overlay');
  const progressBarFill = document.getElementById('progress-bar-fill');
  const progressStatus  = document.getElementById('progress-status');

  let selectedFile = null;

  dropZone.addEventListener('click', e => {
    if (e.target.tagName === 'LABEL' || e.target.tagName === 'INPUT') return;
    fileInput.click();
  });
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', e => {
    if (!dropZone.contains(e.relatedTarget)) dropZone.classList.remove('drag-over');
  });
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const f = e.dataTransfer.files[0];
    if (f) handleFileSelected(f);
  });
  fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleFileSelected(fileInput.files[0]); });

  async function handleFileSelected(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (file.size > 16 * 1024 * 1024) { showError('File too large. Maximum size is 16 MB.'); return; }
    if (!['pdf', 'txt', 'docx'].includes(ext)) { showError('Unsupported file type. Please upload a PDF, DOCX, or TXT file.'); return; }

    selectedFile = file;
    filenameEl.textContent = `✔ ${file.name}`;
    filenameEl.classList.remove('d-none');
    previewSection.classList.add('d-none');

    const fd = new FormData();
    fd.append('doc_pdf', file);
    try {
      const resp = await fetch('/preview', { method: 'POST', body: fd });
      const data = await resp.json();
      previewText.textContent  = data.success ? (data.preview || '(No readable text found)') : '(Preview unavailable — you can still convert)';
      previewCount.textContent = data.success ? `~${data.word_count.toLocaleString()} words` : '';
    } catch {
      previewText.textContent = '(Preview unavailable — you can still convert)';
      previewCount.textContent = '';
    }
    previewSection.classList.remove('d-none');
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

  uploadForm.addEventListener('submit', async e => {
    e.preventDefault();
    if (!selectedFile) { showError('Please select a file first.'); return; }

    const formData = new FormData(uploadForm);
    formData.set('doc_pdf', selectedFile);
    formData.set('use_ai_cleanup', document.getElementById('use_ai_cleanup').checked ? 'true' : 'false');

    progressOverlay.style.display = 'flex';
    ovMouth.startFake();
    setProgress(0, 'Uploading…');

    let jobId;
    try {
      const resp = await fetch('/upload', { method: 'POST', body: formData });
      const data = await resp.json();
      if (!resp.ok) { hideProgress(); showError(data.message || 'Upload failed.'); return; }
      jobId = data.job_id;
    } catch {
      hideProgress();
      showError('Upload failed. Please try again.');
      return;
    }

    const evtSource = new EventSource(`/progress/${jobId}`);
    evtSource.onmessage = e => {
      const data = JSON.parse(e.data);
      if (data.error) {
        evtSource.close(); hideProgress(); showError(data.error);
      } else if (data.status === 'cleaning') {
        setProgress(5, 'Cleaning text with AI…');
      } else if (data.done) {
        evtSource.close();
        setProgress(100, 'Done!');
        ovMouth.stopAll();
        setHeroState('done');
        setTimeout(() => { window.location.href = '/'; }, 500);
      } else if (data.chunk !== undefined) {
        setProgress(Math.round((data.chunk / data.total) * 100), `Converting chunk ${data.chunk} of ${data.total}…`);
      }
    };
    evtSource.onerror = () => { evtSource.close(); hideProgress(); showError('Connection lost. Please try again.'); };
  });

  function setProgress(pct, label) {
    progressBarFill.style.width = `${pct}%`;
    progressStatus.textContent  = label;
  }
  function hideProgress() {
    progressOverlay.style.display = 'none';
    ovMouth.stopAll();
  }
  function showError(msg) {
    document.getElementById('error-detail').textContent = msg || '';
    new bootstrap.Modal(document.getElementById('failureModal')).show();
  }
});

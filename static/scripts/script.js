const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('loaded');

  const audioPlayer = document.getElementById('audio-player');
  if (audioPlayer) {
    audioPlayer.scrollIntoView({ behavior: 'smooth' });
  }

  const uploadForm = document.getElementById('uploadForm');
  if (!uploadForm) return;

  uploadForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const fileInput = document.getElementById('doc_pdf');
    if (fileInput.files[0] && fileInput.files[0].size > MAX_FILE_SIZE_BYTES) {
      alert(`File too large. Maximum size is ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    document.getElementById('spinner-overlay').style.display = 'flex';

    try {
      const formData = new FormData(this);
      const response = await fetch('/upload', { method: 'POST', body: formData });
      const data = await response.json();

      if (data.success) {
        window.location.href = '/';
      } else {
        new bootstrap.Modal(document.getElementById('failureModal')).show();
      }
    } catch {
      new bootstrap.Modal(document.getElementById('failureModal')).show();
    } finally {
      document.getElementById('spinner-overlay').style.display = 'none';
    }
  });

  const resetBtn = document.getElementById('btn_reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      try {
        await fetch('/reset', { method: 'POST' });
      } finally {
        window.location.href = '/';
      }
    });
  }
});

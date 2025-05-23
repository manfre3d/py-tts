document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('uploadForm');
  if (!uploadForm) return; // fallback if form doesn't exist

  uploadForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    document.getElementById('spinner-overlay').style.display = 'flex';

    const formData = new FormData(this);
    const response = await fetch("/upload", {
      method: "POST",
      body: formData
    });

    const data = await response.json();
    document.getElementById('spinner-overlay').style.display = 'none';

    if (data.success) {
        window.location.href = "/";
    } else {
      //to do add fail alert
    }
  });
});
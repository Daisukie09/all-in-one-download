const form = document.getElementById('dl-form');
const msg = document.getElementById('msg');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const url = new FormData(form).get('url');
  msg.textContent = 'Validating URL…';
  try{
    const u = new URL(url);
    if (!/^https?:$/.test(u.protocol)) throw new Error('Only http/https supported');
  }catch(err){ msg.textContent = 'Invalid URL'; return; }
  msg.textContent = 'Starting download…';
  // Trigger browser download by navigating to the API endpoint
  const api = '/api/download?url=' + encodeURIComponent(url);
  window.location.href = api;
  setTimeout(()=>{ msg.textContent = 'If your download didn\'t start, the host may be blocked or file too large.'; }, 4000);
});

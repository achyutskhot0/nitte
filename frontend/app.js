const API = window.location.origin;

const fileInput = document.getElementById('file');
fileInput?.addEventListener('change', () => {
  const names = Array.from(fileInput.files || []).map(f => f.name).join(', ');
  document.getElementById('file-name').textContent = names || 'No files selected';
});

async function upload(){
  const files = document.getElementById('file').files;
  if(!files || files.length === 0){ alert('Select at least one file'); return; }
  const fd = new FormData();
  for (const f of files) fd.append('files', f);
  const r = await fetch(API + "/upload", { method: "POST", body: fd });
  const j = await r.json();
  await loadSummary(j.file_ids[0]);
}

function switchTab(t, ev){
  document.querySelectorAll('#tabs li').forEach(li=>li.classList.remove('is-active'));
  ev?.target?.parentElement?.classList?.add('is-active');
  loadTab(t);
}

async function loadSummary(fid){
  const res = await fetch(API + "/summaries/" + fid, { method: 'POST' });
  const data = await res.json();
  window.data = data;
  window.data._fid = fid;
  switchTab('lawyer');
}

function loadTab(t){
  const box = document.getElementById('content');
  if(!window.data){ box.innerHTML = '<em>Upload a document to see results.</em>'; return; }
  if(t==='lawyer') box.innerHTML = `<pre>${JSON.stringify(window.data.lawyer, null, 2)}</pre>`;
  if(t==='citizen') box.innerHTML = `<pre>${JSON.stringify(window.data.citizen, null, 2)}</pre>`;
  if(t==='next') box.innerHTML = `<div style="display:flex;gap:1rem;align-items:flex-start;">
    <pre style="flex:1;">${JSON.stringify(window.data.next, null, 2)}</pre>
    <a class="button is-link" href="${API + "/ical/" + window.data._fid}" download="deadlines.ics">Download iCal</a>
  </div>`;
}

window.upload = upload;
window.switchTab = switchTab;

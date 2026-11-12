// Browser-only demo frontend for C1; JWT stays in memory (not localStorage).
const $ = (selector) => document.querySelector(selector);
const form = $('#parcel-form');
const feedback = $('#feedback');
const submit = $('#submit-parcel');
let bearerToken = '';

function message(text, kind = 'error') {
  feedback.hidden = false;
  feedback.className = `feedback ${kind}`;
  feedback.textContent = text;
}
function clearMessage() { feedback.hidden = true; }
function setSession(active, text = 'Courier authenticated') {
  $('#session-state').textContent = active ? text : 'Not authenticated';
  $('#session-state').classList.toggle('ok', active);
  $('#logout').hidden = !active;
}
async function request(path, options = {}) {
  const headers = { ...(options.body ? {'Content-Type':'application/json'} : {}), ...options.headers };
  if (bearerToken) headers.Authorization = `Bearer ${bearerToken}`;
  const res = await fetch(path, {...options, headers });
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401) setSession(false);
    const detail = payload.detail;
    const errorText = typeof detail === 'string' ? detail : Array.isArray(detail)
      ? detail.map(x => x.msg.replace(/^Value error, /, '')).join('; ')
      : `Request failed (${res.status})`;
    throw new Error(errorText);
  }
  return payload;
}
const dateFmt = (value) => new Date(value).toLocaleDateString(undefined,{day:'2-digit',month:'short',year:'numeric'});

async function refreshParcels() {
  if (!bearerToken) {
    ['total','awaiting','upcoming'].forEach(key => $(`#stat-${key}`).textContent = '—');
    showEmpty('Authenticate to view your parcels.');
    return;
  }
  try {
    const parcels = await request('/api/parcels');
    $('#stat-total').textContent = parcels.length;
    $('#stat-awaiting').textContent = parcels.filter(p => p.status === 'REGISTERED').length;
    const now = Date.now();
    $('#stat-upcoming').textContent = parcels.filter(p => new Date(p.expectedDeliveryAt).getTime() >= now && new Date(p.expectedDeliveryAt).getTime() < now+7*24*3600*1000).length;
    if (!parcels.length) { showEmpty('No parcels registered yet. Your first parcel will appear here.'); return; }
    const list = $('#parcel-list');
    list.replaceChildren();
    for (const parcel of parcels) {
      const row = document.createElement('div'); row.className = 'parcel-row';
      const info = document.createElement('div');
      const id = document.createElement('div'); id.className = 'parcel-id'; id.textContent = parcel.trackingNumber;
      const meta = document.createElement('div'); meta.className = 'parcel-meta'; meta.textContent = `${parcel.size}  ·  Expected ${dateFmt(parcel.expectedDeliveryAt)}`;
      info.append(id,meta);
      const right = document.createElement('div'); right.className = 'parcel-right';
      const badge = document.createElement('div'); badge.className = 'state'; badge.textContent = parcel.status;
      const date = document.createElement('div'); date.className = 'parcel-date'; date.textContent = `Added ${dateFmt(parcel.createdAt)}`;
      right.append(badge,date); row.append(info,right); list.append(row);
    }
  } catch(e) { showEmpty(e.message); }
}
function showEmpty(text) {
  const wrapper = document.createElement('div'); wrapper.className = 'empty';
  const icon = document.createElement('div'); icon.className = 'empty-icon'; icon.textContent = '▤';
  const heading = document.createElement('strong'); heading.textContent = 'No parcels to show';
  const detail = document.createElement('p'); detail.textContent = text;
  wrapper.append(icon,heading,detail); $('#parcel-list').replaceChildren(wrapper);
}
$('#token-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  bearerToken = $('#token').value.trim(); $('#token').value = '';
  if (!bearerToken) { message('Please paste a signed courier JWT.'); return; }
  setSession(true, 'Courier token provided'); clearMessage();
  await refreshParcels();
});
$('#logout').addEventListener('click', () => {bearerToken='';setSession(false);clearMessage();refreshParcels();});
$('#refresh').addEventListener('click', refreshParcels);
$('#notes').addEventListener('input', (event) => $('#note-count').textContent = `${event.target.value.length} / 500`);

form.addEventListener('submit', async (event) => {
  event.preventDefault(); clearMessage();
  if (!bearerToken) { message('Authenticate with a courier token before registering a parcel.'); return; }
  if (!form.reportValidity()) return;
  const delivery = new Date($('#delivery').value);
  if (Number.isNaN(delivery.getTime())) { message('Choose a valid expected delivery date and time.'); return; }
  submit.disabled = true;
  try {
    const result = await request('/api/parcels', { method: 'POST', body: JSON.stringify({
      barcode: $('#barcode').value, size: $('#size').value,
      expectedDeliveryAt: delivery.toISOString(), notes: $('#notes').value,
    })});
    message(`Parcel registered successfully. Parcel ID: ${result.parcelId}`, 'success');
    form.reset(); $('#note-count').textContent = '0 / 500';
    await refreshParcels();
  } catch (error) { message(error.message); }
  finally { submit.disabled = false; }
});

async function init() {
  const tomorrow = new Date(Date.now() + 24 * 3600_000);
  const local = new Date(tomorrow.getTime()-tomorrow.getTimezoneOffset()*60000);
  $('#delivery').min = new Date(Date.now() - new Date().getTimezoneOffset()*60000).toISOString().slice(0,16);
  $('#delivery').value = local.toISOString().slice(0,16);
  try {
    const config = await request('/api/config');
    if (config.demoMode) {
      $('#demo-login').hidden = false;
      $('#demo-login').addEventListener('click', async () => {
        try {const data = await request('/api/demo-session'); bearerToken=data.token;
          setSession(true, 'Local demo courier'); clearMessage(); await refreshParcels();}
        catch(e) { message(e.message); }
      });
    }
  } catch(e) { message(`Cannot contact backend: ${e.message}`); }
}
init();

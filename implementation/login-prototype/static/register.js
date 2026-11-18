import {
  api, busy, detectKind, KIND_HINTS, session, setMessage, showDevCode, showKind,
} from './common.js';

const $ = (selector) => document.querySelector(selector);
const detailsForm = $('#details-form');
const codeForm = $('#code-form');
const message = $('#message');
const STAFF_CANNOT_REGISTER = "Courier and administrator accounts are provided by the company and can't be registered here.";
let name = '';
let identifier = '';

if (session.token()) location.replace('/dashboard');

async function sendCode({ resend = false } = {}) {
  const result = await api('/api/auth/register', { method: 'POST', body: { name, identifier } });
  $('#code-who').textContent = identifier;
  $('#code-sent').textContent = result.message;
  showDevCode($('#dev-code'), $('#dev-code-value'), result.devCode);
  if (resend) {
    $('#code').value = '';
    setMessage(message, 'A new code has been sent. Earlier codes no longer work.', 'success');
    return;
  }
  detailsForm.hidden = true;
  codeForm.hidden = false;
  setMessage(message, '');
  $('#code').focus();
}

$('#identifier').addEventListener('input', (event) => {
  showKind($('#kind'), detectKind(event.target.value), { staffNotAllowed: true });
});

detailsForm.addEventListener('submit', (event) => {
  event.preventDefault();
  name = $('#name').value.trim();
  identifier = $('#identifier').value.trim();
  const kind = detectKind(identifier);
  if (!name) { setMessage(message, 'Enter your name.'); return; }
  if (kind === 'COURIER' || kind === 'ADMIN' || kind === 'STAFF_INCOMPLETE') {
    setMessage(message, STAFF_CANNOT_REGISTER);
    return;
  }
  if (kind !== 'EMAIL' && kind !== 'PHONE') {
    setMessage(message, kind ? KIND_HINTS[kind] : 'Enter your email address or phone number.');
    return;
  }
  busy(detailsForm, () => sendCode()).catch((error) => setMessage(message, error.message));
});

codeForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const code = $('#code').value.trim();
  if (!/^\d{6}$/.test(code)) { setMessage(message, 'Enter the 6-digit code.'); return; }
  busy(codeForm, async () => {
    const result = await api('/api/auth/register/verify', { method: 'POST', body: { identifier, code } });
    if (!session.save(result.token)) {
      setMessage(message, 'Account created, but your browser blocked session storage. Sign in again.');
      return;
    }
    location.replace(result.redirect || '/dashboard');
  }).catch((error) => setMessage(message, error.message));
});

$('#resend').addEventListener('click', () => {
  busy(codeForm, () => sendCode({ resend: true })).catch((error) => setMessage(message, error.message));
});

$('#back').addEventListener('click', () => {
  $('#code').value = '';
  codeForm.hidden = true;
  detailsForm.hidden = false;
  setMessage(message, '');
  $('#identifier').focus();
});

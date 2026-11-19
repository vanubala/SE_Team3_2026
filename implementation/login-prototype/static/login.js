import {
  api, busy, detectKind, KIND_HINTS, session, setMessage, showDevCode, showKind,
} from './common.js';

const $ = (selector) => document.querySelector(selector);
const forms = { identify: $('#identify-form'), password: $('#password-form'), code: $('#code-form') };
const message = $('#message');
let identifier = '';

if (session.token()) location.replace('/dashboard');

const params = new URLSearchParams(location.search);
if (params.has('expired')) setMessage($('#notice'), 'Your session has ended. Please sign in again.', 'info');
if (params.has('signedout')) setMessage($('#notice'), 'You have been signed out.', 'info');

function goTo(step) {
  Object.entries(forms).forEach(([name, form]) => { form.hidden = name !== step; });
  setMessage(message, '');
  forms[step].querySelector('input').focus();
}

function finish(result) {
  if (!session.save(result.token)) {
    setMessage(message, 'Your browser blocked session storage, so you cannot stay signed in.');
    return;
  }
  location.replace(result.redirect || '/dashboard');
}

async function sendCode({ resend = false } = {}) {
  const result = await api('/api/auth/code', { method: 'POST', body: { identifier } });
  $('#code-who').textContent = identifier;
  $('#code-sent').textContent = result.message;
  showDevCode($('#dev-code'), $('#dev-code-value'), result.devCode);
  if (resend) {
    $('#code').value = '';
    setMessage(message, 'A new code has been sent. Earlier codes no longer work.', 'success');
  } else {
    goTo('code');
  }
}

$('#identifier').addEventListener('input', (event) => showKind($('#kind'), detectKind(event.target.value)));

forms.identify.addEventListener('submit', (event) => {
  event.preventDefault();
  identifier = $('#identifier').value.trim();
  const kind = detectKind(identifier);
  if (kind === 'COURIER' || kind === 'ADMIN') {
    identifier = identifier.toUpperCase();
    $('#password-who').textContent = identifier;
    goTo('password');
    return;
  }
  if (kind === 'EMAIL' || kind === 'PHONE') {
    busy(forms.identify, () => sendCode()).catch((error) => setMessage(message, error.message));
    return;
  }
  setMessage(message, kind ? KIND_HINTS[kind] : 'Enter your company ID, email address or phone number.');
});

forms.password.addEventListener('submit', (event) => {
  event.preventDefault();
  const password = $('#password').value;
  if (!password) { setMessage(message, 'Enter your password.'); return; }
  busy(forms.password, async () => {
    const result = await api('/api/auth/login', { method: 'POST', body: { identifier, password } });
    finish(result);
  }).catch((error) => {
    $('#password').value = '';
    setMessage(message, error.message);
  });
});

forms.code.addEventListener('submit', (event) => {
  event.preventDefault();
  const code = $('#code').value.trim();
  if (!/^\d{6}$/.test(code)) { setMessage(message, 'Enter the 6-digit code.'); return; }
  busy(forms.code, async () => {
    const result = await api('/api/auth/code/verify', { method: 'POST', body: { identifier, code } });
    finish(result);
  }).catch((error) => setMessage(message, error.message));
});

$('#resend').addEventListener('click', () => {
  busy(forms.code, () => sendCode({ resend: true })).catch((error) => setMessage(message, error.message));
});

document.querySelectorAll('[data-back]').forEach((button) => button.addEventListener('click', () => {
  $('#password').value = '';
  $('#code').value = '';
  goTo('identify');
}));

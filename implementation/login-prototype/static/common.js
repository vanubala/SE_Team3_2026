// Helpers shared by the sign-in, registration and dashboard pages.

const TOKEN_KEY = 'spl.session.token';

// The session token lives in sessionStorage: it survives moving between the
// pages of this tab and disappears when the tab is closed.
export const session = {
  token() {
    try { return sessionStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; }
  },
  save(token) {
    try { sessionStorage.setItem(TOKEN_KEY, token); return true; } catch { return false; }
  },
  clear() {
    try { sessionStorage.removeItem(TOKEN_KEY); } catch { /* storage unavailable */ }
  },
};

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

const FIELD_LABELS = { identifier: 'ID, email or phone', password: 'Password', code: 'Code', name: 'Name' };

function describeError(data, status) {
  const detail = data && data.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail.map((item) => {
      const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : '';
      if (field === 'code') return 'Enter the 6-digit code.';
      const text = String(item.msg || '').replace(/^Value error, /, '');
      return `${FIELD_LABELS[field] || field}: ${text}.`;
    }).join(' ');
  }
  return `Something went wrong (error ${status}).`;
}

export async function api(path, { method = 'GET', body, auth = false } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && session.token()) headers.Authorization = `Bearer ${session.token()}`;
  let response;
  try {
    response = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  } catch {
    throw new ApiError('Cannot reach the server. Is it still running?', 0);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(describeError(data, response.status), response.status);
  return data;
}

// Mirrors app/identifiers.py. Only used to guide the person while typing;
// the server makes the real decision.
export function detectKind(raw) {
  const value = raw.trim();
  if (!value) return null;
  if (value.includes('@')) {
    return /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(value) ? 'EMAIL' : 'EMAIL_INCOMPLETE';
  }
  if (/^(co|ad)\d/i.test(value)) {
    if (/^co\d{5}$/i.test(value)) return 'COURIER';
    if (/^ad\d{5}$/i.test(value)) return 'ADMIN';
    return 'STAFF_INCOMPLETE';
  }
  const phone = value.replace(/[\s\-.()]/g, '').replace(/^00/, '+');
  if (/^\+[1-9]\d{7,14}$/.test(phone)) return 'PHONE';
  if (/^\+?\d+$/.test(phone)) return 'PHONE_INCOMPLETE';
  return 'UNKNOWN';
}

export const KIND_TEXT = {
  COURIER: 'Courier account - sign in with your password',
  ADMIN: 'Administrator account - sign in with your password',
  EMAIL: 'Sender / recipient - we will email you a code',
  PHONE: 'Sender / recipient - we will text you a code',
  STAFF_INCOMPLETE: 'Company IDs are CO or AD followed by 5 digits',
  EMAIL_INCOMPLETE: 'Keep typing your email address',
  PHONE_INCOMPLETE: 'Use international format, for example +352 621 123 456',
  UNKNOWN: 'Enter a company ID, an email address or a phone number',
};

export const KIND_HINTS = {
  STAFF_INCOMPLETE: 'Company IDs are CO or AD followed by 5 digits, for example CO00001.',
  EMAIL_INCOMPLETE: 'Enter a valid email address.',
  PHONE_INCOMPLETE: 'Enter the phone number in international format, for example +352 621 123 456.',
  UNKNOWN: 'Enter a company ID (CO or AD + 5 digits), an email address or a phone number.',
};

export const RECOGNISED = new Set(['COURIER', 'ADMIN', 'EMAIL', 'PHONE']);

export const ROLE_LABELS = { COURIER: 'Courier', ADMINISTRATOR: 'Administrator', CUSTOMER: 'Sender / recipient' };

export function showKind(element, kind, { staffNotAllowed = false } = {}) {
  if (!kind) {
    element.textContent = '';
    element.dataset.state = '';
    return;
  }
  if (staffNotAllowed && (kind === 'COURIER' || kind === 'ADMIN' || kind === 'STAFF_INCOMPLETE')) {
    element.textContent = 'Company accounts cannot be registered here';
    element.dataset.state = 'error';
    return;
  }
  element.textContent = KIND_TEXT[kind];
  element.dataset.state = RECOGNISED.has(kind) ? 'ok' : 'pending';
}

export function setMessage(element, text, kind = 'error') {
  element.textContent = text || '';
  element.className = `message ${kind}`;
  element.hidden = !text;
}

// Disables the form's buttons while a request is running.
export async function busy(form, task) {
  const buttons = form.querySelectorAll('button');
  buttons.forEach((button) => { button.disabled = true; });
  form.setAttribute('aria-busy', 'true');
  try {
    return await task();
  } finally {
    buttons.forEach((button) => { button.disabled = false; });
    form.removeAttribute('aria-busy');
  }
}

export function showDevCode(box, valueElement, code) {
  box.hidden = !code;
  valueElement.textContent = code || '';
}

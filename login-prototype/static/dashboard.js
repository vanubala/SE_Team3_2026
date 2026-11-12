import { api, ApiError, ROLE_LABELS, session, setMessage } from './common.js';

const $ = (selector) => document.querySelector(selector);

const AREAS = [
  { label: 'Courier area', path: '/api/courier/overview' },
  { label: 'Administrator area', path: '/api/admin/accounts' },
  { label: 'Sender / recipient area', path: '/api/customer/overview' },
];

const STATUS_TEXT = { ACTIVE: 'Active', PENDING_VERIFICATION: 'Not verified yet', LOCKED: 'Locked' };

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function signOut(reason) {
  session.clear();
  location.replace(`/?${reason}=1`);
}

function formatDate(value) {
  return new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function tokenExpiry() {
  try {
    const payload = JSON.parse(atob(session.token().split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    return new Date(payload.exp * 1000);
  } catch {
    return null;
  }
}

function fillList(list, items) {
  list.replaceChildren(...items.map((item) => el('li', item)));
}

async function renderCourier() {
  const data = await api('/api/courier/overview', { auth: true });
  $('#courier-company').textContent = data.company;
  fillList($('#courier-features'), data.features);
}

async function renderAdmin() {
  const data = await api('/api/admin/accounts', { auth: true });
  const rows = data.accounts.map((account) => {
    const row = el('tr');
    row.append(
      el('td', account.loginId || account.email || account.phone, 'mono'),
      el('td', account.name),
      el('td', ROLE_LABELS[account.role]),
      el('td', STATUS_TEXT[account.status] || account.status),
      el('td', formatDate(account.createdAt)),
    );
    return row;
  });
  $('#accounts').replaceChildren(...rows);
}

async function renderCustomer(me) {
  const data = await api('/api/customer/overview', { auth: true });
  $('#customer-contact').textContent = me.email || me.phone;
  fillList($('#customer-features'), data.features);
}

async function renderAccessCheck() {
  const items = await Promise.all(AREAS.map(async (area) => {
    const item = el('li');
    let verdict;
    try {
      await api(area.path, { auth: true });
      verdict = el('span', 'Allowed', 'verdict allowed');
    } catch (error) {
      verdict = el('span', error.status === 403 ? 'Denied (403)' : `Error (${error.status})`, 'verdict denied');
    }
    item.append(el('span', area.label), el('code', area.path), verdict);
    return item;
  }));
  $('#access-list').replaceChildren(...items);
}

async function load() {
  if (!session.token()) { location.replace('/'); return; }
  try {
    const me = await api('/api/me', { auth: true });
    const role = ROLE_LABELS[me.role];
    $('#user-name').textContent = me.name;
    $('#user-role').textContent = role;
    $('#user-role').dataset.role = me.role;
    $('#role-eyebrow').textContent = `${role} dashboard`;
    $('#welcome').textContent = `Welcome, ${me.name}`;
    $('#identity').textContent = me.loginId ? `Company ID ${me.loginId} - ${me.company}` : `Signed in as ${me.email || me.phone}`;
    $('#fact-role').textContent = role;
    $('#fact-method').textContent = me.loginId ? 'Company ID and password' : 'Email or phone and one-time code';
    const expiry = tokenExpiry();
    $('#fact-expiry').textContent = expiry ? formatDate(expiry) : 'Unknown';
    $(`#panel-${me.role}`).hidden = false;
    $('#dashboard').hidden = false;

    const renderers = { COURIER: renderCourier, ADMINISTRATOR: renderAdmin, CUSTOMER: () => renderCustomer(me) };
    await Promise.all([renderers[me.role](), renderAccessCheck()]);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) { signOut('expired'); return; }
    setMessage($('#message'), error.message);
  }
}

$('#signout').addEventListener('click', () => signOut('signedout'));
load();

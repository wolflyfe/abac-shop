/* ABAC One Stop Custom Shop — Shared JS Utilities */

const CART_KEY = 'abac_cart';

// ── Cart ──────────────────────────────────────────────────────────────────────
const Cart = {
    getItems() { try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; } catch { return []; } },
    save(items) { localStorage.setItem(CART_KEY, JSON.stringify(items)); updateCartBadge(); },
    add(product, size = '', color = '', qty = 1) {
        const items = this.getItems();
        const key = `${product.id}-${size}-${color}`;
        const existing = items.find(i => i.key === key);
        if (existing) { existing.qty += qty; }
        else { items.push({ key, product_id: product.id, product_name: product.name, price: product.price, size, color, qty }); }
        this.save(items);
        showToast(`${product.name} added to cart!`, 'success');
    },
    remove(key) { this.save(this.getItems().filter(i => i.key !== key)); },
    updateQty(key, qty) {
        const items = this.getItems();
        const item = items.find(i => i.key === key);
        if (item) { item.qty = qty <= 0 ? 1 : qty; }
        this.save(items);
    },
    getCount() { return this.getItems().reduce((sum, i) => sum + i.qty, 0); },
    getTotal() { return this.getItems().reduce((sum, i) => sum + i.price * i.qty, 0); },
    clear() { localStorage.removeItem(CART_KEY); updateCartBadge(); }
};

function updateCartBadge() {
    const count = Cart.getCount();
    document.querySelectorAll('.cart-count').forEach(el => {
        el.textContent = count;
        el.style.display = count > 0 ? 'inline-flex' : 'none';
    });
}

// ── API helpers ───────────────────────────────────────────────────────────────
async function apiGet(url, adminKey = null) {
    const headers = {};
    if (adminKey) headers['X-Admin-Key'] = adminKey;
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}

async function apiPost(url, data, adminKey = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (adminKey) headers['X-Admin-Key'] = adminKey;
    const res = await fetch(url, { method: 'POST', headers, body: JSON.stringify(data) });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `API error ${res.status}`); }
    return res.json();
}

async function apiPut(url, data, adminKey = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (adminKey) headers['X-Admin-Key'] = adminKey;
    const res = await fetch(url, { method: 'PUT', headers, body: JSON.stringify(data) });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}

async function apiDelete(url, adminKey = null) {
    const headers = {};
    if (adminKey) headers['X-Admin-Key'] = adminKey;
    const res = await fetch(url, { method: 'DELETE', headers });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = 'success') {
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.classList.add('show'), 10);
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, 3000);
}

function formatPrice(n) { return '$' + parseFloat(n).toFixed(2); }

// ── Delivery Dates ────────────────────────────────────────────────────────────
function updateDeliveryDates() {
    const now = new Date();
    const freeDate = new Date(now); freeDate.setDate(freeDate.getDate() + 10);
    const rushDate = new Date(now); rushDate.setDate(rushDate.getDate() + 3);
    const fmt = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    document.querySelectorAll('.free-delivery-date').forEach(el => el.textContent = fmt(freeDate));
    document.querySelectorAll('.rush-delivery-date').forEach(el => el.textContent = fmt(rushDate));
}

// Init on load
document.addEventListener('DOMContentLoaded', () => { updateCartBadge(); updateDeliveryDates(); });

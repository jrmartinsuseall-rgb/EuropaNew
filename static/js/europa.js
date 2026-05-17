/* ── Europa — JS Global ─────────────────────────────────── */

// ── Helpers BRL (usados também pelo Alpine.js) ────────────
function formatBRL(val) {
  const n = typeof val === 'string' ? parseBRL(val) : (parseFloat(val) || 0);
  return n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function parseBRL(str) {
  if (typeof str === 'number') return str;
  return parseFloat(String(str).replace(/\./g, '').replace(',', '.')) || 0;
}

// Data atual no topbar
document.addEventListener('DOMContentLoaded', function () {
  const el = document.getElementById('data-atual');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleDateString('pt-BR', {
      weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric'
    });
  }

  // Máscaras IMask
  aplicarMascaras();
});

// Reaplicar máscaras após HTMX swaps
document.addEventListener('htmx:afterSwap', function () {
  aplicarMascaras();
});

function aplicarMascaras() {
  // CPF
  document.querySelectorAll('[data-mask="cpf"]').forEach(el => {
    if (el._imask) return;
    el._imask = IMask(el, { mask: '000.000.000-00' });
  });

  // CNPJ
  document.querySelectorAll('[data-mask="cnpj"]').forEach(el => {
    if (el._imask) return;
    el._imask = IMask(el, { mask: '00.000.000/0000-00' });
  });

  // CPF ou CNPJ dinâmico
  document.querySelectorAll('[data-mask="cpfcnpj"]').forEach(el => {
    if (el._imask) return;
    el._imask = IMask(el, {
      mask: [{ mask: '000.000.000-00' }, { mask: '00.000.000/0000-00' }]
    });
  });

  // Telefone
  document.querySelectorAll('[data-mask="fone"]').forEach(el => {
    if (el._imask) return;
    el._imask = IMask(el, {
      mask: [{ mask: '(00) 0000-0000' }, { mask: '(00) 00000-0000' }]
    });
  });

  // CEP
  document.querySelectorAll('[data-mask="cep"]').forEach(el => {
    if (el._imask) return;
    el._imask = IMask(el, { mask: '00000-000' });
  });

  // Data
  document.querySelectorAll('[data-mask="data"]').forEach(el => {
    if (el._imask) return;
    el._imask = IMask(el, { mask: '00/00/0000' });
  });

  // Valor monetário BRL — ex: 1.234,56
  document.querySelectorAll('[data-mask="brl"]').forEach(el => {
    if (el._imask) return;
    el._imask = IMask(el, {
      mask: Number,
      scale: 2,
      signed: false,
      thousandsSeparator: '.',
      padFractionalZeros: true,
      normalizeZeros: true,
      radix: ',',
      mapToRadix: ['.'],
      min: 0,
    });
  });
}

// Converte campos BRL para decimal puro antes do submit
document.addEventListener('submit', function (e) {
  e.target.querySelectorAll('[data-mask="brl"]').forEach(el => {
    if (el._imask) el.value = el._imask.typedValue.toFixed(2);
  });
}, true);

// ── Enter avança campo ────────────────────────────────────
document.addEventListener('keydown', function (e) {
  if (e.key !== 'Enter') return;
  const tag = e.target.tagName;
  if (tag === 'TEXTAREA' || tag === 'BUTTON' || tag === 'A') return;
  if (e.target.type === 'submit') return;

  e.preventDefault();
  const focusable = Array.from(
    document.querySelectorAll(
      'input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), button[type="submit"]'
    )
  ).filter(el => el.offsetParent !== null); // apenas visíveis

  const idx = focusable.indexOf(e.target);
  if (idx > -1 && idx < focusable.length - 1) {
    focusable[idx + 1].focus();
  }
});

// ── Toast HTMX ────────────────────────────────────────────
document.addEventListener('htmx:responseError', function () {
  mostrarToast('Erro ao processar a requisição.', 'danger');
});

function mostrarToast(mensagem, tipo = 'success') {
  const area = document.getElementById('toast-area');
  if (!area) return;
  const id = 'toast-' + Date.now();
  area.insertAdjacentHTML('beforeend', `
    <div id="${id}" class="toast align-items-center text-bg-${tipo} border-0 show" role="alert">
      <div class="d-flex">
        <div class="toast-body">${mensagem}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>
  `);
  setTimeout(() => document.getElementById(id)?.remove(), 3500);
}

import { invoke } from '@tauri-apps/api/core';

const DEFAULT_BACKEND = 'http://127.0.0.1:8002';

let extractedCookies = [];

function getBackendUrl() {
  return localStorage.getItem('cas-demo-backend') || DEFAULT_BACKEND;
}

function showStatus(message, type = 'info') {
  const bar = document.getElementById('status');
  bar.textContent = message;
  bar.className = `status-bar status-${type}`;
  bar.style.display = 'block';
  setTimeout(() => { bar.style.display = 'none'; }, 6000);
}

window.openCasLogin = async function () {
  const btn = document.getElementById('btn-open');
  btn.disabled = true;
  btn.textContent = '⏳ 正在打开...';
  try {
    await invoke('open_cas_login');
    showStatus('✅ CAS 登录窗口已打开，请在弹出的窗口中登录', 'success');
  } catch (e) {
    showStatus('❌ 打开失败: ' + e, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔐 打开 CAS 登录';
  }
};

window.navigateTo = async function (url) {
  const btn = document.getElementById('btn-bb');
  btn.disabled = true;
  btn.textContent = '⏳ 跳转中...';
  try {
    await invoke('navigate_cas_window', { url });
    showStatus('✅ 正在跳转到 ' + url, 'success');
  } catch (e) {
    showStatus('❌ 跳转失败: ' + e, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '📚 跳转到 BB 系统';
  }
};

window.extractCookies = async function () {
  const btn = document.getElementById('btn-extract');
  btn.disabled = true;
  btn.textContent = '⏳ 提取中...';
  try {
    extractedCookies = await invoke('extract_cookies');
    renderCookies(extractedCookies);
    if (extractedCookies.length === 0) {
      showStatus('⚠️ 未提取到 Cookie — 请确认已在弹窗中完成登录', 'error');
    } else {
      showStatus(`✅ 提取到 ${extractedCookies.length} 个 Cookie`, 'success');
      updateBindButtons();
    }
  } catch (e) {
    showStatus('❌ 提取失败: ' + e, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🍪 提取已知域 Cookie';
  }
};

window.extractAllCookies = async function () {
  const btn = document.getElementById('btn-extract-all');
  btn.disabled = true;
  btn.textContent = '⏳ 提取中...';
  try {
    extractedCookies = await invoke('extract_all_cookies');
    renderCookies(extractedCookies);
    if (extractedCookies.length === 0) {
      showStatus('⚠️ 未提取到 Cookie — 请确认已在弹窗中完成登录', 'error');
    } else {
      showStatus(`✅ 提取到 ${extractedCookies.length} 个 Cookie (全部 SUSTech 域)`, 'success');
      updateBindButtons();
    }
  } catch (e) {
    showStatus('❌ 提取失败: ' + e, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🍪 提取全部 SUSTech Cookie';
  }
};

window.closeCasWindow = async function () {
  try {
    await invoke('close_cas_window');
    showStatus('✅ 登录窗口已关闭', 'success');
  } catch (e) {
    showStatus('❌ 关闭失败: ' + e, 'error');
  }
};

window.copyCookies = function () {
  if (extractedCookies.length === 0) return;
  const json = JSON.stringify(extractedCookies, null, 2);
  navigator.clipboard.writeText(json).then(() => {
    showStatus('✅ Cookie JSON 已复制到剪贴板', 'success');
  }).catch(() => {
    showStatus('❌ 复制失败', 'error');
  });
};

window.saveCookies = async function () {
  if (extractedCookies.length === 0) return;
  try {
    const path = await invoke('save_cookies', { cookies: extractedCookies });
    showStatus(`✅ 已保存到 ${path}`, 'success');
  } catch (e) {
    showStatus('❌ 保存失败: ' + e, 'error');
  }
};

async function doBind(action) {
  const backendUrl = getBackendUrl();
  const token = localStorage.getItem('token') || '';
  if (extractedCookies.length === 0) {
    showStatus('❌ 请先提取 Cookie', 'error');
    return;
  }

  const cmd = action === 'tis' ? 'bind_tis' : 'bind_blackboard';
  const btnId = action === 'tis' ? 'btn-bind-tis' : 'btn-bind-bb';
  const label = action === 'tis' ? 'TIS' : 'Blackboard';
  const btn = document.getElementById(btnId);
  const origText = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ 绑定中...';

  try {
    const result = await invoke(cmd, {
      cookies: extractedCookies,
      backendUrl,
      token,
    });
    if (result.success) {
      showStatus(`✅ ${label} 绑定成功: ${result.message}`, 'success');
    } else {
      showStatus(`❌ ${label} 绑定失败: ${result.message}`, 'error');
    }
  } catch (e) {
    showStatus(`❌ ${label} 绑定异常: ${e}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = origText;
  }
}

window.bindTis = () => doBind('tis');
window.bindBlackboard = () => doBind('bb');

function updateBindButtons() {
  const hasTis = extractedCookies.some(c => c.domain.includes('tis.sustech.edu.cn'));
  const hasBb = extractedCookies.some(c => c.domain.includes('bb.sustech.edu.cn'));
  const hasCookies = extractedCookies.length > 0;

  const btnTis = document.getElementById('btn-bind-tis');
  const btnBb = document.getElementById('btn-bind-bb');

  if (btnTis) {
    btnTis.disabled = !hasCookies;
    btnTis.title = hasTis ? '检测到 TIS Cookie，可绑定' : '未检测到 TIS Cookie，可尝试绑定';
    btnTis.style.opacity = hasTis ? '1' : '0.7';
  }
  if (btnBb) {
    btnBb.disabled = !hasCookies;
    btnBb.title = hasBb ? '检测到 BB Cookie，可绑定' : '未检测到 BB Cookie，可尝试绑定';
    btnBb.style.opacity = hasBb ? '1' : '0.7';
  }
}

function renderCookies(cookies) {
  const section = document.getElementById('result-section');
  const list = document.getElementById('cookie-list');
  const summary = document.getElementById('result-summary');

  if (cookies.length === 0) {
    section.style.display = 'none';
    return;
  }

  section.style.display = 'block';

  const domains = {};
  for (const c of cookies) {
    const d = c.domain || '(unknown)';
    if (!domains[d]) domains[d] = [];
    domains[d].push(c);
  }

  const domainCount = Object.keys(domains).length;
  const hasTgc = cookies.some(c => c.name === 'TGC');
  summary.innerHTML = `共 <strong>${cookies.length}</strong> 个 Cookie，来自 <strong>${domainCount}</strong> 个域 `
    + (hasTgc ? '— <strong style="color:var(--success)">✅ TGC 已获取</strong>' : '— <strong style="color:var(--warning)">⚠️ 未找到 TGC</strong>');

  list.innerHTML = '';
  for (const [domain, items] of Object.entries(domains)) {
    const domainDiv = document.createElement('div');
    domainDiv.className = 'cookie-domain';
    domainDiv.innerHTML = `<div class="cookie-domain-header">${domain} (${items.length})</div>`;

    for (const c of items) {
      const flags = [];
      if (c.secure) flags.push('<span class="cookie-flag flag-secure">Secure</span>');
      if (c.http_only) flags.push('<span class="cookie-flag flag-httponly">HttpOnly</span>');
      const truncated = c.value.length > 60 ? c.value.slice(0, 57) + '...' : c.value;
      domainDiv.innerHTML += `
        <div class="cookie-item">
          <span class="cookie-name">${c.name}</span>
          <span class="cookie-value" title="${c.value}">${truncated}</span>
          <span class="cookie-flags">${flags.join('')}</span>
        </div>`;
    }
    list.appendChild(domainDiv);
  }
}
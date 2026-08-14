(function() {
  var STORAGE_KEY = 'billzo_auth_session_v1';
  var config = {
    getClientId: function() {
      return (window.APP_CONFIG && window.APP_CONFIG.clientId) || '';
    },
    getScriptUrl: function() {
      return ((window.APP_CONFIG || {}).sheets || {}).scriptURL || '';
    }
  };
  var overlay, pendingResolve;

  function readCfg(getter) {
    return typeof getter === 'function' ? getter() : getter;
  }

  function clientId() {
    return readCfg(config.getClientId) || '';
  }

  function scriptUrl() {
    return readCfg(config.getScriptUrl) || '';
  }

  function businessName() {
    return ((window.APP_CONFIG || {}).business || {}).name || 'Billzo';
  }

  function storage() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    } catch (e) {
      return null;
    }
  }

  function saveSession(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }

  function clearSession() {
    localStorage.removeItem(STORAGE_KEY);
  }

  function hasLocalSession() {
    var session = storage();
    return !!(session && session.client === clientId() && session.token && session.expiresAt && session.expiresAt > Date.now());
  }

  function buildUrl(params) {
    var base = scriptUrl();
    var query = Object.keys(params).map(function(key) {
      return encodeURIComponent(key) + '=' + encodeURIComponent(params[key]);
    }).join('&');
    return base + (base.indexOf('?') >= 0 ? '&' : '?') + query;
  }

  function jsonGet(params) {
    var url = buildUrl(params);
    return fetch(url).then(function(r) { return r.json(); });
  }

  function ensureOverlay() {
    if (overlay) return overlay;
    var style = document.createElement('style');
    style.textContent = ''
      + '.billzo-auth{position:fixed;inset:0;z-index:10000;background:rgba(8,3,0,.9);display:flex;align-items:center;justify-content:center;padding:20px;}'
      + '.billzo-auth-box{width:min(360px,100%);background:rgba(255,255,255,.05);border:1px solid rgba(201,146,42,.28);border-radius:18px;padding:28px 24px;box-shadow:0 24px 80px rgba(0,0,0,.65);font-family:\'DM Sans\',sans-serif;color:#fff;}'
      + '.billzo-auth-logo{font-family:\'Playfair Display\',serif;font-size:1.5rem;font-weight:900;color:#fff;margin-bottom:4px;}'
      + '.billzo-auth-logo span{color:#e8c46a;}'
      + '.billzo-auth-sub{font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:rgba(255,255,255,.3);margin-bottom:22px;}'
      + '.billzo-auth-label{font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.45);margin-bottom:8px;font-weight:700;}'
      + '.billzo-auth-input{width:100%;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);color:#fff;padding:11px 12px;border-radius:10px;font-size:.92rem;outline:none;}'
      + '.billzo-auth-input:focus{border-color:rgba(201,146,42,.5);}'
      + '.billzo-auth-btn{width:100%;margin-top:12px;background:#8b1a1a;border:none;color:#fff;padding:11px 12px;border-radius:10px;font-size:.9rem;font-weight:700;cursor:pointer;}'
      + '.billzo-auth-msg{min-height:18px;margin-top:12px;font-size:.78rem;color:#ef9a9a;}'
      + '.billzo-auth-note{margin-top:10px;font-size:.72rem;color:rgba(255,255,255,.24);line-height:1.45;}';
    document.head.appendChild(style);

    overlay = document.createElement('div');
    overlay.className = 'billzo-auth';
    overlay.innerHTML = ''
      + '<div class="billzo-auth-box">'
      + '  <div class="billzo-auth-logo">' + businessName() + ' <span>Staff</span></div>'
      + '  <div class="billzo-auth-sub">Protected Access</div>'
      + '  <div class="billzo-auth-label">Shared Password</div>'
      + '  <input class="billzo-auth-input" id="billzoAuthPassword" type="password" placeholder="Enter customer password" autocomplete="current-password"/>'
      + '  <button class="billzo-auth-btn" id="billzoAuthSubmit" type="button">Login</button>'
      + '  <div class="billzo-auth-msg" id="billzoAuthMsg"></div>'
      + '  <div class="billzo-auth-note">Login stays active for 1 day on this browser.</div>'
      + '</div>';
    document.body.appendChild(overlay);

    overlay.querySelector('#billzoAuthSubmit').addEventListener('click', submitLogin);
    overlay.querySelector('#billzoAuthPassword').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') submitLogin();
    });
    return overlay;
  }

  function showOverlay(message) {
    var el = ensureOverlay();
    el.style.display = 'flex';
    el.querySelector('#billzoAuthMsg').textContent = message || '';
    el.querySelector('#billzoAuthPassword').value = '';
    setTimeout(function() { el.querySelector('#billzoAuthPassword').focus(); }, 0);
    return new Promise(function(resolve) {
      pendingResolve = resolve;
    });
  }

  function hideOverlay() {
    if (overlay) overlay.style.display = 'none';
  }

  function submitLogin() {
    var el = ensureOverlay();
    var input = el.querySelector('#billzoAuthPassword');
    var msg = el.querySelector('#billzoAuthMsg');
    var password = input.value.trim();
    if (!password) {
      msg.textContent = 'Enter the customer password.';
      input.focus();
      return;
    }
    msg.textContent = 'Checking password...';
    jsonGet({
      action: 'login',
      client: clientId(),
      password: password,
      t: Date.now()
    }).then(function(data) {
      if (!data || data.status !== 'ok' || !data.token) {
        msg.textContent = (data && data.message) || 'Login failed.';
        return;
      }
      saveSession({
        client: clientId(),
        token: data.token,
        expiresAt: data.expiresAt
      });
      hideOverlay();
      if (pendingResolve) {
        var resolve = pendingResolve;
        pendingResolve = null;
        resolve(storage());
      }
    }).catch(function() {
      msg.textContent = 'Could not reach the server.';
    });
  }

  function validateSession() {
    if (!hasLocalSession()) return Promise.resolve(false);
    var session = storage();
    return jsonGet({
      action: 'validateSession',
      client: session.client,
      token: session.token,
      t: Date.now()
    }).then(function(data) {
      return !!(data && data.status === 'ok' && data.valid);
    }).catch(function() {
      return false;
    });
  }

  function requireSession(message) {
    return validateSession().then(function(valid) {
      if (valid) return storage();
      clearSession();
      return showOverlay(message || 'Enter password to continue.');
    });
  }

  function guard(options) {
    options = options || {};
    return requireSession().then(function() {
      if (typeof options.onReady === 'function') options.onReady();
    });
  }

  function authGet(params) {
    return requireSession('Session expired. Login again.').then(function(session) {
      var request = {};
      Object.keys(params || {}).forEach(function(key) { request[key] = params[key]; });
      request.client = session.client;
      request.token = session.token;
      request.t = Date.now();
      return jsonGet(request).then(function(data) {
        if (data && data.code === 'AUTH_REQUIRED') {
          clearSession();
          return requireSession('Session expired. Login again.').then(function() {
            return authGet(params);
          });
        }
        return data;
      });
    });
  }

  function authPost(payload) {
    return requireSession('Session expired. Login again.').then(function(session) {
      var body = {};
      Object.keys(payload || {}).forEach(function(key) { body[key] = payload[key]; });
      body.client = session.client;
      body.token = session.token;
      return fetch(scriptUrl(), {
        method: 'POST',
        mode: 'no-cors',
        headers: { 'Content-Type': 'text/plain' },
        body: JSON.stringify(body)
      });
    });
  }

  function logout() {
    var session = storage();
    clearSession();
    if (session && session.token && scriptUrl()) {
      fetch(buildUrl({ action: 'logout', client: session.client, token: session.token, t: Date.now() })).catch(function() {});
    }
    window.location.reload();
  }

  window.BillzoAuth = {
    configure: function(next) {
      next = next || {};
      Object.keys(next).forEach(function(key) { config[key] = next[key]; });
    },
    guard: guard,
    authGet: authGet,
    authPost: authPost,
    requireSession: requireSession,
    logout: logout,
    clearSession: clearSession,
    getSession: storage
  };
})();
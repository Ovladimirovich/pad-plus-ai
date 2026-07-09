let isRefreshing = false;
let refreshSubscribers = [];

const onRefreshed = (token) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

const addRefreshSubscriber = (cb) => {
  refreshSubscribers.push(cb);
};

const getAuthToken = () => {
  try {
    const raw = localStorage.getItem('supabase.auth.token');
    if (raw) {
      const authData = JSON.parse(raw);
      return authData?.access_token;
    }
  } catch (e) {
  }
  return localStorage.getItem('access_token');
};

const getRefreshToken = () => localStorage.getItem('refresh_token');

const setTokens = (access, refresh) => {
  localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);

  try {
    const raw = localStorage.getItem('supabase.auth.token');
    if (raw) {
      const authData = JSON.parse(raw);
      authData.access_token = access;
      localStorage.setItem('supabase.auth.token', JSON.stringify(authData));
    }
  } catch (e) {
  }
};

const refreshToken = async () => {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  try {
    const resp = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Refresh-Token': refresh,
      },
    });

    if (!resp.ok) return null;
    const data = await resp.json();
    return data.access_token;
  } catch {
    return null;
  }
};

const buildHeaders = (options) => {
  const existing = options.headers || {};
  const hasFormData = options.body instanceof FormData;

  const headers = {};
  if (!hasFormData && !existing['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const refresh = getRefreshToken();
  if (refresh) {
    headers['X-Refresh-Token'] = refresh;
  }

  Object.assign(headers, existing);
  return headers;
};

export const apiFetch = async (url, options = {}) => {
  const headers = buildHeaders(options);

  let response = await fetch(url, {
    ...options,
    headers,
  });

  // Если сервер вернул новый токен — сохраняем
  const newToken = response.headers.get('X-New-Access-Token');
  if (newToken) {
    setTokens(newToken, getRefreshToken());
  }

  // Retry logic для временных ошибок Render (502/503/504)
  const MAX_RETRIES = 3;
  let retryCount = 0;
  while ((response.status === 502 || response.status === 503 || response.status === 504) && retryCount < MAX_RETRIES) {
    retryCount++;
    const delay = 1000 * retryCount; // 1s, 2s, 3s
    console.warn(`🔄 Retry ${retryCount}/${MAX_RETRIES} for ${url} (status ${response.status}), waiting ${delay}ms...`);
    await new Promise(r => setTimeout(r, delay));
    response = await fetch(url, { ...options, headers: buildHeaders(options) });
  }

  if (response.status === 401) {
    if (!isRefreshing) {
      isRefreshing = true;
      const newToken = await refreshToken();
      isRefreshing = false;

      if (newToken) {
        setTokens(newToken, getRefreshToken());
        onRefreshed(newToken);
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        localStorage.removeItem('supabase.auth.token');
        window.location.href = '/login';
        throw new Error('Session expired, please login again');
      }
    } else {
      const newToken = await new Promise((resolve) =>
        addRefreshSubscriber((token) => resolve(token))
      );
      if (!newToken) {
        throw new Error('Session expired, please login again');
      }
    }

    const retryHeaders = buildHeaders(options);
    response = await fetch(url, {
      ...options,
      headers: retryHeaders,
    });
  }

  return response;
};

export { getAuthToken, getRefreshToken, setTokens };

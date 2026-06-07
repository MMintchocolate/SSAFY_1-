import { ref, computed } from 'vue'

const user         = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const accessToken  = ref(localStorage.getItem('access') || '')
const refreshToken = ref(localStorage.getItem('refresh') || '')

export function useAuth() {
  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)

  function _save(data) {
    accessToken.value  = data.access
    refreshToken.value = data.refresh
    user.value         = data.user
    localStorage.setItem('access',  data.access)
    localStorage.setItem('refresh', data.refresh)
    localStorage.setItem('user',    JSON.stringify(data.user))
  }

  function _clear() {
    accessToken.value  = ''
    refreshToken.value = ''
    user.value         = null
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    localStorage.removeItem('user')
  }

  async function register(username, email, password, password2) {
    const res = await fetch('/api/accounts/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, password2 }),
    })
    const data = await res.json()
    if (!res.ok) throw data
    _save(data)
  }

  async function login(username, password) {
    const res = await fetch('/api/accounts/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    const data = await res.json()
    if (!res.ok) throw data
    _save(data)
  }

  async function logout() {
    if (refreshToken.value) {
      await fetch('/api/accounts/logout/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken.value }),
      }).catch(() => {})
    }
    _clear()
  }

  // access 토큰 만료 시 자동 갱신
  async function refreshAccess() {
    if (!refreshToken.value) return false
    const res = await fetch('/api/accounts/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken.value }),
    })
    if (!res.ok) { _clear(); return false }
    const data = await res.json()
    accessToken.value = data.access
    if (data.refresh) refreshToken.value = data.refresh
    localStorage.setItem('access', data.access)
    if (data.refresh) localStorage.setItem('refresh', data.refresh)
    return true
  }

  // Authorization 헤더 포함 fetch 래퍼
  async function authFetch(url, options = {}) {
    const doFetch = (token) => fetch(url, {
      ...options,
      headers: { ...(options.headers || {}), Authorization: `Bearer ${token}` },
    })

    let res = await doFetch(accessToken.value)
    if (res.status === 401) {
      const ok = await refreshAccess()
      if (!ok) throw new Error('인증이 필요합니다.')
      res = await doFetch(accessToken.value)
    }
    return res
  }

  return { user, isLoggedIn, accessToken, login, register, logout, authFetch }
}

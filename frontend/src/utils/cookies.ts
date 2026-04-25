/**
 * Cookie utility functions for storing and retrieving tokens
 * Uses secure, httpOnly-like approach with SameSite protection
 */

const AUTH_TOKEN_KEY = 'e_clinic_auth_token'
const REFRESH_TOKEN_KEY = 'e_clinic_refresh_token'

// Cookie options - secure, httpOnly-like, SameSite
const getCookieOptions = () => {
  // Check if actually using HTTPS (not just production mode)
  const isHTTPS = typeof window !== 'undefined' && window.location.protocol === 'https:'
  const maxAge = 30 * 24 * 60 * 60 // 30 days in seconds

  return {
    path: '/',
    maxAge,
    sameSite: 'lax' as const, // Changed to 'lax' for better compatibility with HTTP
    secure: isHTTPS, // Only secure if actually using HTTPS
  }
}

/**
 * Set a cookie value
 */
export const setCookie = (name: string, value: string, options?: { maxAge?: number }) => {
  if (typeof document === 'undefined') return

  const cookieOptions = { ...getCookieOptions(), ...options }
  let cookieString = `${name}=${encodeURIComponent(value)}`

  if (cookieOptions.maxAge) {
    const expires = new Date(Date.now() + cookieOptions.maxAge * 1000)
    cookieString += `; expires=${expires.toUTCString()}`
  }

  cookieString += `; path=${cookieOptions.path}`
  cookieString += `; SameSite=${cookieOptions.sameSite}`

  if (cookieOptions.secure) {
    cookieString += '; Secure'
  }

  document.cookie = cookieString
}

/**
 * Get a cookie value
 */
export const getCookie = (name: string): string | null => {
  if (typeof document === 'undefined') return null

  const nameEQ = name + '='
  const cookies = document.cookie.split(';')

  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i]
    while (cookie.charAt(0) === ' ') {
      cookie = cookie.substring(1, cookie.length)
    }
    if (cookie.indexOf(nameEQ) === 0) {
      return decodeURIComponent(cookie.substring(nameEQ.length, cookie.length))
    }
  }

  return null
}

/**
 * Remove a cookie
 */
export const removeCookie = (name: string) => {
  if (typeof document === 'undefined') return

  const isHTTPS = typeof window !== 'undefined' && window.location.protocol === 'https:'
  let cookieString = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=lax`
  
  if (isHTTPS) {
    cookieString += '; Secure'
  }

  document.cookie = cookieString
}

/**
 * Token-specific cookie functions
 */
export const tokenCookies = {
  setAccessToken: (token: string) => {
    setCookie(AUTH_TOKEN_KEY, token)
  },

  getAccessToken: (): string | null => {
    return getCookie(AUTH_TOKEN_KEY)
  },

  setRefreshToken: (token: string) => {
    setCookie(REFRESH_TOKEN_KEY, token)
  },

  getRefreshToken: (): string | null => {
    return getCookie(REFRESH_TOKEN_KEY)
  },

  removeAccessToken: () => {
    removeCookie(AUTH_TOKEN_KEY)
  },

  removeRefreshToken: () => {
    removeCookie(REFRESH_TOKEN_KEY)
  },

  removeAllTokens: () => {
    removeCookie(AUTH_TOKEN_KEY)
    removeCookie(REFRESH_TOKEN_KEY)
  },
}

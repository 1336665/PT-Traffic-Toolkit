import zhCN from './zh-CN'

const locales = {
  'zh-CN': zhCN,
}

let currentLocale = 'zh-CN'
let messages = locales[currentLocale]

export function setLocale(locale) {
  if (locales[locale]) {
    currentLocale = locale
    messages = locales[locale]
  }
}

export function getLocale() {
  return currentLocale
}

export function t(key, params = {}) {
  const keys = key.split('.')
  let value = messages

  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k]
    } else {
      return key // Fallback to key if not found
    }
  }

  if (typeof value === 'string' && params) {
    // Replace {param} with values
    return value.replace(/\{(\w+)\}/g, (_, name) => params[name] ?? `{${name}}`)
  }

  return value
}

// Vue plugin
export const i18nPlugin = {
  install(app) {
    app.config.globalProperties.$t = t
    app.provide('t', t)
    app.provide('setLocale', setLocale)
    app.provide('getLocale', getLocale)
  }
}

export default { t, setLocale, getLocale, i18nPlugin }

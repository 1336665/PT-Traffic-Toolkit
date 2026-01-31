/**
 * Common formatting utilities for the PT Manager frontend
 */

import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

dayjs.locale('zh-cn')
dayjs.extend(relativeTime)
dayjs.extend(utc)
dayjs.extend(timezone)

// Get local timezone
const localTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone

/**
 * Format bytes to human readable size
 * @param {number} bytes - Size in bytes
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted size string
 */
export function formatSize(bytes, decimals = 2) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i]
}

/**
 * Format bytes per second to human readable speed
 * @param {number} bytesPerSecond - Speed in bytes per second
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted speed string
 */
export function formatSpeed(bytesPerSecond, decimals = 2) {
  if (!bytesPerSecond || bytesPerSecond === 0) return '0 B/s'
  const k = 1024
  const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s']
  const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k))
  return parseFloat((bytesPerSecond / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i]
}

/**
 * Format timestamp to localized date/time string
 * Backend sends UTC timestamps, so we convert to local timezone
 * @param {string|Date|number} timestamp - Timestamp to format (UTC)
 * @param {string} format - dayjs format string (default: 'MM-DD HH:mm')
 * @returns {string} Formatted date/time string
 */
export function formatTime(timestamp, format = 'MM-DD HH:mm') {
  if (!timestamp) return '-'
  // Parse as UTC and convert to local timezone
  return dayjs.utc(timestamp).tz(localTimezone).format(format)
}

/**
 * Format duration in seconds to human readable string
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string
 */
export function formatDuration(seconds) {
  if (!seconds || seconds === 0) return '0秒'
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时`
  return `${Math.floor(seconds / 86400)}天`
}

/**
 * Format timestamp to relative time string (e.g., "5 minutes ago")
 * Backend sends UTC timestamps, so we convert to local timezone
 * @param {string|Date|number} timestamp - Timestamp to format (UTC)
 * @returns {string} Relative time string
 */
export function formatRelativeTime(timestamp) {
  if (!timestamp) return '-'
  // Parse as UTC and convert to local timezone for correct relative time
  return dayjs.utc(timestamp).tz(localTimezone).fromNow()
}

/**
 * Format number with thousand separators
 * @param {number} num - Number to format
 * @returns {string} Formatted number string
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString()
}

/**
 * Truncate string with ellipsis
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length before truncation
 * @returns {string} Truncated string
 */
export function truncate(str, maxLength = 50) {
  if (!str) return ''
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength) + '...'
}

/**
 * Parse size string to bytes
 * @param {string} sizeStr - Size string like "10 GB", "500 MB"
 * @returns {number} Size in bytes
 */
export function parseSize(sizeStr) {
  if (!sizeStr) return 0
  const match = sizeStr.match(/(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB|PB)?/i)
  if (!match) return 0

  const num = parseFloat(match[1])
  const unit = (match[2] || 'B').toUpperCase()
  const multipliers = { 'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4, 'PB': 1024**5 }
  return Math.round(num * (multipliers[unit] || 1))
}

export default {
  formatSize,
  formatSpeed,
  formatTime,
  formatDuration,
  formatRelativeTime,
  formatNumber,
  truncate,
  parseSize
}

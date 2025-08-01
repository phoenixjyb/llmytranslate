// Shared utility functions for both web and React Native platforms
// These utilities work identically across all platforms

import type { ApiResponse, AppError, Language, User } from '../types';

// =============================================================================
// API Utilities
// =============================================================================

/**
 * Create a standardized API response
 */
export const createApiResponse = <T>(
  success: boolean,
  data?: T,
  error?: string,
  message?: string
): ApiResponse<T> => {
  const response: ApiResponse<T> = {
    success,
    timestamp: new Date().toISOString(),
  };
  
  if (data !== undefined) response.data = data;
  if (error !== undefined) response.error = error;
  if (message !== undefined) response.message = message;
  
  return response;
};

/**
 * Handle API errors consistently
 */
export const handleApiError = (error: any): AppError => {
  const timestamp = new Date().toISOString();
  
  if (error.response) {
    // HTTP error response
    return {
      code: `HTTP_${error.response.status}`,
      message: error.response.data?.message || error.response.statusText || 'HTTP Error',
      details: error.response.data,
      timestamp,
    };
  } else if (error.request) {
    // Network error
    return {
      code: 'NETWORK_ERROR',
      message: 'Network connection failed',
      details: error.message,
      timestamp,
    };
  } else {
    // Other error
    return {
      code: 'UNKNOWN_ERROR',
      message: error.message || 'An unknown error occurred',
      details: error,
      timestamp,
    };
  }
};

/**
 * Build query string from parameters
 */
export const buildQueryString = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  });
  
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
};

// =============================================================================
// Text and Language Utilities
// =============================================================================

/**
 * Truncate text to specified length
 */
export const truncateText = (text: string, maxLength: number, suffix: string = '...'): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - suffix.length) + suffix;
};

/**
 * Clean and normalize text input
 */
export const normalizeText = (text: string): string => {
  return text
    .trim()
    .replace(/\s+/g, ' ') // Replace multiple spaces with single space
    .replace(/\n\s*\n/g, '\n'); // Remove empty lines
};

/**
 * Find language by code
 */
export const findLanguageByCode = (languages: Language[], code: string): Language | undefined => {
  return languages.find(lang => lang.code.toLowerCase() === code.toLowerCase());
};

/**
 * Get language display name
 */
export const getLanguageDisplayName = (language: Language): string => {
  return language.native_name || language.name;
};

/**
 * Detect if text contains non-Latin characters
 */
export const hasNonLatinCharacters = (text: string): boolean => {
  return /[^\u0000-\u007F]/.test(text);
};

/**
 * Count words in text
 */
export const countWords = (text: string): number => {
  return text.trim().split(/\s+/).filter(word => word.length > 0).length;
};

/**
 * Estimate reading time in minutes
 */
export const estimateReadingTime = (text: string, wordsPerMinute: number = 200): number => {
  const wordCount = countWords(text);
  return Math.max(1, Math.round(wordCount / wordsPerMinute));
};

// =============================================================================
// Date and Time Utilities
// =============================================================================

/**
 * Format date for display
 */
export const formatDate = (date: string | Date, locale: string = 'en-US'): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

/**
 * Format time for display
 */
export const formatTime = (date: string | Date, locale: string = 'en-US'): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleTimeString(locale, {
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Get relative time string (e.g., "2 hours ago")
 */
export const getRelativeTime = (date: string | Date): string => {
  const now = new Date();
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const diffMs = now.getTime() - dateObj.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSeconds < 60) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  
  return formatDate(dateObj);
};

/**
 * Format duration in milliseconds to readable string
 */
export const formatDuration = (ms: number): string => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
  }
  return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`;
};

// =============================================================================
// Validation Utilities
// =============================================================================

/**
 * Validate email address
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate URL
 */
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * Check if string is empty or only whitespace
 */
export const isEmpty = (str: string): boolean => {
  return !str || str.trim().length === 0;
};

/**
 * Validate text length
 */
export const isValidLength = (text: string, minLength: number = 1, maxLength: number = 10000): boolean => {
  const length = text.trim().length;
  return length >= minLength && length <= maxLength;
};

// =============================================================================
// Storage Utilities (Platform-agnostic)
// =============================================================================

/**
 * Safe JSON parse with fallback
 */
export const safeJsonParse = <T>(json: string, fallback: T): T => {
  try {
    return JSON.parse(json);
  } catch {
    return fallback;
  }
};

/**
 * Safe JSON stringify
 */
export const safeJsonStringify = (obj: any): string => {
  try {
    return JSON.stringify(obj);
  } catch {
    return '{}';
  }
};

/**
 * Create storage key with prefix
 */
export const createStorageKey = (prefix: string, key: string): string => {
  return `${prefix}_${key}`;
};

// =============================================================================
// Array and Object Utilities
// =============================================================================

/**
 * Remove duplicates from array
 */
export const uniqueArray = <T>(array: T[]): T[] => {
  return [...new Set(array)];
};

/**
 * Group array by key
 */
export const groupBy = <T, K extends keyof T>(array: T[], key: K): Record<string, T[]> => {
  return array.reduce((groups, item) => {
    const groupKey = String(item[key]);
    groups[groupKey] = groups[groupKey] || [];
    groups[groupKey].push(item);
    return groups;
  }, {} as Record<string, T[]>);
};

/**
 * Deep clone object
 */
export const deepClone = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj));
};

/**
 * Check if object is empty
 */
export const isEmptyObject = (obj: object): boolean => {
  return Object.keys(obj).length === 0;
};

/**
 * Pick specific keys from object
 */
export const pick = <T extends Record<string, any>, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

/**
 * Omit specific keys from object
 */
export const omit = <T, K extends keyof T>(obj: T, keys: K[]): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach(key => {
    delete result[key];
  });
  return result;
};

// =============================================================================
// Number and Math Utilities
// =============================================================================

/**
 * Clamp number between min and max
 */
export const clamp = (value: number, min: number, max: number): number => {
  return Math.min(Math.max(value, min), max);
};

/**
 * Round to specified decimal places
 */
export const roundToDecimal = (value: number, decimals: number): number => {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
};

/**
 * Format number with thousand separators
 */
export const formatNumber = (value: number, locale: string = 'en-US'): string => {
  return value.toLocaleString(locale);
};

/**
 * Convert bytes to human readable format
 */
export const formatBytes = (bytes: number, decimals: number = 2): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
};

// =============================================================================
// Random and ID Utilities
// =============================================================================

/**
 * Generate random ID
 */
export const generateId = (length: number = 12): string => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

/**
 * Generate UUID v4
 */
export const generateUUID = (): string => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

/**
 * Random integer between min and max (inclusive)
 */
export const randomInt = (min: number, max: number): number => {
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

/**
 * Random item from array
 */
export const randomItem = <T>(array: T[]): T => {
  return array[Math.floor(Math.random() * array.length)];
};

// =============================================================================
// Async Utilities
// =============================================================================

/**
 * Sleep for specified milliseconds
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * Debounce function calls
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: number | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait) as any;
  };
};

/**
 * Throttle function calls
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Retry async function with exponential backoff
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: Error;
  
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      if (i === maxRetries) {
        throw lastError;
      }
      
      const delay = baseDelay * Math.pow(2, i);
      await sleep(delay);
    }
  }
  
  throw lastError!;
};

// =============================================================================
// User and Authentication Utilities
// =============================================================================

/**
 * Check if user is guest
 */
export const isGuestUser = (user?: User): boolean => {
  return !user || user.is_guest === true;
};

/**
 * Get user display name
 */
export const getUserDisplayName = (user?: User): string => {
  if (!user) return 'Guest';
  return user.username || user.email || 'User';
};

/**
 * Generate guest user ID
 */
export const generateGuestId = (): string => {
  return `guest_${generateId(8)}_${Date.now()}`;
};

// =============================================================================
// Platform Detection Utilities
// =============================================================================

/**
 * Check if running on mobile platform (React Native)
 */
export const isMobilePlatform = (): boolean => {
  return typeof navigator !== 'undefined' && navigator.product === 'ReactNative';
};

/**
 * Check if running on web platform
 */
export const isWebPlatform = (): boolean => {
  return typeof window !== 'undefined' && typeof navigator !== 'undefined';
};

/**
 * Get platform name
 */
export const getPlatformName = (): string => {
  if (isMobilePlatform()) return 'mobile';
  if (isWebPlatform()) return 'web';
  return 'unknown';
};

// =============================================================================
// Export all utilities
// =============================================================================

export default {
  // API utilities
  createApiResponse,
  handleApiError,
  buildQueryString,
  
  // Text utilities
  truncateText,
  normalizeText,
  findLanguageByCode,
  getLanguageDisplayName,
  hasNonLatinCharacters,
  countWords,
  estimateReadingTime,
  
  // Date utilities
  formatDate,
  formatTime,
  getRelativeTime,
  formatDuration,
  
  // Validation utilities
  isValidEmail,
  isValidUrl,
  isEmpty,
  isValidLength,
  
  // Storage utilities
  safeJsonParse,
  safeJsonStringify,
  createStorageKey,
  
  // Array/Object utilities
  uniqueArray,
  groupBy,
  deepClone,
  isEmptyObject,
  pick,
  omit,
  
  // Number utilities
  clamp,
  roundToDecimal,
  formatNumber,
  formatBytes,
  
  // Random utilities
  generateId,
  generateUUID,
  randomInt,
  randomItem,
  
  // Async utilities
  sleep,
  debounce,
  throttle,
  retryWithBackoff,
  
  // User utilities
  isGuestUser,
  getUserDisplayName,
  generateGuestId,
  
  // Platform utilities
  isMobilePlatform,
  isWebPlatform,
  getPlatformName,
};

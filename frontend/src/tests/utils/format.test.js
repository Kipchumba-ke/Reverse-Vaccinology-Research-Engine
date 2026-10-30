import { describe, it, expect } from 'vitest'
import {
  formatEvalue,
  formatNumber,
  formatPercent,
  formatSigned,
} from '../../utils/format'

describe('formatNumber', () => {
  it('rounds floats to two decimals', () => {
    expect(formatNumber(43573.359879999996)).toBe('43573.36')
    expect(formatNumber(-0.20151515151515154)).toBe('-0.20')
    expect(formatNumber(0.5)).toBe('0.50')
    expect(formatNumber(3)).toBe('3.00')
  })

  it('can group thousands', () => {
    expect(formatNumber(13892.05968, { group: true })).toBe('13,892.06')
  })

  it('does not print a negative zero', () => {
    expect(formatNumber(-0.001)).toBe('0.00')
  })

  it('accepts numeric strings and falls back for missing values', () => {
    expect(formatNumber('1.239')).toBe('1.24')
    expect(formatNumber(null)).toBe('Unavailable')
    expect(formatNumber(undefined)).toBe('Unavailable')
    expect(formatNumber('')).toBe('Unavailable')
    expect(formatNumber(NaN)).toBe('Unavailable')
    expect(formatNumber('abc', { fallback: 'n/a' })).toBe('n/a')
  })
})

describe('formatPercent', () => {
  it('adds a percent sign after rounding', () => {
    expect(formatPercent(11.616161616161616)).toBe('11.62%')
    expect(formatPercent(85)).toBe('85.00%')
  })

  it('uses the fallback without a percent sign', () => {
    expect(formatPercent(undefined)).toBe('Unavailable')
    expect(formatPercent(null, { fallback: '' })).toBe('')
  })
})

describe('formatSigned', () => {
  it('shows an explicit sign for charges', () => {
    expect(formatSigned(2.997390920388489)).toBe('+3.00')
    expect(formatSigned(-1.2)).toBe('-1.20')
    expect(formatSigned(0)).toBe('0.00')
    expect(formatSigned(undefined, { fallback: '' })).toBe('')
  })
})

describe('formatEvalue', () => {
  it('uses scientific notation for very small e-values', () => {
    expect(formatEvalue(0.0000123)).toBe('1.23e-5')
    expect(formatEvalue(3.2e-12)).toBe('3.20e-12')
  })

  it('uses two decimals for ordinary values', () => {
    expect(formatEvalue(0.5)).toBe('0.50')
    expect(formatEvalue(0.001)).toBe('1.00e-3')
    expect(formatEvalue(0.0123)).toBe('0.01')
    expect(formatEvalue(0)).toBe('0.00')
  })

  it('falls back when missing', () => {
    expect(formatEvalue(undefined)).toBe('Unavailable')
  })
})

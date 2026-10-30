import { useCallback, useEffect, useRef, useState } from 'react'
import './ZoomFigure.css'

const MIN_ZOOM = 1
const MAX_ZOOM = 8
const STEP = 1.5

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

/**
 * Wraps a figure (usually an SVG chart) so it can be magnified and panned.
 *
 * - Buttons: zoom in, zoom out, reset (each with a text label, 44px targets).
 * - Pointer: drag to pan once zoomed; Ctrl/Cmd + wheel zooms. A plain wheel is
 *   left alone so the page never gets stuck while scrolling.
 * - Keyboard: with the figure focused, + / - zoom, 0 resets, arrows pan.
 * - The zoom level is announced in a polite live region.
 */
function ZoomFigure({ label, children, className = '', caption }) {
  const viewportRef = useRef(null)
  const dragRef = useRef(null)
  const [view, setView] = useState({ k: 1, x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)

  const constrain = useCallback((next) => {
    const element = viewportRef.current
    const width = element?.clientWidth ?? 0
    const height = element?.clientHeight ?? 0
    const k = clamp(next.k, MIN_ZOOM, MAX_ZOOM)

    return {
      k,
      x: clamp(next.x, Math.min(0, width * (1 - k)), 0),
      y: clamp(next.y, Math.min(0, height * (1 - k)), 0),
    }
  }, [])

  const zoomAt = useCallback(
    (factor, originX, originY) => {
      setView((current) => {
        const k = clamp(current.k * factor, MIN_ZOOM, MAX_ZOOM)
        const ratio = k / current.k

        return constrain({
          k,
          x: originX - (originX - current.x) * ratio,
          y: originY - (originY - current.y) * ratio,
        })
      })
    },
    [constrain],
  )

  const zoomFromCentre = useCallback(
    (factor) => {
      const element = viewportRef.current
      zoomAt(factor, (element?.clientWidth ?? 0) / 2, (element?.clientHeight ?? 0) / 2)
    },
    [zoomAt],
  )

  const reset = useCallback(() => setView({ k: 1, x: 0, y: 0 }), [])

  // A non-passive listener is needed to cancel the browser's page zoom.
  useEffect(() => {
    const element = viewportRef.current
    if (!element) return undefined

    function onWheel(event) {
      if (!event.ctrlKey && !event.metaKey) return
      event.preventDefault()
      const rect = element.getBoundingClientRect()
      zoomAt(
        event.deltaY < 0 ? STEP : 1 / STEP,
        event.clientX - rect.left,
        event.clientY - rect.top,
      )
    }

    element.addEventListener('wheel', onWheel, { passive: false })
    return () => element.removeEventListener('wheel', onWheel)
  }, [zoomAt])

  function onPointerDown(event) {
    if (view.k === 1 || event.button !== 0) return
    dragRef.current = { x: event.clientX, y: event.clientY, view }
    setDragging(true)
    event.currentTarget.setPointerCapture?.(event.pointerId)
  }

  function onPointerMove(event) {
    const drag = dragRef.current
    if (!drag) return
    setView(
      constrain({
        k: drag.view.k,
        x: drag.view.x + event.clientX - drag.x,
        y: drag.view.y + event.clientY - drag.y,
      }),
    )
  }

  function endDrag(event) {
    if (!dragRef.current) return
    dragRef.current = null
    setDragging(false)
    event.currentTarget.releasePointerCapture?.(event.pointerId)
  }

  function onKeyDown(event) {
    const pan = 40
    const actions = {
      '+': () => zoomFromCentre(STEP),
      '=': () => zoomFromCentre(STEP),
      '-': () => zoomFromCentre(1 / STEP),
      _: () => zoomFromCentre(1 / STEP),
      0: reset,
      ArrowLeft: () => setView((v) => constrain({ ...v, x: v.x + pan })),
      ArrowRight: () => setView((v) => constrain({ ...v, x: v.x - pan })),
      ArrowUp: () => setView((v) => constrain({ ...v, y: v.y + pan })),
      ArrowDown: () => setView((v) => constrain({ ...v, y: v.y - pan })),
    }
    const action = actions[event.key]
    if (!action) return
    if (event.key.startsWith('Arrow') && view.k === 1) return
    event.preventDefault()
    action()
  }

  const zoomed = view.k > 1

  return (
    <figure className={`zoom-figure ${className}`.trim()}>
      <div className="zoom-figure-tools" role="group" aria-label={`${label} zoom controls`}>
        <button
          type="button"
          onClick={() => zoomFromCentre(1 / STEP)}
          disabled={view.k <= MIN_ZOOM}
          aria-label={`Zoom out ${label}`}
        >
          <span aria-hidden="true">−</span>
        </button>
        <button
          type="button"
          onClick={() => zoomFromCentre(STEP)}
          disabled={view.k >= MAX_ZOOM}
          aria-label={`Zoom in ${label}`}
        >
          <span aria-hidden="true">+</span>
        </button>
        <button type="button" onClick={reset} disabled={!zoomed} aria-label={`Reset zoom for ${label}`}>
          Reset
        </button>
        <span className="zoom-figure-hint">
          {caption ?? 'Drag to pan when zoomed. Ctrl or ⌘ + scroll to zoom.'}
        </span>
        <span className="zoom-figure-level" aria-live="polite">
          {Math.round(view.k * 100)}%
        </span>
      </div>

      <div
        ref={viewportRef}
        className={`zoom-figure-viewport${zoomed ? ' is-zoomed' : ''}${dragging ? ' is-dragging' : ''}`}
        tabIndex={0}
        role="group"
        aria-label={`${label}. Press plus or minus to zoom, zero to reset, arrow keys to pan.`}
        onKeyDown={onKeyDown}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
      >
        <div
          className="zoom-figure-content"
          style={{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.k})` }}
        >
          {children}
        </div>
      </div>
    </figure>
  )
}

export default ZoomFigure

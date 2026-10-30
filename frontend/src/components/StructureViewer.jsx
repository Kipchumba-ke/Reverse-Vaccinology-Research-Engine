import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { fetchStructure, isUniprotAccession } from '../services/structureService'
import { centre, nearestPoint, parseCaTrace, project } from '../utils/pdb'
import { PLDDT_BANDS, residueColor } from '../utils/structureColors'

const VIEW_WIDTH = 640
const VIEW_HEIGHT = 480

const MODES = [
  { value: 'confidence', label: 'Model confidence (pLDDT)' },
  { value: 'annotation', label: 'Predicted features' },
  { value: 'plain', label: 'Plain' },
]

function StructureViewer({ accession, sequence, tracks = [] }) {
  const canvasRef = useRef(null)
  const dragRef = useRef(null)

  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [model, setModel] = useState(null)
  const [mode, setMode] = useState('confidence')
  const [view, setView] = useState({ rotX: 0.3, rotY: 0.6, zoom: 1 })
  const [hover, setHover] = useState(null)

  const trace = useMemo(() => {
    if (!model) return null
    return centre(parseCaTrace(model.pdb))
  }, [model])

  const projected = useMemo(() => {
    if (!trace) return []
    const scale = (Math.min(VIEW_WIDTH, VIEW_HEIGHT) / 2 - 24) / trace.radius
    return project(trace.points, {
      rotX: view.rotX,
      rotY: view.rotY,
      scale: scale * view.zoom,
      width: VIEW_WIDTH,
      height: VIEW_HEIGHT,
    })
  }, [trace, view])

  useEffect(() => {
    const canvas = canvasRef.current
    const context = canvas?.getContext?.('2d')
    // jsdom and some privacy modes have no 2-D context; skip drawing.
    if (!context || projected.length === 0) return

    context.clearRect(0, 0, VIEW_WIDTH, VIEW_HEIGHT)
    context.lineCap = 'round'

    const segments = []
    for (let i = 1; i < projected.length; i += 1) {
      const a = projected[i - 1]
      const b = projected[i]
      if (b.position - a.position !== 1) continue
      segments.push({ a, b, depth: (a.depth + b.depth) / 2 })
    }

    // Far segments first so near ones draw over them.
    segments.sort((s, t) => s.depth - t.depth)
    const depths = segments.map((s) => s.depth)
    const near = Math.max(...depths)
    const far = Math.min(...depths)
    const span = Math.max(near - far, 1e-6)

    for (const { a, b, depth } of segments) {
      const nearness = (depth - far) / span
      context.globalAlpha = 0.45 + 0.55 * nearness
      context.lineWidth = 1.5 + 2.5 * nearness
      context.strokeStyle = residueColor(b, mode, tracks)
      context.beginPath()
      context.moveTo(a.sx, a.sy)
      context.lineTo(b.sx, b.sy)
      context.stroke()
    }

    context.globalAlpha = 1
  }, [projected, mode, tracks])

  const load = useCallback(async () => {
    setStatus('loading')
    setError('')

    try {
      const token = localStorage.getItem('token')
      const data = await fetchStructure(accession.trim().toUpperCase(), token)
      setModel(data)
      setStatus('ready')
    } catch (loadError) {
      setError(loadError.message)
      setStatus('error')
    }
  }, [accession])

  if (!isUniprotAccession(accession)) {
    return (
      <p className="structure-note">
        A 3-D model can be fetched from the AlphaFold Database when the protein has a
        UniProt accession. This analysis has none, and no structure prediction is run
        here.
      </p>
    )
  }

  const onPointerDown = (event) => {
    dragRef.current = { x: event.clientX, y: event.clientY }
    event.currentTarget.setPointerCapture?.(event.pointerId)
  }

  const onPointerMove = (event) => {
    const rect = event.currentTarget.getBoundingClientRect()
    const scaleX = VIEW_WIDTH / (rect.width || VIEW_WIDTH)
    const scaleY = VIEW_HEIGHT / (rect.height || VIEW_HEIGHT)

    if (dragRef.current) {
      const dx = event.clientX - dragRef.current.x
      const dy = event.clientY - dragRef.current.y
      dragRef.current = { x: event.clientX, y: event.clientY }
      setView((current) => ({
        ...current,
        rotY: current.rotY + dx * 0.01,
        rotX: current.rotX + dy * 0.01,
      }))
      return
    }

    setHover(
      nearestPoint(
        projected,
        (event.clientX - rect.left) * scaleX,
        (event.clientY - rect.top) * scaleY,
      ),
    )
  }

  const endDrag = () => {
    dragRef.current = null
  }

  const onKeyDown = (event) => {
    const step = 0.12
    const moves = {
      ArrowLeft: { rotY: -step },
      ArrowRight: { rotY: step },
      ArrowUp: { rotX: -step },
      ArrowDown: { rotX: step },
    }
    const move = moves[event.key]
    if (!move) return
    event.preventDefault()
    setView((current) => ({
      ...current,
      rotX: current.rotX + (move.rotX ?? 0),
      rotY: current.rotY + (move.rotY ?? 0),
    }))
  }

  const zoomBy = (factor) =>
    setView((current) => ({
      ...current,
      zoom: Math.min(6, Math.max(0.3, current.zoom * factor)),
    }))

  const sequenceMatches =
    model && sequence ? model.reference_sequence === sequence : null

  return (
    <div className="structure-viewer">
      {status !== 'ready' && (
        <div className="structure-load">
          <button type="button" onClick={load} disabled={status === 'loading'}>
            {status === 'loading' ? 'Loading structure…' : 'Load predicted 3-D structure'}
          </button>
          <p className="structure-note">
            Fetches the model AlphaFold DB already holds for {accession.trim().toUpperCase()}.
            Nothing is predicted here.
          </p>
        </div>
      )}

      {status === 'error' && (
        <p role="alert" className="structure-error">
          {error}
        </p>
      )}

      {status === 'ready' && model && (
        <>
          <div className="structure-controls">
            <label>
              Colour by{' '}
              <select value={mode} onChange={(event) => setMode(event.target.value)}>
                {MODES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" onClick={() => zoomBy(1.25)} aria-label="Zoom in">
              +
            </button>
            <button type="button" onClick={() => zoomBy(0.8)} aria-label="Zoom out">
              −
            </button>
            <button
              type="button"
              onClick={() => setView({ rotX: 0.3, rotY: 0.6, zoom: 1 })}
            >
              Reset view
            </button>
          </div>

          <canvas
            ref={canvasRef}
            width={VIEW_WIDTH}
            height={VIEW_HEIGHT}
            tabIndex={0}
            role="img"
            aria-label={`Predicted 3-D backbone of ${model.accession}. Drag or use the arrow keys to rotate.`}
            className="structure-canvas"
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={endDrag}
            onPointerLeave={() => {
              endDrag()
              setHover(null)
            }}
            onKeyDown={onKeyDown}
          />

          <p className="structure-hover" aria-live="polite">
            {hover
              ? `Residue ${hover.position} (${hover.residue}), pLDDT ${hover.plddt.toFixed(1)}`
              : 'Hover over the trace to read a residue.'}
          </p>

          {mode === 'confidence' && (
            <ul className="structure-legend">
              {PLDDT_BANDS.map((band) => (
                <li key={band.label}>
                  <span className="structure-swatch" style={{ background: band.color }} />
                  {band.label}
                </li>
              ))}
            </ul>
          )}

          {mode === 'annotation' && (
            <>
              <ul className="structure-legend">
                {tracks.map((track) => (
                  <li key={track.id}>
                    <span className="structure-swatch" style={{ background: track.color }} />
                    {track.label}
                  </li>
                ))}
              </ul>
              <p className="structure-note">
                Where features overlap, the first one in this list sets the colour.
                Residues with no feature are grey.
              </p>
            </>
          )}

          <p className="structure-summary">
            {model.entry_id}, model v{model.model_version}, mean pLDDT {model.mean_plddt}. Source:{' '}
            {model.source}.
          </p>

          {sequenceMatches === false && (
            <p role="alert" className="structure-warning">
              The model is for the UniProt reference sequence, which differs from the
              sequence analysed here. Residue numbers and the feature colours may not line up.
            </p>
          )}

          <p className="structure-note">
            Backbone (C-alpha) trace of a predicted model, not an experimental structure.
            Regions with pLDDT below 70 are low confidence.
          </p>
        </>
      )}
    </div>
  )
}

export default StructureViewer

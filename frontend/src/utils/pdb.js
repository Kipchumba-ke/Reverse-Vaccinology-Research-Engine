// Reads C-alpha atoms from a PDB file and projects them for drawing.
// A C-alpha trace shows the fold, not side chains or secondary structure.

export function parseCaTrace(pdbText) {
  const points = []

  for (const line of String(pdbText ?? '').split('\n')) {
    if (!line.startsWith('ATOM') || line.slice(12, 16).trim() !== 'CA') continue

    const x = Number(line.slice(30, 38))
    const y = Number(line.slice(38, 46))
    const z = Number(line.slice(46, 54))
    const position = Number.parseInt(line.slice(22, 26), 10)
    const plddt = Number(line.slice(60, 66))

    if (![x, y, z, position, plddt].every(Number.isFinite)) continue

    points.push({
      position,
      residue: line.slice(17, 20).trim(),
      x,
      y,
      z,
      plddt,
    })
  }

  return points
}

export function centre(points) {
  if (points.length === 0) return { points: [], radius: 1 }

  const mean = (key) => points.reduce((sum, p) => sum + p[key], 0) / points.length
  const cx = mean('x')
  const cy = mean('y')
  const cz = mean('z')

  const moved = points.map((p) => ({ ...p, x: p.x - cx, y: p.y - cy, z: p.z - cz }))
  const radius = Math.max(
    ...moved.map((p) => Math.hypot(p.x, p.y, p.z)),
    1,
  )

  return { points: moved, radius }
}

// Rotate about the y axis, then the x axis, then scale to fit the view.
export function project(points, { rotX = 0, rotY = 0, scale = 1, width, height }) {
  const cosY = Math.cos(rotY)
  const sinY = Math.sin(rotY)
  const cosX = Math.cos(rotX)
  const sinX = Math.sin(rotX)

  return points.map((p) => {
    const x1 = p.x * cosY + p.z * sinY
    const z1 = -p.x * sinY + p.z * cosY
    const y2 = p.y * cosX - z1 * sinX
    const z2 = p.y * sinX + z1 * cosX

    return {
      position: p.position,
      residue: p.residue,
      plddt: p.plddt,
      sx: width / 2 + x1 * scale,
      sy: height / 2 - y2 * scale,
      depth: z2,
    }
  })
}

export function nearestPoint(projected, sx, sy, maxDistance = 12) {
  let best = null
  let bestDistance = maxDistance

  for (const p of projected) {
    const distance = Math.hypot(p.sx - sx, p.sy - sy)
    // Prefer points nearer the viewer when two are equally close.
    if (distance < bestDistance || (best && distance === bestDistance && p.depth > best.depth)) {
      best = p
      bestDistance = distance
    }
  }

  return best
}

// The reference sequence behind the model, as one-letter codes.
const THREE_TO_ONE = {
  ALA: 'A', ARG: 'R', ASN: 'N', ASP: 'D', CYS: 'C', GLN: 'Q', GLU: 'E',
  GLY: 'G', HIS: 'H', ILE: 'I', LEU: 'L', LYS: 'K', MET: 'M', PHE: 'F',
  PRO: 'P', SER: 'S', THR: 'T', TRP: 'W', TYR: 'Y', VAL: 'V',
}

export function sequenceOfTrace(points) {
  return points.map((p) => THREE_TO_ONE[p.residue] ?? 'X').join('')
}

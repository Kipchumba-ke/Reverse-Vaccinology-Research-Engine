import { useState } from "react"
import { submitAnalysis } from './services/analysisService'


function App() {
  const [submitted, setSubmitted] = useState(false) 
  const [sequence, setSequence] = useState('')
  const [error, setError] = useState(null)

  async function handleSubmit() {
    try {
      await submitAnalysis(sequence)
      setSubmitted(true)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main>
      <h1>Reverse Vaccinology</h1>

      < label htmlFor="protein-sequence">
        Protein Sequence
      </label>

      <textarea 
        id="protein-sequence" 
        name="protein-sequence" 
        value={sequence}
        onChange={(e) => setSequence(e.target.value)}
      />

      <button type="button" onClick={handleSubmit}>
        Analyze Protein
      </button>

      {submitted && (
        <p>
          Analysis submitted!
        </p>
      )}

      {error && (
        <p>
          {error}
        </p>
      )}
    </main>
  )
}

export default App

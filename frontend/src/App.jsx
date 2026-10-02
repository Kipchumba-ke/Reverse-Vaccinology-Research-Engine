import { useState } from "react"


function App() {
  const [submitted, setSubmitted] = useState(false) 

  function handleSubmit() {
    setSubmitted(true)
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
      />

      <button type="button" onClick={handleSubmit}>
        Analyze Protein
      </button>

      {submitted && (
        <p>
          Analysis submitted!
        </p>
      )}

    </main>
  )
}

export default App

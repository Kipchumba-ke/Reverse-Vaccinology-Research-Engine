
function App() {

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

      <button type="button">
        Analyze Protein
      </button>

    </main>
  )
}

export default App

import { useEffect, useState } from 'react'
import { getHealth } from './api.js'

export default function App() {
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <main className="container">
      <h1>ProcurePilot AI</h1>
      <p>Multi-agent procurement audit assistant.</p>

      <section className="card">
        <h2>Backend status</h2>
        {error && <p className="error">Unreachable: {error}</p>}
        {!error && !health && <p>Checking…</p>}
        {health && (
          <p>
            {health.status} (Python {health.python_version})
          </p>
        )}
      </section>
    </main>
  )
}

function App() {
  return (
    <div style={{
      display: 'flex',
      minHeight: '100vh',
      justifyContent: 'center',
      alignItems: 'center',
      fontFamily: 'Inter, system-ui, sans-serif',
      padding: '1rem',
      background: '#f5f7fb',
    }}>
      <div style={{
        maxWidth: 620,
        width: '100%',
        padding: '2rem',
        borderRadius: '16px',
        background: '#ffffff',
        boxShadow: '0 20px 50px rgba(15, 23, 42, 0.08)',
      }}>
        <h1 style={{ marginBottom: '1rem' }}>Equity Intelligence Platform</h1>
        <p style={{ marginBottom: '1rem', color: '#334155' }}>
          Welcome to the Equity Intelligence frontend starter page. The frontend is running successfully.
        </p>
        <p style={{ marginTop: '1rem', color: '#475569' }}>
          This platform is designed for research and decision support, not investment advice.
        </p>
      </div>
    </div>
  )
}

export default App

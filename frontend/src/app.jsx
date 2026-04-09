import { useState, useEffect, useRef } from 'preact/hooks';
import './index.css';

const POOLS = [
  { name: 'MiningOcean (Auto)', host: 'qrl.miningocean.org', port: 3333 },
  { name: 'HeroMiners (West)', host: 'qrl.herominers.com', port: 10371 },
  { name: 'Custom Stratum...', host: '', port: 0 }
];

export function App() {
  const [address, setAddress] = useState('Q0105007a9b2d5c63770e481ab66dbf0f87faefcc4a8b78990390919198642273087037f');
  const [poolIdx, setPoolIdx] = useState(0);
  const [customHost, setCustomHost] = useState('');
  const [customPort, setCustomPort] = useState(3333);
  
  const [threads, setThreads] = useState(1);
  const [physicalCores, setPhysicalCores] = useState(1);
  const [logicalThreads, setLogicalThreads] = useState(1);
  const [isTurbo, setIsTurbo] = useState(false);
  const [useTls, setUseTls] = useState(false);
  
  const [stats, setStats] = useState({ hashrate: 0, shares: 0, running: false });
  const [errorHeader, setErrorHeader] = useState(null);
  const [logs, setLogs] = useState([
    { time: '00:00:00', cat: 'PROC', msg: 'System initialized. Ready for substrate deployment.' }
  ]);
  const ws = useRef(null);
  const cliRef = useRef(null);

  useEffect(() => {
    fetch(`http://${window.location.hostname}:8000/status`)
      .then(res => res.json())
      .then(data => {
        setPhysicalCores(data.physical_threads);
        setLogicalThreads(data.max_threads);
        setThreads(data.physical_threads);
      })
      .catch(() => setErrorHeader("Hardware Substrate offline. Check Backend."));
    
    connectWS();
    return () => ws.current?.close();
  }, []);

  const connectWS = () => {
    ws.current = new WebSocket(`ws://${window.location.hostname}:8000/ws`);
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStats(data);
      if (data.logs && data.logs.length > 0) {
        setLogs(data.logs);
      }
    };
    ws.current.onerror = () => setErrorHeader("Communication link severed. Reconnecting...");
    ws.current.onopen = () => {
        setErrorHeader(null);
        setLogs(prev => [...prev, { time: new Date().toLocaleTimeString().split(' ')[0], cat: 'NET', msg: 'Quantum link established.' }]);
    }
    ws.current.onclose = () => setTimeout(connectWS, 3000);
  };

  useEffect(() => {
    if (cliRef.current) {
      cliRef.current.scrollTop = cliRef.current.scrollHeight;
    }
  }, [logs]);

  const handleTurboToggle = () => {
    if (stats.running) return;
    const newTurbo = !isTurbo;
    setIsTurbo(newTurbo);
    setThreads(newTurbo ? logicalThreads : physicalCores);
  };

  const toggleMining = async () => {
    const endpoint = stats.running ? '/stop' : '/start';
    const pool = POOLS[poolIdx];
    const payload = stats.running ? {} : { 
      address, 
      threads: Number(threads),
      host: pool.name.includes('Custom') ? customHost : pool.host,
      port: pool.name.includes('Custom') ? Number(customPort) : pool.port,
      use_tls: useTls
    };
    
    try {
      const response = await fetch(`http://${window.location.hostname}:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: endpoint === '/start' ? JSON.stringify(payload) : undefined
      });
      
      const result = await response.json();
      if (!result.success && result.message) {
        setErrorHeader(`Protocol Error: ${result.message}`);
      } else if (endpoint === '/start') {
        setErrorHeader(null);
      }
    } catch (e) {
      setErrorHeader("Network Failure: Backend Unreachable");
    }
  };

  return (
    <>
      <div className="mesh-bg"></div>
      
      {errorHeader && (
        <div className="error-banner">
          ⚠️ SYSTEM ALERT: {errorHeader}
        </div>
      )}

      <img src="/logo.png" className="logo-main" alt="QRL Logo" style={{ marginTop: errorHeader ? '4rem' : '0' }} />
      <h1 className={stats.running ? 'quantum-pulse' : ''}>QRL Miner Core</h1>
      <div className="subtitle">Quantum Resistant Substrate</div>

      <div className="dashboard-layout">
        <div className="glass-panel config-group">
          <div className="input-section">
            <label>Encrypted Address Segment</label>
            <input 
              type="text" 
              className="input-glow"
              value={address} 
              onInput={(e) => setAddress(e.target.value)}
              disabled={stats.running}
            />
          </div>

          <div className="input-section">
            <label>Target Stratum Cluster</label>
            <select 
              className="input-glow" 
              value={poolIdx} 
              onChange={(e) => setPoolIdx(e.target.value)}
              disabled={stats.running}
            >
              {POOLS.map((p, i) => <option value={i}>{p.name}</option>)}
            </select>
          </div>

          {POOLS[poolIdx].name.includes('Custom') && (
            <div className="grid-2" style={{ marginTop: '1rem' }}>
              <input 
                type="text" className="input-glow" placeholder="host..." 
                value={customHost} onInput={(e) => setCustomHost(e.target.value)} 
                disabled={stats.running}
              />
              <input 
                type="number" className="input-glow" placeholder="port..." 
                value={customPort} onInput={(e) => setCustomPort(e.target.value)} 
                disabled={stats.running}
              />
            </div>
          )}

          <div className="tuning-section" style={{ marginTop: '0.5rem', background: 'rgba(56, 189, 248, 0.05)' }}>
            <div className="flex-between">
              <label style={{ margin: 0 }}>Security Layer</label>
              <div 
                className="toggle-container" 
                onClick={() => setUseTls(!useTls)}
                style={{ cursor: 'pointer' }}
              >
                <div className={`toggle-track ${useTls ? 'active' : ''}`} style={useTls ? {background: 'var(--neon-green)'} : {}}>
                  <div className="toggle-thumb" style={useTls ? {transform: 'translateX(20px)'} : {}}></div>
                </div>
                <span className="toggle-label" style={{ color: useTls ? 'var(--neon-green)' : 'var(--text-dim)', fontSize: '0.7rem' }}>
                  {useTls ? 'STRATUM+SSL ENCRYPTED' : 'STANDARD TCP (UNSECURED)'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="tuning-section">
            <div className="flex-between">
              <label>Substrate Tuning</label>
              <div className={`tuning-badge ${isTurbo ? 'turbo' : 'balanced'}`}>
                {isTurbo ? 'MAX POWER' : 'BALANCED'}: {threads} CORES
              </div>
            </div>
            <div className="toggle-container" onClick={handleTurboToggle}>
                <div className={`toggle-track ${isTurbo ? 'active' : ''}`}>
                    <div className="toggle-thumb"></div>
                </div>
                <span className="toggle-label">{isTurbo ? 'Turbo Mode Active (Logical Threads)' : 'Efficient Mode Active (Physical Cores)'}</span>
            </div>
          </div>

          <button 
            className={`btn-premium ${stats.running ? 'btn-stop' : 'btn-start'}`}
            onClick={toggleMining}
          >
            {stats.running ? 'Halt Sequence' : 'Initialize Miner'}
          </button>
        </div>

        <div className="glass-panel stats-group">
          <div className="stats-grid-v2">
            <div className="stat-widget">
              <span className="stat-header">Network Hashrate</span>
              <span className={`stat-data ${stats.running ? 'highlight' : ''}`}>
                {stats.hashrate} <span style={{fontSize: '0.8rem'}}>H/s</span>
              </span>
            </div>
            <div className="stat-widget">
              <span className="stat-header">Accepted Work</span>
              <span className="stat-data">{stats.shares}</span>
            </div>
            <div className="stat-widget">
              <span className="stat-header">Current Substrate</span>
              <span className="stat-data" style={{ fontSize: '1.2rem', color: stats.running ? '#10b981' : '#ef4444' }}>
                {stats.running ? 'ENCRYPTING' : 'READY'}
              </span>
            </div>
            <div className="stat-widget">
              <span className="stat-header">Cluster Node</span>
              <span className="stat-data" style={{ fontSize: '1.2rem' }}>
                {POOLS[poolIdx].name.includes('Custom') ? 'CUSTOM-LINK' : POOLS[poolIdx].name.split(' ')[0]}
              </span>
            </div>
          </div>
        </div>

        <div className="glass-panel chart-group">
          <label>Performance Temporal System // CLI</label>
          <div className="cli-container" ref={cliRef}>
            {logs.map((log, i) => (
              <div key={i} className="cli-line">
                <span className="cli-time">[{log.time}]</span>
                <span className={`cli-cat cat-${log.cat}`}>{log.cat}</span>
                <span className="cli-msg">{log.msg}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <footer className="footer-credits">
        SYSTEM VERSION 3.0.0-QUANTUM | SECURED BY RANDOM-X
      </footer>
    </>
  );
}

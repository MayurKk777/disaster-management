import React, { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await axios.get('http://localhost:8000/dashboard');
        setData(res.data);
      } catch (e) {}
    };
    fetch();
    const id = setInterval(fetch, 5000);
    return () => clearInterval(id);
  }, []);

  if (!data) return <div className="container"><h1>Loading EcoRescue...</h1></div>;

  return (
    <div className="container">
      <div className="header">
        <div>
          <h1>EcoRescue</h1>
          <p style={{color:'#94a3b8'}}>AI-Powered Disaster Response System</p>
        </div>
        <div className="status">● System Active</div>
      </div>

      <div className="stats">
        <div className="card"><h3>Total People Detected</h3><p>{data.total_people || 0}</p></div>
        <div className="card"><h3>Available Shelter Beds</h3><p className="green">{data.available_beds || 0}</p></div>
        <div className="card"><h3>Active Volunteers</h3><p>{data.active_volunteers || '0/0'}</p></div>
        <div className="card"><h3>Critical Zones</h3><p className="red">{data.critical_zones || 0}</p></div>
      </div>

      <h2 style={{fontSize:'2.5rem', marginBottom:'1rem'}}>Zone Monitoring</h2>
      <p style={{color:'#94a3b8', marginBottom:'3rem'}}>Real-time risk assessment across all zones</p>

      <div className="zones">
  {data.zones?.map((z: any) => {
    const level = z.risk_level?.toLowerCase() || 'safe';  // ← safe fallback
    return (
      <div key={z.id} className={`zone ${level}`}>
        <div className="zone-header">
          <h3>{z.name}</h3>
          <span className={`badge ${level}`}>{z.risk_level || 'Safe'}</span>
        </div>
        <div className="zone-stats">
          <div>Detected: <strong style={{fontSize:'2rem'}}>{z.detected || 0}</strong></div>
          <div>Beds: <strong style={{fontSize:'20'}}>{z.beds || 0}</strong></div>
          <div>Volunteers: <strong style={{fontSize:'2rem'}}>{z.volunteers || 0}</strong></div>
          <div>Freq: <strong style={{fontSize:'2rem'}}>{z.freq || 0}/30min</strong></div>
        </div>
      </div>
    );
  })}
</div>
    </div>
  );
}

export default App;
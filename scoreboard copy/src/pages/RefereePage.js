import React, { useState, useEffect } from 'react';
import './RefereePage.css';
import { MdRefresh } from 'react-icons/md';

function RefereePage() {
  const [isRunning, setIsRunning] = useState(false);
  const [team1Foul, setTeam1Foul] = useState(0);
  const [team2Foul, setTeam2Foul] = useState(0);

  useEffect(() => {
    const updateFouls = () => {
      const state = JSON.parse(localStorage.getItem('visioncourt-state')) || { fouls: { teamA: 0, teamB: 0 } };
      setTeam1Foul(state.fouls.teamA);
      setTeam2Foul(state.fouls.teamB);
    };
    window.addEventListener('storage', updateFouls);
    updateFouls();
    return () => window.removeEventListener('storage', updateFouls);
  }, []);

  const sendControl = (type, payload) => {
    localStorage.setItem('visioncourt-control', JSON.stringify({
      type,
      payload,
      timestamp: Date.now()
    }));
  };

  return (
    <div className="referee-container">
      <h1 className="title">CONTROLLER</h1>
      {/* <div className="status connected">🔗 Ready (Offline Mode)</div> */}

      <div className="circle-button-group">
        <div className="circle-btn-wrapper">
          <button
            className={`circle-btn ${isRunning ? 'btn-stop' : 'btn-start'}`}
            onClick={() => {
              setIsRunning(r => !r);
              sendControl('GAME_CONTROL', { action: isRunning ? 'pause' : 'start' });
            }}
          >
            {isRunning ? '⏸' : '▶'}
          </button>
          <div className="btn-label">
            {isRunning ? 'pause' : 'start'}
          </div>
        </div>
        <div className="circle-btn-wrapper">
          <button
            className="circle-btn btn-reset"
            onClick={() => sendControl('SHOT_CLOCK_CONTROL', { action: 'reset' })}
          >
            <MdRefresh size={28} />
          </button>
          <div className="btn-label">reset</div>
        </div>
      </div>

      <div className="foul-controls">
        <div className="foul-panel">
          <h2 className="team-a-text">TEAM A</h2>
          <div className="foul-count team-a">{team1Foul}</div>
          <button
            className="foul-btn team-a"
            onClick={() => sendControl('FOUL_CONTROL', { team: 'A' })}
          >
            🟥 FOUL
          </button>
        </div>
        <div className="foul-panel">
          <h2 className="team-b-text">TEAM B</h2>
          <div className="foul-count team-b">{team2Foul}</div>
          <button
            className="foul-btn team-b"
            onClick={() => sendControl('FOUL_CONTROL', { team: 'B' })}
          >
            🟦 FOUL
          </button>
        </div>
      </div>
    </div>
  );
}

export default RefereePage;
import React from 'react';
import './Scoreboard.css';

// 게임 시간을 분:초 형식으로 변환하는 함수
const formatGameTime = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
};

function Scoreboard({ scores, fouls, gameTime, shotClock, period, shotClockWarning }) {
  return (
    <div className={`scoreboard-container ${shotClockWarning ? 'warning' : ''}`}>      {/* Top Row: Team Names */}
      <div className="team-name home">TeamA</div>
      <div className="team-name guest">TeamB</div>

      {/* Middle Row: Scores, Game Clock, Period */}
      <div className="score home-score">{scores.teamA.toString().padStart(2, '0')}</div>
      <div className="game-clock-section">
        <div className="game-time">{formatGameTime(gameTime)}</div>
        <div className="period-section">
          <div className="period-label">PERIOD</div>
          <div className="period-number">{period}</div>
        </div>
      </div>
      <div className="score guest-score">{scores.teamB.toString().padStart(2, '0')}</div>

      {/* Bottom Row: Fouls and Shot Clock */}
      <div className="fouls-section home-fouls">
        <div className="fouls-label">FOULS</div>
        <div className="fouls-number">{fouls.teamA.toString().padStart(2, '0')}</div>
      </div>
      <div className="shot-clock-section">
        <div className="shot-clock-label">SHOT CLOCK</div>
        <div className="shot-clock-time">{shotClock.toString().padStart(2, '0')}</div>
      </div>
      <div className="fouls-section guest-fouls">
        <div className="fouls-label">FOULS</div>
        <div className="fouls-number">{fouls.teamB.toString().padStart(2, '0')}</div>
      </div>
    </div>
  );
}

export default Scoreboard;
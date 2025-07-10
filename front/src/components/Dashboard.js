import React from 'react';
import './Dashboard.css';

function Dashboard({ data }) {
  if (!data) {
    return <div>경기 결과를 불러오는 중입니다...</div>;
  }

  const { finalScore, gameStats } = data;

  return (
    <div className="dashboard-container">
      <h1>경기 종료</h1>
      <h2>최종 점수</h2>
      <div className="final-score">
        <span>HOME {finalScore.A}</span> : <span>{finalScore.B} AWAY</span>
      </div>
      <div className="game-stats">
        <h3>주요 스탯</h3>
        {/* gameStats 객체를 기반으로 원하는 통계 데이터를 표시 */}
        <p>예: 최다 득점 선수, 리바운드, 어시스트 등</p>
        <pre>{JSON.stringify(gameStats, null, 2)}</pre>
      </div>
    </div>
  );
}

export default Dashboard;
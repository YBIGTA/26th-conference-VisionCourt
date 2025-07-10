// App.js

import React, { createContext, useContext, useRef, useState, useEffect } from 'react'; // ✅ createContext, useContext 등을 직접 import
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ScoreboardPage from './pages/ScoreboardPage';
import RefereePage from './pages/RefereePage';
import VideoUploadPage from './pages/VideoUploadPage';

// ✅ 1. App.js 파일 내에서 Context를 직접 생성하고 export 합니다.
const GameContext = createContext(null);
export const useGameContext = () => useContext(GameContext);

const SHOT_CLOCK_RESET = 12;

function App() {
  // ✅ 2. 이전에 GameProvider에 있던 모든 상태 관리 로직을 App 컴포넌트 안으로 가져옵니다.
  const [scores, setScores] = useState({ teamA: 0, teamB: 0 });
  const [shotClock, setShotClock] = useState(SHOT_CLOCK_RESET);
  const [gameTime, setGameTime] = useState(600);
  const [fouls, setFouls] = useState({ teamA: 0, teamB: 0 });
  const [period, setPeriod] = useState(1);
  const [isMainClockRunning, setIsMainClockRunning] = useState(false);
  const [isShotClockRunning, setIsShotClockRunning] = useState(false);
  
  const mainClockTimer = useRef();
  const shotClockTimer = useRef();
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = new WebSocket("ws://13.125.244.130:8000/ws/yolo/");
    socketRef.current.onopen = () => console.log("✅ WebSocket 연결 성공 (App.js)");

    socketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // console.log("📩 [App.js] 서버에서 수신한 메시지:", data);
    
        // 1) 기존 액션 처리
        if (data.main_clock_action === "pause")  setIsMainClockRunning(false);
        if (data.main_clock_action === "start")  setIsMainClockRunning(true);
        if (data.shot_clock_action === "pause") setIsShotClockRunning(false);
        if (data.shot_clock_action === "start") setIsShotClockRunning(true);
        if (data.shot_clock_action === "reset") {
          setShotClock(SHOT_CLOCK_RESET);
          setIsShotClockRunning(true);
        }
    
        // 2) **여기에 추가**: 서버가 보내주는 남은 시간 동기화
        if (typeof data.main_clock === "number") {
          setGameTime(data.main_clock);
        }
        if (typeof data.shot_clock === "number") {
          setShotClock(data.shot_clock);
        }
    
      } catch (error) {
        console.error("수신 데이터 처리 오류:", error);
      }
    };
    // ... onerror, onclose 핸들러 ...
    return () => socketRef.current?.close();
  }, []);

  // ... 타이머 로직들은 이전과 동일 ...
  useEffect(() => {
    if (isMainClockRunning) {
      mainClockTimer.current = setInterval(() => setGameTime(prev => Math.max(0, prev - 1)), 1000);
    } else {
      clearInterval(mainClockTimer.current);
    }
    return () => clearInterval(mainClockTimer.current);
  }, [isMainClockRunning]);

  useEffect(() => {
    if (isShotClockRunning) {
      shotClockTimer.current = setInterval(() => setShotClock(prev => Math.max(0, prev - 1)), 1000);
    } else {
      clearInterval(shotClockTimer.current);
    }
    return () => clearInterval(shotClockTimer.current);
  }, [isShotClockRunning]);

  // 방송으로 내보낼 값들을 객체로 묶음
  const contextValue = {
    socket: socketRef.current,
    scores,
    shotClock,
    gameTime,
    fouls,
    period,
  };

  return (
    // ✅ 3. GameContext.Provider로 감싸고, contextValue를 value로 전달합니다.
    <GameContext.Provider value={contextValue}>
      <Router>
        <Routes>
          <Route path="/scoreboard" element={<ScoreboardPage />} />
          <Route path="/referee" element={<RefereePage />} />
          <Route path="/upload" element={<VideoUploadPage />} />
        </Routes>
      </Router>
    </GameContext.Provider>
  );
}

export default App;


// import React, { useState, useEffect, useRef } from 'react';
// import { useLocation } from 'react-router-dom';
// import Scoreboard from '../components/Scoreboard';

// const SHOT_CLOCK_RESET = 12;
// const FPS = 10;

// function ScoreboardPage() {
//   const location = useLocation();
//   const videoUrl = localStorage.getItem('uploadedVideoUrl');
  
//   const [scores, setScores] = useState({ teamA: 0, teamB: 0 });
//   const [shotClock, setShotClock] = useState(SHOT_CLOCK_RESET);
//   const [gameTime, setGameTime] = useState(600);
//   const [fouls, setFouls] = useState({ teamA: 0, teamB: 0 });
//   const [period, setPeriod] = useState(1);
//   const [isMainClockRunning, setIsMainClockRunning] = useState(false);
//   const [isShotClockRunning, setIsShotClockRunning] = useState(false);
//   const [shotClockWarning, setShotClockWarning] = useState(false);
//   const [videoReady, setVideoReady] = useState(false);
//   const [wsReady, setWsReady] = useState(false);

//   const mainClockTimer = useRef();
//   const shotClockTimer = useRef();
//   const yoloSocketRef = useRef(null);

//   const videoRef = useRef(null);
//   const canvasRef = useRef(null);
//   const frameIntervalRef = useRef(null);

//   useEffect(() => {
//     yoloSocketRef.current = new WebSocket("ws://13.125.244.130:8000/ws/yolo/");

//     yoloSocketRef.current.onopen = () => {
//       console.log("🟢 YOLO WebSocket 연결 완료");
//       setWsReady(true);
//     };

//     yoloSocketRef.current.onmessage = (event) => {
//       console.log("📩 WebSocket 메시지 수신:", event.data);
//       try {
//         const data = JSON.parse(event.data);

//         // 기존 foul / score / shot reset 처리
//         if (data.foul_action) {
//           if (data.foul_action.team === 'A') setFouls(f => ({ ...f, teamA: f.teamA + 1 }));
//           if (data.foul_action.team === 'B') setFouls(f => ({ ...f, teamB: f.teamB + 1 }));
//         }
//         if (data.score_action) {
//           if (data.score_action.team === 'A') setScores(s => ({ ...s, teamA: s.teamA + 2 }));
//           if (data.score_action.team === 'B') setScores(s => ({ ...s, teamB: s.teamB + 2 }));
//         }
//         if (data.shot_clock_action === "reset") {
//           setShotClock(SHOT_CLOCK_RESET);
//           setIsShotClockRunning(true);
//         }

//         // ── 여기에 추가한 부분 ──

//         // 1) main_clock_action 으로 시계 상태 제어
//         if (data.main_clock_action === "start") {
//           setIsMainClockRunning(true);
//           setIsShotClockRunning(true);
//         }
//         if (data.main_clock_action === "pause") {
//           setIsMainClockRunning(false);
//           setIsShotClockRunning(false);
//         }

//         // 2) 서버에서 내려주는 남은 시간으로 동기화
//         if (typeof data.main_clock === "number") {
//           setGameTime(data.main_clock);
//         }
//         if (typeof data.shot_clock === "number") {
//           setShotClock(data.shot_clock);
//         }

//       } catch (e) {
//         console.error("JSON 파싱 에러:", e, event.data);
//       }
//     };

//     yoloSocketRef.current.onerror = (err) => {
//       console.error("WebSocket 에러:", err);
//     };

//     yoloSocketRef.current.onclose = () => {
//       console.warn("WebSocket 연결 종료");
//     };

//     return () => {
//       yoloSocketRef.current?.close();
//     };
//   }, []);

//   const handleVideoCanPlay = () => {
//     setVideoReady(true);
//   };

//   useEffect(() => {
//     if (videoReady && wsReady) {
//       startFrameProcessing();
//     }
//     return () => stopFrameProcessing();
//   }, [videoReady, wsReady]);

//   const startFrameProcessing = () => {
//     const video = videoRef.current;
//     const canvas = canvasRef.current;
//     if (!video || !canvas) return;

//     canvas.width = video.videoWidth;
//     canvas.height = video.videoHeight;
//     video.play();

//     frameIntervalRef.current = setInterval(() => {
//       if (video.paused || video.ended) return;

//       const ctx = canvas.getContext('2d');
//       ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
//       const dataURL = canvas.toDataURL('image/jpeg', 0.8);

//       if (yoloSocketRef.current.readyState === WebSocket.OPEN) {
//         yoloSocketRef.current.send(JSON.stringify({ image: dataURL }));
//         console.log('🟢 YOLO WebSocket 프레임 전송 완료');
//       } else {
//         console.warn("⚠️ WebSocket 연결되지 않음. 프레임 전송 생략됨.");
//       }
//     }, 1000 / FPS);
//   };

//   const stopFrameProcessing = () => {
//     clearInterval(frameIntervalRef.current);
//   };

//   // 로컬 스토리지로 파울/샷/게임 제어
//   useEffect(() => {
//     const handleStorage = (event) => {
//       if (event.key === 'visioncourt-control') {
//         const control = JSON.parse(event.newValue);
//         if (!control) return;
//         if (control.type === 'GAME_CONTROL') {
//           if (control.payload.action === 'start') {
//             setIsMainClockRunning(true);
//             setIsShotClockRunning(true);
//           }
//           if (control.payload.action === 'pause') {
//             setIsMainClockRunning(false);
//             setIsShotClockRunning(false);
//           }
//         }
//         if (control.type === 'SHOT_CLOCK_CONTROL' && control.payload.action === 'reset') {
//           setShotClock(SHOT_CLOCK_RESET);
//           setIsShotClockRunning(true);
//         }
//         if (control.type === 'FOUL_CONTROL') {
//           if (control.payload.team === 'A') setFouls(f => ({ ...f, teamA: f.teamA + 1 }));
//           if (control.payload.team === 'B') setFouls(f => ({ ...f, teamB: f.teamB + 1 }));
//         }
//       }
//     };
//     window.addEventListener('storage', handleStorage);
//     return () => window.removeEventListener('storage', handleStorage);
//   }, []);

//   // 파울/period 상태를 localStorage에 저장
//   useEffect(() => {
//     const state = { fouls, period };
//     localStorage.setItem('visioncourt-state', JSON.stringify(state));
//   }, [fouls, period]);

//   // 메인 클락 타이머
//   useEffect(() => {
//     if (isMainClockRunning) {
//       mainClockTimer.current = setInterval(() => {
//         setGameTime(prev => Math.max(0, prev - 1));
//       }, 1000);
//     } else {
//       clearInterval(mainClockTimer.current);
//     }
//     return () => clearInterval(mainClockTimer.current);
//   }, [isMainClockRunning]);

//   // 샷 클락 타이머
//   useEffect(() => {
//     if (isShotClockRunning) {
//       shotClockTimer.current = setInterval(() => {
//         setShotClock(prev => Math.max(0, prev - 1));
//       }, 1000);
//     } else {
//       clearInterval(shotClockTimer.current);
//     }
//     return () => clearInterval(shotClockTimer.current);
//   }, [isShotClockRunning]);

//   // 샷 클락 경고 및 리셋
//   useEffect(() => {
//     if (shotClock === 0) {
//       setShotClockWarning(true);
//       setShotClock(SHOT_CLOCK_RESET);
//     }
//   }, [shotClock]);

//   useEffect(() => {
//     if (shotClockWarning) {
//       const timeout = setTimeout(() => setShotClockWarning(false), 500);
//       return () => clearTimeout(timeout);
//     }
//   }, [shotClockWarning]);

//   return (
//     <div
//       style={{
//         height: '95vh',
//         display: 'flex',
//         flexDirection: 'column',
//         alignItems: 'center'
//       }}
//     >
//       <Scoreboard
//         scores={scores}
//         fouls={fouls}
//         gameTime={gameTime}
//         shotClock={shotClock}
//         period={period}
//         shotClockWarning={shotClockWarning}
//       />

//       {videoUrl && (
//         <video
//           ref={videoRef}
//           src={videoUrl}
//           width="100%"
//           style={{
//             height: '40vh',
//             width: 'auto',
//             display: 'block',
//             margin: '2rem auto 0 auto'
//           }}
//           controls
//           muted
//           onCanPlay={handleVideoCanPlay}
//           onEnded={stopFrameProcessing}
//         />
//       )}

//       <canvas ref={canvasRef} style={{ display: 'none' }} />
//     </div>
//   );
// }

// export default ScoreboardPage;


import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import Scoreboard from '../components/Scoreboard';

const SHOT_CLOCK_RESET = 12;
const FPS = 5;

function ScoreboardPage() {
  const location = useLocation();
  const videoUrl = localStorage.getItem('uploadedVideoUrl');
  
  const [scores, setScores] = useState({ teamA: 0, teamB: 0 });
  const [shotClock, setShotClock] = useState(SHOT_CLOCK_RESET);
  const [gameTime, setGameTime] = useState(600);
  const [fouls, setFouls] = useState({ teamA: 0, teamB: 0 });
  const [period, setPeriod] = useState(1);
  const [isMainClockRunning, setIsMainClockRunning] = useState(false);
  const [isShotClockRunning, setIsShotClockRunning] = useState(false);
  const [shotClockWarning, setShotClockWarning] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const [wsReady, setWsReady] = useState(false);

  const mainClockTimer = useRef();
  const shotClockTimer = useRef();
  const yoloSocketRef = useRef(null);
  const hasTimerStartedRef = useRef(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const frameIntervalRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket("ws://13.125.244.130:8000/ws/yolo/");
    yoloSocketRef.current = ws;

    ws.onopen = () => {
      console.log("🟢 YOLO WebSocket 연결 완료");
      setWsReady(true);
    };

    ws.onmessage = (event) => {
      console.log("📩 WebSocket 메시지 수신:", event.data);
      try {
        const data = JSON.parse(event.data);

        // foul / score 처리
        if (data.foul_action) {
          setFouls(f => ({
            teamA: f.teamA + (data.foul_action.team === 'A'),
            teamB: f.teamB + (data.foul_action.team === 'B')
          }));
        }
        if (data.score_action) {
          setScores(s => ({
            teamA: s.teamA + (data.score_action.team === 'A') * 2,
            teamB: s.teamB + (data.score_action.team === 'B') * 2
          }));
        }

        // WS shot clock reset
        if (data.shot_clock_action === "reset") {
          setShotClock(SHOT_CLOCK_RESET);
        }
      } catch (e) {
        console.error("JSON 파싱 에러:", e, event.data);
      }
    };

    ws.onerror = (err) => console.error("WebSocket 에러:", err);
    ws.onclose = () => console.warn("WebSocket 연결 종료");

    return () => ws.close();
  }, []);

  const handleVideoCanPlay = () => setVideoReady(true);

  useEffect(() => {
    if (videoReady && wsReady) {
      startFrameProcessing();
    }
    return () => stopFrameProcessing();
  }, [videoReady, wsReady]);

  const startFrameProcessing = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    video.play();

    // 첫 프레임 전송 시 타이머 시작
    if (!hasTimerStartedRef.current) {
      setIsMainClockRunning(true);
      setIsShotClockRunning(true);
      hasTimerStartedRef.current = true;
    }

    frameIntervalRef.current = setInterval(() => {
      if (video.paused || video.ended) return;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataURL = canvas.toDataURL('image/jpeg', 0.8);

      if (yoloSocketRef.current.readyState === WebSocket.OPEN) {
        yoloSocketRef.current.send(JSON.stringify({ image: dataURL }));
        console.log('🟢 YOLO WebSocket 프레임 전송 완료');
      }
    }, 1000 / FPS);
  };

  const stopFrameProcessing = () => {
    clearInterval(frameIntervalRef.current);
  };

  // local storage 이벤트로 pause/start/reset 반영
  useEffect(() => {
    const handleStorage = (event) => {
      if (event.key !== 'visioncourt-control') return;
      const control = JSON.parse(event.newValue || '{}');
      if (control.type === 'GAME_CONTROL') {
        if (control.payload.action === 'start') {
          setIsMainClockRunning(true);
          setIsShotClockRunning(true);
        }
        if (control.payload.action === 'pause') {
          setIsMainClockRunning(false);
          setIsShotClockRunning(false);
        }
      }
      if (control.type === 'SHOT_CLOCK_CONTROL') {
        if (control.payload.action === 'reset') {
          setShotClock(SHOT_CLOCK_RESET);
          setIsShotClockRunning(true);
        }
      }
      if (control.type === 'FOUL_CONTROL') {
        setFouls(f => ({
          teamA: f.teamA + (control.payload.team === 'A'),
          teamB: f.teamB + (control.payload.team === 'B')
        }));
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  // 파울/period 상태 저장
  useEffect(() => {
    localStorage.setItem('visioncourt-state', JSON.stringify({ fouls, period }));
  }, [fouls, period]);

  // 메인 클락 카운트다운
  useEffect(() => {
    if (isMainClockRunning) {
      mainClockTimer.current = setInterval(() => {
        setGameTime(t => Math.max(0, t - 1));
      }, 1000);
    } else {
      clearInterval(mainClockTimer.current);
    }
    return () => clearInterval(mainClockTimer.current);
  }, [isMainClockRunning]);

  // 샷 클락 카운트다운
  useEffect(() => {
    if (isShotClockRunning) {
      shotClockTimer.current = setInterval(() => {
        setShotClock(s => Math.max(0, s - 1));
      }, 1000);
    } else {
      clearInterval(shotClockTimer.current);
    }
    return () => clearInterval(shotClockTimer.current);
  }, [isShotClockRunning]);

  // 샷 클락 경고 & 리셋
  useEffect(() => {
    if (shotClock === 0) {
      setShotClockWarning(true);
      setShotClock(SHOT_CLOCK_RESET);
    }
  }, [shotClock]);

  useEffect(() => {
    if (shotClockWarning) {
      const id = setTimeout(() => setShotClockWarning(false), 500);
      return () => clearTimeout(id);
    }
  }, [shotClockWarning]);

  return (
    <div style={{ height: '95vh', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Scoreboard
        scores={scores}
        fouls={fouls}
        gameTime={gameTime}
        shotClock={shotClock}
        period={period}
        shotClockWarning={shotClockWarning}
      />

      {videoUrl && (
        <video
          ref={videoRef}
          src={videoUrl}
          style={{ height: '40vh', width: 'auto', display: 'block', margin: '2rem auto 0 auto' }}
          controls
          muted
          onCanPlay={handleVideoCanPlay}
          onEnded={stopFrameProcessing}
        />
      )}

      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
}

export default ScoreboardPage;
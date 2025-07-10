// import React, { useRef, useState, useEffect } from 'react';

// const FPS = 30; // 초당 20프레임으로 설정

// function YoloVideoProcessor() {
//   // 상태 관리: UI에 표시될 텍스트들
//   const [status, setStatus] = useState('영상을 선택해주세요.');
//   const [yoloResult, setYoloResult] = useState('결과 대기 중...');
//   const [isProcessing, setIsProcessing] = useState(false);

//   // DOM 요소 및 데이터 참조
//   const socketRef = useRef(null);        // WebSocket 객체
//   const videoRef = useRef(null);         // <video> 태그 참조
//   const canvasRef = useRef(null);        // <canvas> 태그 참조
//   const intervalRef = useRef(null);      // 프레임 전송 타이머
//   const frameCountRef = useRef(0);       // 전송된 프레임 수

//   // 1. WebSocket 연결 및 메시지 핸들러 설정
//   useEffect(() => {
//     // WebSocket 연결
//     socketRef.current = new WebSocket("ws://13.125.244.130:8000/ws/yolo/");

//     // 연결 성공 시
//     socketRef.current.onopen = () => {
//       console.log("✅ WebSocket 연결 성공");
//       setStatus('WebSocket 연결 성공. 영상을 선택해주세요.');
//     };

//     // 📩 서버로부터 메시지 수신 시 (YoloUploader의 로직 통합)
//     socketRef.current.onmessage = (event) => {
//       try {
//         const data = JSON.parse(event.data);
//         console.log("📩 서버로부터 결과 수신:", data);
        
//         const countByClass = {};
//         // 서버가 보낸 events 배열을 순회하며 class별 개수 카운트
//         (data.events || []).forEach(d => {
//           const cls = d.class;
//           countByClass[cls] = (countByClass[cls] || 0) + 1;
//         });

//         // 화면에 표시할 텍스트 생성
//         const display = Object.entries(countByClass)
//           .map(([cls, count]) => `- class ${cls}: ${count}개`)
//           .join("\n");

//         setYoloResult(display || "감지된 객체 없음");
//       } catch (error) {
//         console.error("수신 데이터 처리 오류:", error);
//         setYoloResult("수신된 결과가 올바른 형식이 아닙니다.");
//       }
//     };

//     // 에러 발생 시
//     socketRef.current.onerror = (err) => {
//       console.error("❌ WebSocket 오류:", err);
//       setStatus("WebSocket 연결 오류 발생");
//     };
    
//     // 연결 종료 시
//     socketRef.current.onclose = () => {
//       console.warn("🔌 WebSocket 연결 종료");
//       setStatus("WebSocket 연결이 종료되었습니다.");
//     };

//     // 컴포넌트가 사라질 때 정리 함수
//     return () => {
//       if (intervalRef.current) clearInterval(intervalRef.current);
//       if (socketRef.current) socketRef.current.close();
//     };
//   }, []);

//   // 2. 파일 선택 시 실행되는 함수
//   const handleFileChange = (e) => {
//     const file = e.target.files[0];
//     if (!file || isProcessing) return;
    
//     console.log(`1️⃣ 파일 선택됨: ${file.name}`);
//     const videoUrl = URL.createObjectURL(file);
//     videoRef.current.src = videoUrl;
    
//     setStatus('영상 로드 중...');
//     setYoloResult('결과 대기 중...'); // 결과 초기화
//     setIsProcessing(true);
//     frameCountRef.current = 0;
//   };

//   // 3. 비디오가 재생 준비되면 프레임 추출 시작
//   const startFrameProcessing = () => {
//     const video = videoRef.current;
//     const canvas = canvasRef.current;
//     if (!video || !canvas) return;

//     console.log("3️⃣ 영상 재생 준비 완료. 프레임 추출을 시작합니다.");
//     setStatus('프레임 추출 및 전송 시작...');
    
//     canvas.width = video.videoWidth;
//     canvas.height = video.videoHeight;
//     video.play();

//     intervalRef.current = setInterval(() => {
//       if (video.paused || video.ended) return;

//       const frameLabel = `Frame #${++frameCountRef.current}`;
//       console.time(frameLabel);
      
//       const context = canvas.getContext('2d');
//       context.drawImage(video, 0, 0, canvas.width, canvas.height);

//       // 🖼️ 프레임을 base64 데이터로 변환
//       const dataURL = canvas.toDataURL('image/jpeg', 0.8);

//       // 🚀 서버가 기대하는 JSON 형식으로 감싸서 전송
//       if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
//         socketRef.current.send(JSON.stringify({ image: dataURL }));
//       }
      
//       console.timeEnd(frameLabel);
//     }, 1000 / FPS);
//   };

//   // 4. 비디오 재생이 끝나면 처리 종료
//   const stopFrameProcessing = () => {
//     console.log(`✅ 영상 처리 완료! 총 ${frameCountRef.current}개의 프레임이 전송되었습니다.`);
//     setStatus('영상 전송 완료! 결과 확인 중...');
//     clearInterval(intervalRef.current);
//     setIsProcessing(false);
//   };

//   return (
//     <div style={{ maxWidth: 600, margin: '2rem auto', padding: 20, background: '#f9f9f9', borderRadius: 12, boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>
//       <h2>VISION COURT</h2>
//       <p>아래에 경기 영상을 업로드하면 분석이 시작됩니다.</p>
      
//       <input 
//         type="file" 
//         accept="video/*" 
//         onChange={handleFileChange} 
//         disabled={isProcessing} 
//       />
      
//       <div style={{ margin: '1rem 0', fontWeight: 'bold', color: '#007bff' }}>상태: {status}</div>

//       <video 
//         ref={videoRef} 
//         width="100%" 
//         controls 
//         muted
//         onCanPlay={startFrameProcessing}
//         onEnded={stopFrameProcessing}
//       />

//       <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>

//       {/* <h3>📊 감지 결과:</h3>
//       <pre style={{ background: '#e9ecef', padding: '1rem', borderRadius: '5px' }}>
//         {yoloResult}
//       </pre> */}
//     </div>
//   );
// }

// export default YoloVideoProcessor;

import React from 'react';
import { useNavigate } from 'react-router-dom';

function VideoUploadPage() {
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const videoUrl = URL.createObjectURL(file);
    localStorage.setItem('uploadedVideoUrl', videoUrl); // 임시 저장

    // 서버 업로드 로직 생략 (나중에 구현 예정)
    console.log("🎥 영상 선택 완료:", file.name);

    // 업로드 후 scoreboard 페이지로 이동
    navigate('/scoreboard');
  };

  return (
    <div>
      <h2>영상 업로드</h2>
      <input type="file" accept="video/*" onChange={handleFileChange} />
    </div>
  );
}

export default VideoUploadPage;
// WebSocket 연결
let socket;
try {
  socket = new WebSocket("ws://localhost:8000/ws"); // 서버 주소에 맞게 수정
  document.getElementById("websocket").textContent = "WebSocket 연결을 시도합니다...";
} catch (error) {
  console.error("WebSocket 연결 실패:", error);
  document.getElementById("message").textContent = "서버 연결에 실패했습니다";
}

// 웹캠 영상 요소
const video = document.getElementById('video');

// 비디오 프레임 캡처용 캔버스
const canvas = document.getElementById('canvas');
const context = canvas.getContext("2d");

// WebRTC를 사용해 카메라 접근
navigator.mediaDevices.getUserMedia({ video: true, audio: false })
  .then(stream => {
    video.srcObject = stream;
  })
  .catch(err => {
    console.error("카메라 접근 실패:", err);
  });

// 전송 상태 관리 변수
let isSending = false;

// 시작 버튼과 종료 버튼
const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");

// 버튼 클릭 이벤트 핸들러
startButton.addEventListener("click", () => {
  isSending = true;
  document.getElementById("message").textContent = "이미지 전송 중"; // 메시지 업데이트
});

stopButton.addEventListener("click", () => {
  isSending = false;
  document.getElementById("message").textContent = "이미지 전송 대기"; // 메시지 업데이트
});

// WebSocket이 열리면 이미지 전송 제어
socket.addEventListener("open", () => {
  console.log("WebSocket 연결 성공");

  setInterval(() => {
    if (isSending) {
      // 현재 비디오 프레임을 캔버스로 캡처
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageDataURL = canvas.toDataURL("image/jpeg"); // base64로 변환

      // WebSocket으로 JSON 형식으로 전송
      socket.send(JSON.stringify({ image: imageDataURL }));
    }
  }, 100); // 0.1초마다 전송 => 10 FPS
});

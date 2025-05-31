// WebSocket 연결
let socket;
try {
  socket = new WebSocket("ws://localhost:8000/ws"); // 서버 주소에 맞게 수정
  document.getElementById("websocket").textContent = "WebSocket 연결을 시도합니다...";
} catch (error) {
  console.error("WebSocket 연결 실패:", error);
  document.getElementById("message").textContent = "서버 연결에 실패했습니다";
}

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const context = canvas.getContext("2d");

let isSending = false;
let videoStream = null;
let uploadVideo = false;

const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");

startButton.addEventListener("click", () => {
  video.play();
  isSending = true;
  document.getElementById("message").textContent = "이미지 전송 중";
});

stopButton.addEventListener("click", () => {
  video.pause();
  isSending = false;
  document.getElementById("message").textContent = "이미지 전송 대기";
});

// 업로드한 파일 재생
document.getElementById("uploadButton").addEventListener("click", () => {
  const fileInput = document.getElementById("upload");
  const file = fileInput.files[0];
  if (file) {
    uploadVideo = true;
    const url = URL.createObjectURL(file);
    video.srcObject = null; // 웹캠 stream 제거
    video.src = url;
    // video.play(); // 자동재생 막기
  }
});

// 웹캠 연결
navigator.mediaDevices.getUserMedia({ video: true, audio: false })
  .then(stream => {
    videoStream = stream;
    video.srcObject = stream;
  })
  .catch(err => {
    console.error("카메라 접근 실패:", err);
  });

// 영상 메타데이터 로드 후 캔버스 사이즈 설정
video.addEventListener("loadedmetadata", () => {
  if (uploadVideo) {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
  } else {
    canvas.width = 480;
    canvas.height = 360;
  }
});

// WebSocket 연결 후 프레임 전송
socket.addEventListener("open", () => {
  document.getElementById("websocket").textContent = "WebSocket 연결 성공";

  setInterval(() => {
    if (isSending) {
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageDataURL = canvas.toDataURL("image/jpeg");
      socket.send(JSON.stringify({ image: imageDataURL }));
    }
  }, 100); // 100ms 간격
});

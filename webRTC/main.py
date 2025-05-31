from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from kafka import KafkaProducer
from PIL import Image
import base64
import io
import json
from datetime import datetime
import uuid

app = FastAPI()

""" producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
) """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # JSON 데이터 파싱
            message = json.loads(data)
            img_base64 = message["image"].split(",")[1]  # base64 부분 추출

            # base64 데이터를 .txt 파일로 저장
            u = uuid.uuid4()
            """ with open(f"{u}_base64.txt", "w") as txt_file:
                txt_file.write(img_base64) """

            img_bytes = base64.b64decode(img_base64)
            image = Image.open(io.BytesIO(img_bytes))
            width, height = image.size

            # uuid를 사용하여 고유한 이미지 파일명 생성
            unique_filename = f"{u}.png"
            # image.save(unique_filename)

            # TODO: image → 모델에 전달 및 결과 처리
            print(f"[{datetime.now()}] 이미지 수신 및 저장 완료")
            
    except WebSocketDisconnect:
        print("클라이언트 연결 종료")
    except Exception as e:
        print(f"알 수 없는 오류 발생: {e}")

# uvicorn main:app --reload --host 0.0.0.0 --port 8000
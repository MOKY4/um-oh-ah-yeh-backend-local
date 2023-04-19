from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import cross_origin
from dotenv import load_dotenv

load_dotenv()

import openai
import uuid
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY")

socketio = SocketIO(app, cors_allowed_origins="*", debug=True)

DEFAULT_PROMPT = "You are a kind helpful assistant that helps to write some texts. You will ask the user to answer 1. choose role between student and office worker, 2. who the user try to send the text, 3.specific context or essential information to write the text in a given order after user answers to each question."


@app.route("/")
@cross_origin()
def index():
    return render_template("index.html")


@socketio.on("connect")
def connect():
    # 방 이름을 UUID로 지정
    room_name = str(uuid.uuid4())
    emit("enter_room", room_name)
    # 프라이빗 룸 입장
    join_room(room_name)
    # 메시지 리스트 생성
    session.setdefault("room_name", room_name)
    session.setdefault("messages", []).append({"role": "system", "content": DEFAULT_PROMPT})


@socketio.on("disconnect")
def disconnect():
    # 프라이빗 룸에서 나감
    room_name = session.get("room_name", "default")
    leave_room(room_name)


@socketio.on("chat")
def chat(message, room_name):
    # API KEY 세팅
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # 메시지 입력받아서 chatgpt에게 요청
    messages = session.get("messages", [])
    messages.append({
        "role": "user",
        "content": message
    })
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages)
    # chatgpt 응답
    response = completion.choices[0].message.content
    # 단일(프라이빗 룸) 클라이언트에게 응답
    emit("chat", {"message": response}, room=room_name)
    # 응답을 리스트에 저장
    messages.append({"role": "assistant", "content": response})


if __name__ == '__main__':
    socketio.run(app)

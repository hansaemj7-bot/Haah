import streamlit as st
import json
import os
from google import genai
from google.genai import types


MODEL_NAME = "gemini-2.5-flash"


DATA_DIR = "story_data"
CHATS_DIR = os.path.join(DATA_DIR, "chats")
STATES_DIR = os.path.join(DATA_DIR, "states")


os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHATS_DIR, exist_ok=True)
os.makedirs(STATES_DIR, exist_ok=True)


CHARACTERS_FILE = os.path.join(DATA_DIR, "characters.json")
WORLDS_FILE = os.path.join(DATA_DIR, "worlds.json")


def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


default_worlds = {
    "판타지 아카데미": "마법과 기계공학이 융합된 왕립 아카데미. 결계에 정체불명의 균열이 생기고 있다.",
    "사이버펑크 2180": "거대 기업이 통제하는 네온 거리. 인간과 기계의 경계가 무너진 어두운 디스토피아."
}


default_chars = {
    "엘레나": {
        "world": "판타지 아카데미",
        "description": "아카데미 수석 마법학도. 냉철하고 분석적인 성격이지만 호기심이 많다. 정중한 존댓말을 쓴다.",
        "first_message": "기다리고 있었습니다. 결계 균열 조사 준비는 끝나셨습니까?"
    },
    "하이드": {
        "world": "사이버펑크 2180",
        "description": "뒷골목 정보 브로커. 능글맞고 잇속에 밝으며 거친 반말을 쓴다. 쓸모 있는 정보와 돈을 밝힌다.",
        "first_message": "여, 왔어? 네오코프 감시 드론이 방금 지나갔으니 조용히 말해."
    }
}


worlds = load_json(WORLDS_FILE, default_worlds)
characters = load_json(CHARACTERS_FILE, default_chars)


def update_dynamic_state(client, char_name, current_state, user_msg, ai_reply):
    prompt = f"""
캐릭터 롤플레잉 게임의 상태 기록관입니다.
최근 대화를 바탕으로 상태(JSON)를 갱신하세요.


[현재 상태]
{json.dumps(current_state, ensure_ascii=False)}


[최근 대화]
유저: {user_msg}
캐릭터: {ai_reply}


반드시 마크다운 없이 순수 JSON 형식으로만 답하세요:
{{
  "current_location": "현재 위치",
  "relationship": "유저와의 현재 관계 및 호감도",
  "inventory": ["소지품 및 단서 목록"],
  "memories": ["기억해야 할 사건 및 약속 목록"]
}}
"""
    try:
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return json.loads(res.text)
    except Exception:
        return current_state


st.set_page_config(page_title="AI 스토리 룸", page_icon="⚡", layout="wide")


with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AI Studio 키 입력")


    st.markdown("---")
    st.header("세계관 및 캐릭터 등록")


    with st.expander("새 세계관 등록"):
        w_name = st.text_input("세계관 이름")
        w_desc = st.text_area("세계관 설명")
        if st.button("세계관 저장"):
            if w_name and w_desc:
                worlds[w_name] = w_desc
                save_json(WORLDS_FILE, worlds)
                st.success("저장 완료")
                st.rerun()


    with st.expander("새 캐릭터 등록"):
        c_name = st.text_input("캐릭터 이름")
        c_world = st.selectbox("소속 세계관", options=list(worlds.keys()))
        c_desc = st.text_area("성격 및 특징")
        c_intro = st.text_area("첫 대사")
        if st.button("캐릭터 저장"):
            if c_name and c_desc:
                characters[c_name] = {
                    "world": c_world,
                    "description": c_desc,
                    "first_message": c_intro or "반갑습니다."
                }
                save_json(CHARACTERS_FILE, characters)
                st.success("저장 완료")
                st.rerun()


    st.markdown("---")
    selected_char = st.selectbox("대화할 캐릭터", options=list(characters.keys()))


if not selected_char:
    st.info("캐릭터를 선택해주세요.")
    st.stop()


char_data = characters[selected_char]
world_name = char_data.get("world", "미지정")
world_desc = worlds.get(world_name, "설정 없음")


chat_file = os.path.join(CHATS_DIR, f"{selected_char}.json")
state_file = os.path.join(STATES_DIR, f"{selected_char}_state.json")


init_state = {
    "current_location": "시작 지점",
    "relationship": "첫 만남",
    "inventory": [],
    "memories": ["대화가 시작되었습니다."]
}


messages = load_json(chat_file, [
    {"role": "assistant", "content": char_data.get("first_message", "반갑습니다.")}
])
live_state = load_json(state_file, init_state)


col_chat, col_state = st.columns([7, 3])


with col_state:
    st.subheader("실시간 저장 메모리")
    st.markdown(f"**위치:** `{live_state.get('current_location', '알 수 없음')}`")
    st.markdown(f"**관계:** {live_state.get('relationship', '미정')}")
    
    st.markdown("**소지품 / 단서:**")
    items = live_state.get("inventory", [])
    if items:
        for it in items:
            st.markdown(f"- {it}")
    else:
        st.markdown("*없음*")


    st.markdown("**기억된 사건:**")
    mems = live_state.get("memories", [])
    for m in mems:
        st.markdown(f"- {m}")


    st.markdown("---")
    if st.button("대화 기록 초기화"):
        messages = [{"role": "assistant", "content": char_data.get("first_message", "반갑습니다.")}]
        live_state = init_state
        save_json(chat_file, messages)
        save_json(state_file, live_state)
        st.rerun()


with col_chat:
    st.title(f"{selected_char}")
    st.caption(f"세계관: {world_name} — {world_desc}")


    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


    if prompt := st.chat_input("행동이나 대사를 입력하세요..."):
        if not api_key:
            st.error("사이드바에 Gemini API 키를 먼저 입력해주세요.")
            st.stop()


        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)


        client = genai.Client(api_key=api_key)


        system_instruction = f"""
당신은 캐릭터 '{selected_char}'입니다.
세계관과 실시간 상태를 엄격히 지켜 롤플레잉하세요.


[세계관]
{world_desc}


[캐릭터 설정]
{char_data['description']}


[현재 실시간 상태]
위치: {live_state.get('current_location')}
관계: {live_state.get('relationship')}
소지품: {', '.join(live_state.get('inventory', []))}
기억: {'; '.join(live_state.get('memories', []))}


[규칙]
1. AI 모델임을 밝히지 말고 캐릭터 1인칭으로만 대답하세요.
2. 지문(*행동 및 표정*)과 대사를 섞어 대답하세요.
3. 과거의 사건과 관계를 일관성 있게 기억하세요.
"""


        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=m["content"])]
            ))


        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.8
                    )
                )
                reply = response.text
                st.markdown(reply)


        messages.append({"role": "assistant", "content": reply})
        save_json(chat_file, messages)


        with st.spinner("상태 갱신 중..."):
            updated = update_dynamic_state(
                client=client,
                char_name=selected_char,
                current_state=live_state,
                user_msg=prompt,
                ai_reply=reply
            )
            save_json(state_file, updated)


        st.rerun()
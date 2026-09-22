import streamlit as st
from io import BytesIO

from stamp_generator import generate_seal

st.set_page_config(
    page_title="도장(직인) 생성기",
    page_icon="🔖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 860px; }
    .stButton > button { border-radius: 12px; font-weight: bold; }
    .stTextInput > div > input { border-radius: 10px; }
    h1 { font-size: 1.6rem !important; }
    [data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.page_link("app.py", label="블로그 글 생성기로 이동", icon="✍️")

st.markdown("## 🔖 도장(직인) 생성기")
st.caption("업체명을 입력하면 투명 배경 PNG 도장 이미지를 만들어 드립니다 · 전자문서에 바로 붙여 쓸 수 있습니다")

st.divider()

col_name, col_shape = st.columns([2, 1])
with col_name:
    name = st.text_input("🏢 업체명 / 이름", value="극동전기", placeholder="예) 극동전기")
with col_shape:
    shape_label = st.radio("모양", ["원형", "사각형"], horizontal=True)
shape = "round" if shape_label == "원형" else "square"

gen_btn = st.button("🖋  도장 생성하기", type="primary", use_container_width=True)

if gen_btn or "stamp_img" not in st.session_state:
    clean_name = name.strip()
    if clean_name:
        img = generate_seal(clean_name, shape=shape, size=700)
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.session_state["stamp_img"] = buf.getvalue()
        st.session_state["stamp_name"] = clean_name
        st.session_state["stamp_shape"] = shape_label
    elif gen_btn:
        st.warning("업체명을 입력해주세요.")

if "stamp_img" in st.session_state:
    st.divider()
    preview_col, _ = st.columns([1, 1])
    with preview_col:
        st.image(
            st.session_state["stamp_img"],
            caption=f"{st.session_state['stamp_name']} ({st.session_state['stamp_shape']})",
        )
    st.download_button(
        "💾  PNG 다운로드",
        data=st.session_state["stamp_img"],
        file_name=f"{st.session_state['stamp_name']}_도장.png",
        mime="image/png",
        use_container_width=True,
    )

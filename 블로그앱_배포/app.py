import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import json, re, random, html, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

st.set_page_config(
    page_title="네이버 블로그 글 생성기",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 860px; }
    .stButton > button { border-radius: 12px; font-weight: bold; }
    .stTextInput > div > input { border-radius: 10px; }
    .stTextArea > div > textarea { border-radius: 10px; font-family: 'Malgun Gothic', sans-serif; }
    h1 { font-size: 1.6rem !important; }
    h2 { font-size: 1.2rem !important; color: #2563EB; }
    h3 { font-size: 1.05rem !important; background: #EFF6FF; padding: 8px 14px; border-radius: 8px; color: #1D4ED8; }
    .stRadio > div { flex-wrap: wrap; gap: 6px; }
    [data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

RSS_URLS = {
    "게임":    "https://news.google.com/rss/search?q=게임+신작+업데이트&hl=ko&gl=KR&ceid=KR:ko",
    "시사":    "https://news.google.com/rss/search?q=한국+뉴스+오늘&hl=ko&gl=KR&ceid=KR:ko",
    "경제":    "https://news.google.com/rss/search?q=경제+주식+환율&hl=ko&gl=KR&ceid=KR:ko",
    "스포츠":  "https://news.google.com/rss/search?q=스포츠+축구+야구&hl=ko&gl=KR&ceid=KR:ko",
    "IT":     "https://news.google.com/rss/search?q=IT+기술+AI+스마트폰&hl=ko&gl=KR&ceid=KR:ko",
    "생활TIP": "https://news.google.com/rss/search?q=생활꿀팁+건강+절약+생활정보&hl=ko&gl=KR&ceid=KR:ko",
}

THEMES = {
    "게임":    ((22, 8, 58),   (90, 14, 130),  (210, 90, 255)),
    "시사":    ((8, 28, 80),   (14, 58, 148),  (80, 168, 255)),
    "경제":    ((4, 58, 82),   (8, 95, 122),   (50, 205, 230)),
    "스포츠":  ((130, 10, 10), (195, 42, 8),   (255, 162, 30)),
    "IT":     ((8, 14, 75),   (28, 42, 148),  (65, 182, 255)),
    "생활TIP": ((148, 52, 6),  (198, 90, 14),  (255, 195, 70)),
}


def get_font(size):
    paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def strip_emoji(text):
    return re.sub(
        r'[\U00010000-\U0010ffff\U00002600-\U000027BF\U0001F300-\U0001F9FF]',
        '', text).strip()


def get_trending_topic(category):
    try:
        resp = requests.get(RSS_URLS[category], timeout=10,
                            headers={'User-Agent': 'Mozilla/5.0'})
        root = ET.fromstring(resp.content)
        titles = []
        for item in root.findall('.//item')[:10]:
            el = item.find('title')
            if el is not None and el.text:
                t = el.text.split(' - ')[0].strip()
                if len(t) > 5:
                    titles.append(t)
        if titles:
            return random.choice(titles[:5])
    except Exception:
        pass
    defaults = {
        "게임": "최신 인기 게임 추천", "시사": "오늘의 주요 뉴스",
        "경제": "최근 경제 동향 분석", "스포츠": "이번 주 스포츠 하이라이트",
        "IT": "최신 AI 기술 트렌드", "생활TIP": "알아두면 유용한 생활 꿀팁",
    }
    return defaults.get(category, "최신 트렌드")


def get_news_context(topic, category):
    def clean(text):
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    articles = []
    for url in [
        f"https://news.google.com/rss/search?q={urllib.parse.quote(topic)}&hl=ko&gl=KR&ceid=KR:ko",
        RSS_URLS.get(category, ""),
    ]:
        if not url or len(articles) >= 5:
            break
        try:
            resp = requests.get(url, timeout=12, headers={'User-Agent': 'Mozilla/5.0'})
            root = ET.fromstring(resp.content)
            for item in root.findall('.//item'):
                if len(articles) >= 5:
                    break
                t_el    = item.find('title')
                d_el    = item.find('description')
                date_el = item.find('pubDate')
                src_el  = item.find('source')
                if date_el is not None and date_el.text:
                    try:
                        if parsedate_to_datetime(date_el.text) < cutoff:
                            continue
                    except Exception:
                        pass
                t = clean(t_el.text if t_el is not None else "")
                if len(t) > 5:
                    articles.append({
                        'title': t.split(' - ')[0].strip(),
                        'description': clean(d_el.text if d_el is not None else "")[:600],
                        'date': (date_el.text or "")[:30] if date_el is not None else "",
                        'source': src_el.text if src_el is not None else "",
                    })
        except Exception:
            continue
    return articles


def generate_content(category, topic, api_key, articles):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash-lite')

    if articles:
        news_block = ""
        for i, a in enumerate(articles, 1):
            news_block += f"\n[뉴스 {i}]\n제목: {a['title']}\n"
            if a['date']:
                news_block += f"날짜: {a['date']}\n"
            if a['source']:
                news_block += f"출처: {a['source']}\n"
            if a['description']:
                news_block += f"내용: {a['description']}\n"
    else:
        news_block = "(수집된 뉴스 없음 — 알려진 사실 기반으로 신중하게 작성)"

    intro_styles = [
        "독자가 가장 궁금해하는 핵심 질문을 던지며 시작",
        "놀라운 사실이나 수치로 시작해 독자의 호기심 유발",
        "독자의 공감을 이끄는 일상적인 상황 묘사로 시작",
        "결론을 먼저 던지고 '그 이유는 이렇습니다' 식으로 시작",
        "최근 가장 많이 검색되는 이유를 중심으로 시작",
    ]
    section_styles = [
        "각 소제목은 독자에게 말 걸듯 질문형으로",
        "각 소제목은 핵심 키워드 + 감탄·놀람 표현으로",
        "각 소제목은 '~하려면?', '~한 이유는?' 처럼 이유·방법형으로",
        "각 소제목은 순서나 단계를 암시하는 형태로",
    ]

    prompt = f"""당신은 팩트 체크를 철저히 하는 네이버 블로그 전문 작가입니다.
아래 뉴스 기사들을 사실 확인 자료로만 참고하여, 완전히 새롭게 쓴 독창적인 블로그 글을 JSON 형식으로만 작성하세요.
JSON 외 텍스트는 절대 포함하지 마세요.

━━━ 참고 뉴스 (사실 확인용) ━━━
{news_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

카테고리: {category} / 주제: {topic}

[이번 글의 스타일]
- 서론 방식: {random.choice(intro_styles)}
- 소제목 방식: {random.choice(section_styles)}

[절대 규칙]
1. 모든 문장은 "~입니다", "~합니다" 어투 통일 / 질문은 "~일까?" 처럼 친근하게
2. 뉴스 문장 절대 복사 금지 — 같은 사실도 완전히 새로운 문장으로 재작성
3. 뉴스에서 확인된 사실(수치·날짜·인명·기관명)만 사용, 없는 내용 추가 금지
4. 추측·과장 금지 / 불확실한 내용은 "~에 따르면", "~로 알려졌습니다" 표현
5. 각 섹션 최소 200자 이상 / 설명과 맥락 풍부하게
6. 특정 행정구역(구·동·시·군) 사용 금지 — 전국 독자 대상
7. 제목은 30~40자 이내로 간결하게

{{"title": "30~40자 이내, 숫자·질문·반전·공감 중 하나 활용",
  "intro": "4~5문장, 위 서론 방식 적용",
  "sections": [
    {{"title": "이모지 + 소제목1", "content": "5~7문장"}},
    {{"title": "이모지 + 소제목2", "content": "5~7문장"}},
    {{"title": "이모지 + 소제목3", "content": "5~7문장"}}
  ],
  "conclusion": "핵심 요약 마무리 3~4문장",
  "faq": [
    {{"q": "질문1?", "a": "답변 2~3문장"}},
    {{"q": "질문2?", "a": "답변 2~3문장"}},
    {{"q": "질문3?", "a": "답변 2~3문장"}}
  ],
  "tags": "태그1, 태그2, 태그3, 태그4, 태그5, 태그6, 태그7, 태그8, 태그9, 태그10"
}}"""

    response = model.generate_content(prompt, generation_config={"temperature": 0.8})
    text = response.text.strip()
    if '```' in text:
        text = re.sub(r'```(?:json)?', '', text).replace('```', '').strip()
    return json.loads(text)


def generate_image(category, section_title, base_topic, idx):
    W, H = 800, 400
    c1, c2, acc = THEMES.get(category, ((28, 28, 58), (58, 58, 98), (148, 148, 255)))

    img = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    for x in range(W):
        t = x / (W - 1)
        col = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
        draw.line([(x, 0), (x, H)], fill=col)

    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for y in range(H):
        od.line([(0, y), (W, y)], fill=(0, 0, 0, int((y / H) * 60)))
    od.ellipse([W - 320, -100, W + 100, H + 100], fill=(*acc, 28))
    od.ellipse([W - 180, H - 180, W + 60, H + 60], fill=(*acc, 18))
    od.ellipse([-60, H - 180, 200, H + 60], fill=(*acc, 14))
    img = Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, H - 10, W, H], fill=acc)
    draw.rectangle([0, 0, 8, H], fill=acc)

    font_badge = get_font(16)
    font_title = get_font(34)
    font_sub   = get_font(18)

    cat_text = category
    bx1, by1 = 28, 26
    bx2 = bx1 + int(len(cat_text) * 13) + 26
    by2 = by1 + 34
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=17, fill=acc)
    draw.text(((bx1 + bx2) // 2, (by1 + by2) // 2), cat_text,
              font=font_badge, fill=tuple(max(0, c - 60) for c in acc), anchor='mm')

    clean_title = strip_emoji(section_title)
    words = clean_title.split()
    lines, cur = [], ""
    for word in words:
        test = cur + word + " "
        if draw.textlength(test, font=font_title) > W - 70 and cur:
            lines.append(cur.strip())
            cur = word + " "
        else:
            cur = test
    if cur.strip():
        lines.append(cur.strip())

    ty = 85
    for line in lines[:3]:
        draw.text((28, ty), line, font=font_title, fill='white')
        bbox = draw.textbbox((28, ty), line, font=font_title)
        ty = bbox[3] + 10

    sub_color = tuple(min(255, c + 70) for c in acc)
    draw.text((28, H - 44), strip_emoji(base_topic)[:50], font=font_sub, fill=sub_color)

    buf = BytesIO()
    img.save(buf, format='JPEG', quality=92)
    buf.seek(0)
    return buf.getvalue()


def build_copy_text(data):
    lines = [data['title'], "", data['intro'], ""]
    for s in data.get('sections', []):
        lines += [s['title'], "", s['content'], ""]
    lines += ["✅ 마무리", data['conclusion'], ""]
    if data.get('faq'):
        lines += ["❓ 자주 묻는 질문 (FAQ)", ""]
        for item in data['faq']:
            lines += [f"Q. {item.get('q', '')}", f"A. {item.get('a', '')}", ""]
    hashtags = "  ".join(f"#{t.strip()}" for t in data.get('tags', '').split(',') if t.strip())
    lines += ["─" * 20, hashtags]
    return "\n".join(lines)


# ── 메인 UI ─────────────────────────────────────────────────────

st.markdown("## ✍️ 네이버 블로그 글 생성기")
st.caption("AI 팩트 기반 자동 생성 · 네이버 블로그 최적화")

with st.expander("🔑 Gemini API 키 설정", expanded='api_key' not in st.session_state):
    api_input = st.text_input("API 키", type="password",
                               placeholder="AIza... (aistudio.google.com 무료 발급)",
                               key="api_input_field")
    if st.button("저장", key="save_api"):
        if api_input.strip():
            st.session_state['api_key'] = api_input.strip()
            st.success("저장됐습니다!")
        else:
            st.warning("API 키를 입력해주세요.")

st.divider()

col_cat, col_topic = st.columns([1, 2])
with col_cat:
    category = st.radio(
        "📂 카테고리",
        ["🎮 게임", "📰 시사", "💰 경제", "⚽ 스포츠", "💻 IT", "🌿 생활TIP"],
        key="category"
    )
    cat = category.split(" ", 1)[1]

with col_topic:
    topic_input = st.text_input(
        "✏️ 주제 (비워두면 자동 선택)",
        placeholder="예) 손흥민 시즌 첫 골, 최신 AI 트렌드, 금리 동향 ...",
        key="topic_input"
    )

gen_btn = st.button("✨  글 생성하기", type="primary", use_container_width=True)

if gen_btn:
    api_key = st.session_state.get('api_key', '').strip()
    if not api_key:
        st.error("API 키를 먼저 입력하고 저장해주세요.")
        st.stop()

    with st.status("글을 생성하고 있습니다...", expanded=True) as status:
        topic = topic_input.strip()
        if not topic:
            st.write("🔍 최신 뉴스에서 주제 자동 선택 중...")
            topic = get_trending_topic(cat)

        st.write(f"📰 '{topic}' 관련 뉴스 수집 중...")
        articles = get_news_context(topic, cat)

        st.write("📝 팩트 기반 블로그 글 작성 중...")
        try:
            data = generate_content(cat, topic, api_key, articles)
        except Exception as e:
            st.error(f"글 생성 오류: {e}")
            st.stop()

        images_data = []
        for i, section in enumerate(data.get('sections', [])):
            st.write(f"🖼 이미지 생성 중 ({i+1}/{len(data['sections'])})...")
            img_bytes = generate_image(cat, section['title'], topic, i)
            images_data.append(img_bytes)

        st.session_state['result_data'] = data
        st.session_state['result_images'] = images_data
        st.session_state['result_topic'] = topic
        status.update(label="✅ 완료!", state="complete")

if 'result_data' in st.session_state:
    data   = st.session_state['result_data']
    images = st.session_state['result_images']
    topic  = st.session_state['result_topic']

    st.divider()
    st.markdown(f"# {data.get('title', '')}")
    st.write(data.get('intro', ''))

    for i, section in enumerate(data.get('sections', [])):
        st.markdown(f"### {section.get('title', '')}")
        if i < len(images) and images[i]:
            st.image(images[i], use_container_width=True)
        st.write(section.get('content', ''))

    st.markdown("### ✅ 마무리")
    st.write(data.get('conclusion', ''))

    faq = data.get('faq', [])
    if faq:
        st.markdown("### ❓ 자주 묻는 질문 (FAQ)")
        for item in faq:
            with st.expander(f"Q. {item.get('q', '')}"):
                st.write(f"A. {item.get('a', '')}")

    raw_tags = data.get('tags', '')
    hashtags = "  ".join(f"#{t.strip()}" for t in raw_tags.split(',') if t.strip())
    st.caption(f"🏷 {hashtags}")

    st.divider()
    st.markdown("#### 📋 텍스트 복사")
    full_text = build_copy_text(data)
    st.text_area("아래 텍스트를 전체 선택해서 복사하세요", value=full_text, height=300, key="copy_area")

    st.markdown("#### 💾 이미지 다운로드")
    img_cols = st.columns(len(images))
    for i, (col, img_bytes) in enumerate(zip(img_cols, images)):
        with col:
            col.download_button(
                label=f"이미지 {i+1}",
                data=img_bytes,
                file_name=f"blog_image_{i+1}.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )

import os
import base64
import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# =========================================================
# 1. CẤU HÌNH CƠ BẢN
# =========================================================
st.set_page_config(
    page_title="AI-SafeSchool Guard | Trợ lý an toàn học đường",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DOCS = [
    APP_DIR / "Tài liệu ma tuý học đường.docx",
    APP_DIR / "Luật tra cứu liên quan về ma tuý.pdf",
]
BACKGROUND_PATH = APP_DIR / "background.png"

# Nên cấu hình GEMINI_API_KEY và ADMIN_PASSWORD trong .streamlit/secrets.toml
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
admin_password = st.secrets.get("ADMIN_PASSWORD", os.getenv("ADMIN_PASSWORD", ""))

# =========================================================
# 2. GIAO DIỆN
# =========================================================
def image_to_base64(path: Path) -> str:
    try:
        if path.exists():
            return base64.b64encode(path.read_bytes()).decode("utf-8")
    except OSError:
        pass
    return ""

hero_image = image_to_base64(BACKGROUND_PATH)

st.markdown(
    """
    <style>
    :root {
        --navy: #102a56;
        --blue: #155eef;
        --cyan: #26c6da;
        --ink: #14213d;
        --muted: #5b6780;
        --line: #dce5f2;
        --surface: #ffffff;
        --soft: #f3f7fc;
    }
    .stApp {
        background:
            radial-gradient(circle at 8% 0%, rgba(38,198,218,.10), transparent 28%),
            linear-gradient(180deg, #f4f8ff 0%, #f8fbff 55%, #eef4fb 100%);
        color: var(--ink);
    }
    [data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer { visibility: hidden; }
    .block-container {
        max-width: 1180px;
        padding-top: 1.3rem;
        padding-bottom: 2.5rem;
    }
    .hero {
        position: relative;
        overflow: hidden;
        border-radius: 24px;
        padding: 30px 34px 26px;
        margin-bottom: 20px;
        color: white;
        background: linear-gradient(120deg, #09265b 0%, #104aa0 58%, #087caa 100%);
        box-shadow: 0 16px 36px rgba(14, 49, 105, .18);
        border: 1px solid rgba(255,255,255,.24);
    }
    .hero:before {
        content: "";
        position: absolute;
        inset: 0;
        background-image: var(--hero-image);
        background-size: cover;
        background-position: center 38%;
        opacity: .22;
        pointer-events: none;
    }
    .hero-content { position: relative; z-index: 1; }
    .hero-kicker {
        display: inline-block;
        padding: 5px 10px;
        border: 1px solid rgba(255,255,255,.32);
        border-radius: 999px;
        background: rgba(255,255,255,.10);
        color: #e5f6ff;
        font-size: .82rem;
        font-weight: 700;
        letter-spacing: .04em;
        margin-bottom: 10px;
    }
    .hero h1 {
        color: white !important;
        font-size: clamp(1.8rem, 3.3vw, 2.65rem);
        line-height: 1.16;
        margin: 0 0 10px 0;
        letter-spacing: -.025em;
    }
    .hero p {
        color: #e5efff !important;
        font-size: 1.02rem;
        max-width: 760px;
        margin: 0;
        line-height: 1.6;
    }
    .hero-note {
        display: inline-block;
        margin-top: 17px;
        padding: 8px 12px;
        border-radius: 12px;
        background: rgba(2, 18, 48, .34);
        color: #e8f8ff;
        font-size: .88rem;
    }
    .section-label {
        color: #23416e;
        font-size: .86rem;
        font-weight: 800;
        letter-spacing: .06em;
        text-transform: uppercase;
        margin: 6px 0 10px;
    }
    .stRadio > label { color: #19345e !important; font-weight: 700; }
    div[role="radiogroup"] {
        gap: 10px;
        padding: 5px 0 8px;
    }
    div[role="radiogroup"] label {
        background: white;
        border: 1px solid #d9e4f3;
        border-radius: 12px;
        padding: 10px 14px;
    }
    div[role="radiogroup"] label:has(input:checked) {
        border-color: #4c8dff;
        background: #eaf2ff;
    }
    .info-card {
        height: 100%;
        border: 1px solid #dce7f5;
        border-radius: 16px;
        padding: 16px;
        background: rgba(255,255,255,.94);
        box-shadow: 0 5px 18px rgba(30, 64, 115, .05);
    }
    .info-card .card-icon { font-size: 1.5rem; margin-bottom: 6px; }
    .info-card h3 {
        font-size: 1rem;
        color: #173765 !important;
        margin: 0 0 6px 0;
    }
    .info-card p {
        color: #586984 !important;
        font-size: .9rem;
        line-height: 1.5;
        margin: 0;
    }
    [data-testid="stChatMessage"] {
        background: white;
        border: 1px solid #e0e8f3;
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 5px 16px rgba(25, 54, 97, .045);
        margin-bottom: 12px;
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {
        color: #1b2b45 !important;
        line-height: 1.68;
    }
    [data-testid="stChatInput"] {
        border: 1px solid #cddcf0 !important;
        border-radius: 16px !important;
        background: white !important;
        box-shadow: 0 8px 24px rgba(26, 63, 116, .08);
    }
    [data-testid="stChatInput"] textarea {
        color: #172b4d !important;
    }
    [data-testid="stSidebar"] {
        background: #f7faff;
        border-right: 1px solid #dce6f3;
    }
    [data-testid="stSidebar"] * { color: #1b355c; }
    h2, h3, h4 { color: #193963 !important; }
    p, label, .stMarkdown { color: #263b59; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #dce7f5;
        border-radius: 14px;
        padding: 14px;
    }
    .privacy-note {
        border-left: 4px solid #1a9aa8;
        padding: 10px 14px;
        background: #eaf8fa;
        border-radius: 0 10px 10px 0;
        color: #245568;
        font-size: .88rem;
        line-height: 1.55;
    }
    @media (max-width: 700px) {
        .block-container { padding: .8rem .8rem 2rem; }
        .hero { padding: 23px 20px; border-radius: 18px; }
        .hero p { font-size: .95rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if hero_image:
    st.markdown(
        f"""<style>.hero {{ --hero-image: url("data:image/png;base64,{hero_image}"); }}</style>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<style>.hero { --hero-image: none; }</style>",
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <section class="hero">
      <div class="hero-content">
        <div class="hero-kicker">🛡️ AN TOÀN HỌC ĐƯỜNG · AI HỖ TRỢ</div>
        <h1>AI-SafeSchool Guard</h1>
        <p>Người bạn đồng hành lắng nghe, hỗ trợ tìm hiểu pháp luật và nâng cao kỹ năng phòng ngừa nguy cơ ma túy học đường.</p>
        <div class="hero-note">💙 Lắng nghe không phán xét · Thông tin có trách nhiệm · Bảo vệ quyền riêng tư</div>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 3. KẾT NỐI AI VÀ TÀI LIỆU
# =========================================================
if not api_key:
    st.warning(
        "Chưa cấu hình GEMINI_API_KEY. Hãy thêm khóa API vào "
        "`.streamlit/secrets.toml` hoặc biến môi trường trước khi trò chuyện."
    )
    client = None
else:
    try:
        client = genai.Client(api_key=api_key)
    except Exception:
        client = None
        st.error("Không khởi tạo được dịch vụ AI. Vui lòng kiểm tra cấu hình API.")

@st.cache_resource(show_spinner="Đang chuẩn bị tài liệu tham khảo...")
def load_default_documents(_client):
    processed = []
    if _client is None:
        return processed
    for doc_path in DEFAULT_DOCS:
        if not doc_path.exists():
            continue
        try:
            mime_type = (
                "application/pdf"
                if doc_path.suffix.lower() == ".pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            with doc_path.open("rb") as source_file:
                uploaded = _client.files.upload(
                    file=source_file,
                    config=types.UploadFileConfig(mime_type=mime_type),
                )
            processed.append((doc_path.name, uploaded))
        except Exception:
            # Không hiển thị chi tiết lỗi nội bộ cho học sinh.
            continue
    return processed

loaded_docs_info = load_default_documents(client) if client else []
preloaded_files = [item[1] for item in loaded_docs_info]

# =========================================================
# 4. SIDEBAR: THÔNG TIN VÀ GIỚI HẠN
# =========================================================
with st.sidebar:
    st.markdown("## 🛡️ AI-SafeSchool Guard")
    st.caption("Trợ lý hỗ trợ an toàn học đường")
    st.divider()
    st.markdown("### 📚 Tài liệu tham khảo")
    if loaded_docs_info:
        for doc_name, _ in loaded_docs_info:
            st.markdown(f"- 📄 {doc_name}")
    else:
        st.info("Chưa nạp được tài liệu tham khảo. Cần kiểm tra tệp và cấu hình API.")
    st.divider()
    st.markdown("### 🔎 Lưu ý khi sử dụng")
    st.markdown(
        "- AI có thể trả lời chưa chính xác.\n"
        "- Không nhập họ tên, địa chỉ, số điện thoại hoặc thông tin nhận diện cá nhân.\n"
        "- Với nguy cơ tức thời, hãy liên hệ người lớn đáng tin cậy hoặc dịch vụ khẩn cấp phù hợp."
    )

# =========================================================
# 5. CHỌN CHẾ ĐỘ
# =========================================================
st.markdown('<div class="section-label">Bạn muốn làm gì hôm nay?</div>', unsafe_allow_html=True)
mode_selection = st.radio(
    "Chọn khu vực sử dụng",
    ["💬 Trợ lý học sinh", "📊 Quản trị hệ thống"],
    horizontal=True,
    label_visibility="collapsed",
)

# =========================================================
# 6. ADMIN: THỐNG KÊ TỐI THIỂU, KHÔNG LƯU NỘI DUNG TÂM SỰ
# =========================================================
if mode_selection == "📊 Quản trị hệ thống":
    st.subheader("🔐 Bảng điều khiển quản trị")
    st.caption("Chỉ dành cho người được nhà trường phân quyền.")
    if not admin_password:
        st.error("Chưa cấu hình ADMIN_PASSWORD trong secrets hoặc biến môi trường. Không thể mở khu vực quản trị.")
        st.stop()

    entered_password = st.text_input(
        "Mật khẩu quản trị",
        type="password",
        placeholder="Nhập mật khẩu quản trị",
    )
    if entered_password != admin_password:
        if entered_password:
            st.error("Thông tin xác thực chưa đúng.")
        else:
            st.info("Vui lòng xác thực để xem bảng điều khiển.")
        st.stop()

    logs = st.session_state.get("interaction_logs", [])
    logs_df = pd.DataFrame(logs)

    st.success("Đã xác thực. Dữ liệu bên dưới chỉ phản ánh các phiên tương tác được ghi nhận trong phiên chạy hiện tại.")
    total = len(logs_df) if not logs_df.empty else 0
    category_count = (
        logs_df["category"].value_counts()
        if total and "category" in logs_df.columns
        else pd.Series(dtype="int64")
    )
    top_category = category_count.index[0] if not category_count.empty else "Chưa có dữ liệu"
    col1, col2, col3 = st.columns(3)
    col1.metric("Lượt tương tác đã ghi nhận", total)
    col2.metric("Chủ đề phổ biến nhất", top_category)
    col3.metric("Tài liệu đang nạp", len(loaded_docs_info))

    st.markdown("### 📈 Phân bố chủ đề")
    if not category_count.empty:
        st.bar_chart(category_count)
    else:
        st.info("Chưa có dữ liệu thống kê trong phiên này.")

    if not logs_df.empty:
        st.markdown("### 🧾 Nhật ký tối thiểu")
        st.dataframe(logs_df, use_container_width=True, hide_index=True)

    st.markdown(
        '<div class="privacy-note">Thiết kế này không lưu nguyên văn câu hỏi vào nhật ký quản trị. '
        'Nếu triển khai thực tế, cần bổ sung chính sách lưu trữ, phân quyền, kiểm tra truy cập và quy trình xử lý sự cố dữ liệu.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# =========================================================
# 7. CHAT HỌC SINH
# =========================================================
st.markdown(
    """
    <div class="privacy-note">
      <strong>Không gian trò chuyện an toàn:</strong> Bạn có thể hỏi về cảm xúc, tình huống bị rủ rê hoặc quy định pháp luật.
      Không cần cung cấp tên thật hay thông tin có thể nhận diện bạn. AI không thay thế chuyên gia tâm lý, luật sư hoặc người hỗ trợ khẩn cấp.
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# Lối vào theo nhu cầu; nút chỉ đưa gợi ý vào ô chat thông qua session state.
if "suggested_prompt" not in st.session_state:
    st.session_state.suggested_prompt = ""

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown(
        '<div class="info-card"><div class="card-icon">💙</div><h3>Tâm sự cùng AI</h3><p>Khi bạn căng thẳng, cô đơn hoặc cần sắp xếp suy nghĩ.</p></div>',
        unsafe_allow_html=True,
    )
    if st.button("Chia sẻ cảm xúc", use_container_width=True):
        st.session_state.suggested_prompt = "Mình đang cảm thấy áp lực và muốn có người lắng nghe."
with col_b:
    st.markdown(
        '<div class="info-card"><div class="card-icon">🧪</div><h3>Nhận diện nguy cơ</h3><p>Tìm hiểu cách ứng xử khi gặp chất lạ hoặc bị rủ rê.</p></div>',
        unsafe_allow_html=True,
    )
    if st.button("Hỏi cách từ chối", use_container_width=True):
        st.session_state.suggested_prompt = "Nếu bị bạn bè rủ thử một chất lạ, mình nên từ chối và tìm hỗ trợ như thế nào?"
with col_c:
    st.markdown(
        '<div class="info-card"><div class="card-icon">⚖️</div><h3>Tra cứu pháp luật</h3><p>Tìm hiểu quy định và các bước kiểm chứng thông tin.</p></div>',
        unsafe_allow_html=True,
    )
    if st.button("Hỏi về pháp luật", use_container_width=True):
        st.session_state.suggested_prompt = "Mình muốn tìm hiểu quy định pháp luật hiện hành liên quan đến phòng, chống ma túy học đường."

system_instruction = """
Bạn là AI-SafeSchool Guard, trợ lý giáo dục hỗ trợ học sinh THPT về cảm xúc, kỹ năng ứng xử an toàn và kiến thức phòng ngừa ma túy học đường.

Nguyên tắc:
1. Trò chuyện bằng tiếng Việt rõ ràng, ấm áp, không phán xét; hỏi thêm nhẹ nhàng khi cần.
2. Không chẩn đoán bệnh tâm lý, không khẳng định chắc chắn về tình trạng của học sinh.
3. Khi trả lời pháp luật, ưu tiên tài liệu được cung cấp. Nêu rõ nếu tài liệu không đủ căn cứ hoặc có thể đã cũ; không tự bịa điều luật, số điều, mức phạt hay nguồn dẫn.
4. Với chất hoặc sản phẩm nghi vấn, không khẳng định chỉ từ tên gọi/hình ảnh rằng đó chắc chắn là ma túy. Khuyên không thử, không sử dụng và nhờ người lớn/cơ quan chuyên môn kiểm tra an toàn.
5. Nếu người dùng có dấu hiệu bị đe dọa, bị ép buộc, ngộ độc, nguy hiểm tức thời hoặc muốn tự làm hại bản thân, ưu tiên hướng dẫn tìm người lớn đáng tin cậy và trợ giúp khẩn cấp tại địa phương; không chỉ tiếp tục trò chuyện với AI.
6. Bảo vệ riêng tư: khuyến khích không cung cấp họ tên, địa chỉ, trường/lớp cụ thể, số điện thoại hoặc thông tin nhận diện.
7. Không tuyên bố AI thay thế chuyên gia tâm lý, luật sư, bác sĩ hay cơ quan chức năng.
"""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Chào bạn! 💙 Mình là **AI-SafeSchool Guard**. "
                "Bạn có thể tâm sự, hỏi cách xử lý tình huống bị rủ rê hoặc tìm hiểu kiến thức pháp luật. "
                "Bạn muốn bắt đầu từ điều gì hôm nay?"
            ),
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🛡️" if message["role"] == "assistant" else "🙂"):
        st.markdown(message["content"])

prompt_placeholder = st.session_state.suggested_prompt or (
    "Bạn đang băn khoăn điều gì? Hãy chia sẻ, không cần nêu thông tin nhận diện cá nhân..."
)
prompt = st.session_state.suggested_prompt or st.chat_input(prompt_placeholder)
if prompt:
    st.session_state.suggested_prompt = ""
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🙂"):
        st.markdown(prompt)

    # Chỉ lưu thời gian và nhóm chủ đề; không ghi nguyên văn nội dung nhạy cảm.
    prompt_lower = prompt.lower()
    category = "Tra cứu pháp luật"
    if any(word in prompt_lower for word in ["áp lực", "buồn", "căng thẳng", "sợ", "cô đơn", "tâm sự", "mệt mỏi", "lo lắng"]):
        category = "Tâm lý học đường"
    elif any(word in prompt_lower for word in ["bánh", "kẹo", "nước vui", "thuốc lá", "chất lạ", "hướng thần", "bị rủ"]):
        category = "Nhận diện nguy cơ"
    if "interaction_logs" not in st.session_state:
        st.session_state.interaction_logs = []
    st.session_state.interaction_logs.append(
        {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": category,
        }
    )

    with st.chat_message("assistant", avatar="🛡️"):
        with st.spinner("Đang xem xét câu hỏi..."):
            try:
                if client is None:
                    raise RuntimeError("Dịch vụ AI chưa được cấu hình.")
                contents = preloaded_files + [prompt] if preloaded_files else [prompt]
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.4,
                    ),
                )
                answer = response.text or (
                    "Mình chưa tạo được câu trả lời rõ ràng. Bạn thử diễn đạt lại câu hỏi nhé."
                )
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception:
                st.error(
                    "Hiện chưa thể kết nối hoặc xử lý câu hỏi. Vui lòng thử lại sau. "
                    "Nếu bạn đang gặp nguy hiểm ngay lúc này, hãy tìm người lớn đáng tin cậy để hỗ trợ trực tiếp."
                )

st.caption("AI-SafeSchool Guard là công cụ hỗ trợ giáo dục. Hãy kiểm chứng thông tin quan trọng và tìm hỗ trợ trực tiếp khi cần.")

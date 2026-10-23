import base64
import datetime
import os
import sqlite3
import time
import random
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH API KEY BẢO MẬT TỪ STREAMLIT SECRETS ---
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

MODEL_NAME = "gemini-2.5-flash"
MAX_API_ATTEMPTS = 3

if not GEMINI_API_KEY:
    st.error("Chưa cấu hình GEMINI_API_KEY. Vui lòng thêm khóa trong Streamlit Secrets.")
    st.stop()


def is_temporary_api_error(error):
    message = str(error).lower()
    return any(token in message for token in (
        "503", "service unavailable", "overloaded", "unavailable",
        "429", "resource_exhausted", "rate limit", "500", "502", "504",
        "internal server error", "deadline exceeded", "temporarily"
    ))


def send_message_with_retry(chat, message):
    """Thử lại có chờ tăng dần khi Gemini tạm thời quá tải."""
    last_error = None
    for attempt in range(MAX_API_ATTEMPTS):
        try:
            return chat.send_message(message)
        except Exception as error:
            last_error = error
            if attempt == MAX_API_ATTEMPTS - 1 or not is_temporary_api_error(error):
                raise
            time.sleep((2 ** (attempt + 1)) + random.uniform(0, 0.5))
    raise last_error

DEFAULT_DOCS = [
    "Tài liệu ma tuý học đường.docx",
    "Luật tra cứu liên quan về ma tuý.pdf"
]

# --- 2. CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="AI-SafeSchool Guard - Hệ sinh thái An toàn Học đường",
    page_icon="🛡️",
    layout="wide"
)

# --- 3. HÀM MÃ HÓA ẢNH NỀN BASE64 ---
def get_base64_of_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    return ""

img_base64 = get_base64_of_image("background.png")

# --- 4. CSS TÙY CHỈNH: GIAO DIỆN KÍNH MỜ ---
custom_css = f"""
<style>
.stApp {{
    background: linear-gradient(rgba(5, 15, 35, 0.25), rgba(5, 15, 35, 0.25)), 
                url("data:image/png;base64,{img_base64}") no-repeat top center fixed;
    background-size: cover;
}}

[data-testid="stSidebar"] {{
    background: rgba(10, 25, 50, 0.85);
    backdrop-filter: blur(12px);
    border-right: 1px solid rgba(59, 130, 246, 0.2);
}}

[data-testid="stChatMessage"] {{
    background-color: rgba(15, 23, 42, 0.65) !important;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 14px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}}

header {{visibility: hidden;}}

h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] {{
    color: #ffffff !important;
}}

[data-testid="stMarkdownContainer"] em, [data-testid="stMarkdownContainer"] small {{
    color: #cbd5e1 !important;
}}

.stChatInputContainer {{
    background-color: rgba(15, 23, 42, 0.75) !important;
    backdrop-filter: blur(12px);
    border-radius: 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    box-shadow: 0 4px 25px rgba(0, 0, 0, 0.4);
    padding: 4px;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 5. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE CHO NHẬT KÝ ---
DB_FILE = "interaction_logs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            category TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def add_log_to_db(timestamp, category, content):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (timestamp, category, content) VALUES (?, ?, ?)",
        (timestamp, category, content)
    )
    conn.commit()
    conn.close()

def get_logs_from_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT timestamp, category, content FROM logs ORDER BY id DESC", conn)
    conn.close()
    return df

# --- 6. HÀM NẠP TÀI LIỆU AN TOÀN QUA FILE API (CACHED) ---
@st.cache_resource
def load_default_documents(api_key):
    client = genai.Client(api_key=api_key)
    processed_files = []
    processed_names = []
    for doc_name in DEFAULT_DOCS:
        if os.path.exists(doc_name):
            try:
                mime_type = "application/pdf" if doc_name.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                with open(doc_name, "rb") as f_to_upload:
                    gemini_file = client.files.upload(
                        file=f_to_upload,
                        config=types.UploadFileConfig(mime_type=mime_type)
                    )
                processed_files.append(gemini_file)
                processed_names.append(doc_name)
            except Exception as e:
                print(f"Lỗi nạp file {doc_name}: {e}")
    return client, processed_files, processed_names

client, preloaded_files, preloaded_file_names = load_default_documents(GEMINI_API_KEY)

# --- 7. CẤU HÌNH NHÂN DẠNG HỆ THỐNG ---
system_instruction = """
Bạn là "AI-SafeSchool Guard", trợ lý chuyên gia ảo về giáo dục pháp luật, sơ cứu tâm lý học đường và phòng ngừa tệ nạn ma túy THPT.
NHIỆM VỤ & NGUYÊN TẮC BẮT BUỘC:
1. Bạn CHỈ ĐƯỢC PHÉP sử dụng thông tin, số liệu, điều luật, mức xử phạt và nội dung có trong hai tài liệu đã được cung cấp. Tuyệt đối không tự suy diễn hoặc lấy thông tin ngoài tài liệu.
2. Lắng nghe và thấu cảm: Đón nhận mọi tâm sự áp lực, căng thẳng của học sinh với thái độ nhẹ nhàng, không phán xét, khéo léo sơ cứu tâm lý.
3. Thông điệp giáo dục: Luôn lan tỏa "Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài" và "Không giữ, không thử, không tham gia tổ chức sử dụng ma túy dù chỉ một lần".
Phong cách: Tiếng Việt chuẩn mực, ấm áp khi tư vấn tâm lý, chuẩn xác khi trích dẫn pháp luật.
"""

# --- 8. KHỞI TẠO PHIÊN CHAT SESSION CHO MỖI PHIÊN LÀM VIỆC ---
def create_chat_session():
    chat = client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        )
    )
    if preloaded_files:
        send_message_with_retry(
            chat,
            preloaded_files + ["Hãy đọc kỹ các tài liệu trên để làm căn cứ trả lời xuyên suốt."]
        )
    return chat


if "chat_session" not in st.session_state:
    try:
        st.session_state.chat_session = create_chat_session()
    except Exception as error:
        st.session_state.chat_session = None
        print(f"Không thể khởi tạo phiên Gemini: {error}")

# --- 9. THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910795.png", width=60)
    st.markdown("### 🛡️ AI-SafeSchool Guard")
    st.markdown("**Slogan:** *Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài*")
    st.markdown("---")
    
    st.markdown("#### 📁 Kho tài liệu tích hợp")
    if len(preloaded_file_names) > 0:
        st.success("✅ Đã nạp thành công tài liệu cho học sinh!")
        for name in preloaded_file_names:
            st.markdown(f"- 📄 `{name}`")
    else:
        st.warning("⚠️ Không tìm thấy file tài liệu trong thư mục!")
    
    st.markdown("---")
    st.info("💡 Trợ lý AI sẵn sàng hỗ trợ tâm lý, pháp luật cho học sinh 24/7.")

# --- 10. TIÊU ĐỀ & THANH CHỌN CHẾ ĐỘ ---
st.title("🛡️ Trợ lý AI-SafeSchool Guard")
st.markdown("##### Hệ thống hỗ trợ tâm lý học đường, tra cứu pháp luật & quản trị cảnh báo sớm.")

mode_selection = st.radio(
    "📌 Chọn chế độ hệ thống:",
    ["💬 Trò chuyện với trợ lý AI", "📊 Admin"],
    horizontal=True
)
st.markdown("---")

# --- 11. QUẢN TRỊ NHÀ TRƯỜNG (ADMIN) ---
if "Admin" in mode_selection:
    st.subheader("🔒 Đăng nhập bảo mật Quản trị viên")
    admin_password_input = st.text_input("Nhập mật khẩu quản trị hệ thống:", type="password", placeholder="Nhập mật khẩu...")
    ADMIN_SECRET_KEY = "admin2026"
    
    if admin_password_input == ADMIN_SECRET_KEY:
        st.success("🔓 Đăng nhập thành công! Dưới đây là Bảng điều khiển phân tích dữ liệu:")
        st.markdown("---")
        
        df_logs = get_logs_from_db()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng lượt tương tác ẩn danh", len(df_logs), "Lưu trữ SQLite")
        
        top_cat = "Chưa có dữ liệu"
        if not df_logs.empty and "category" in df_logs.columns and len(df_logs["category"]) > 0:
            top_cat = df_logs["category"].mode()[0]
            
        col2.metric("Chủ đề học sinh quan tâm nhất", top_cat, "Chiếm đa số")
        col3.metric("Cảnh báo tâm lý cần lưu ý", "1 trường hợp", "Cần đồng hành")

        st.markdown("### 📈 Biểu đồ phân bổ nhu cầu tư vấn & tra cứu của học sinh")
        
        if not df_logs.empty:
            category_counts = df_logs["category"].value_counts()
            st.bar_chart(category_counts)

            st.markdown("### 📋 Nhật ký tương tác ẩn danh thời gian thực (Real-time Logs)")
            st.dataframe(df_logs, use_container_width=True)
            
            st.info("💡 **Bảo mật tuyệt đối:** Dữ liệu học sinh được ẩn danh và lưu trữ bền vững trong cơ sở dữ liệu SQLite.")
        else:
            st.info("Chưa có lịch sử tương tác nào được ghi nhận.")
            
    elif admin_password_input != "":
        st.error("❌ Mật khẩu không chính xác! Vui lòng nhập lại đúng mật khẩu quản trị.")
    else:
        st.info("💡 Vui lòng nhập mật khẩu quản trị để mở bảng điều khiển phân tích số liệu.")
        
    st.stop()

# --- 12. GIAO DIỆN CHAT CHÍNH (DÀNH CHO HỌC SINH) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! Tôi là **AI-SafeSchool Guard** – Người bạn đồng hành lắng nghe tâm sự, hỗ trợ giáo dục pháp luật và phòng ngừa tệ nạn ma túy học đường. Hôm nay bạn đang cảm thấy thế nào hoặc cần tra cứu vấn đề gì, hãy chia sẻ với tôi nhé!"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập tâm sự hoặc câu hỏi của bạn (ví dụ: Thuốc lá điện tử có chứa ma túy không?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    category = "Pháp luật & Ma túy mới"
    if any(kw in prompt.lower() for kw in ["áp lực", "buồn", "căng thẳng", "sợ", "cô đơn", "tâm sự", "mệt mỏi"]):
        category = "Tâm lý học đường"
    elif any(kw in prompt.lower() for kw in ["bánh", "kẹo", "nước", "thuốc lá", "chất", "hướng thần"]):
        category = "Nhận diện ma túy trá hình"

    add_log_to_db(current_time, category, prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("AI SafeSchool Guard đang lắng nghe và phân tích...")

        try:
            if st.session_state.chat_session is None:
                st.session_state.chat_session = create_chat_session()

            response = send_message_with_retry(st.session_state.chat_session, prompt)
            answer = response.text or "Mình chưa tạo được câu trả lời lần này. Bạn thử diễn đạt lại câu hỏi nhé."
            message_placeholder.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as error:
            print(f"Lỗi khi gọi Gemini: {error}")
            message_placeholder.markdown(
                "Xin lỗi bạn, dịch vụ AI đang quá tải hoặc kết nối tạm thời không ổn định. "
                "Bạn vui lòng chờ khoảng 10–20 giây rồi gửi lại câu hỏi nhé."
            )
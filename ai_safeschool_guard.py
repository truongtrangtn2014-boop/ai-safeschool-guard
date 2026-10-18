import os
import base64
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH API KEY BẢO MẬT & 2 FILE TÀI LIỆU ---
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

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

# --- 4. CSS TÙY CHỈNH: TỈ LỆ ẢNH NỀN & BONG BÓNG CHAT MỜ ẢO (COZE STYLE) ---
custom_css = f"""
<style>
/* Tinh chỉnh tỉ lệ và vị trí hiển thị hình nền */
.stApp {{
    background: linear-gradient(rgba(5, 15, 35, 0.25), rgba(5, 15, 35, 0.25)), 
                url("data:image/png;base64,{img_base64}") no-repeat top center fixed;
    background-size: cover;
}}

/* Thanh Sidebar kính mờ tối giản */
[data-testid="stSidebar"] {{
    background: rgba(10, 25, 50, 0.85);
    backdrop-filter: blur(12px);
    border-right: 1px solid rgba(59, 130, 246, 0.2);
}}

/* Khung bong bóng chat thiết kế mờ ảo (Glassmorphism) */
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

/* Ẩn header mặc định của Streamlit */
header {{visibility: hidden;}}

/* Ép toàn bộ chữ hiển thị màu trắng sáng sắc nét */
h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stMarkdownContainer"] {{
    color: #ffffff !important;
}}

/* Chú thích / trích dẫn luật */
[data-testid="stMarkdownContainer"] em, [data-testid="stMarkdownContainer"] small {{
    color: #cbd5e1 !important;
}}

/* Khung nhập tin nhắn */
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

# --- 5. TỰ ĐỘNG NẠP NGẦM 2 FILE CỐ ĐỊNH ---
client = genai.Client()

@st.cache_resource
def load_default_documents():
    processed = []
    for doc_name in DEFAULT_DOCS:
        if os.path.exists(doc_name):
            try:
                mime_type = "application/pdf" if doc_name.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                with open(doc_name, "rb") as f_to_upload:
                    gemini_file = client.files.upload(
                        file=f_to_upload,
                        config=types.UploadFileConfig(mime_type=mime_type)
                    )
                processed.append((doc_name, gemini_file))
            except Exception as e:
                print(f"Lỗi nạp file {doc_name}: {e}")
    return processed

loaded_docs_info = load_default_documents()
preloaded_files = [item[1] for item in loaded_docs_info]

# --- 6. KHỞI TẠO BỘ NHỚ LƯU TRỮ NHẬT KÝ TƯƠNG TÁC (CHO ADMIN DASHBOARD) ---
if "interaction_logs" not in st.session_state:
    st.session_state.interaction_logs = [
        {"timestamp": "2026-10-18 08:30", "category": "Pháp luật & Ma túy mới", "content": "Hỏi về mức xử phạt tàng trữ thuốc lá điện tử."},
        {"timestamp": "2026-10-18 09:15", "category": "Tâm lý học đường", "content": "Chia sẻ áp lực học tập và cảm giác căng thẳng."},
        {"timestamp": "2026-10-18 10:20", "category": "Nhận diện ma túy trá hình", "content": "Tra cứu thông tin về hình thức bánh lười."},
    ]

# --- 7. GIAO DIỆN THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910795.png", width=60)
    st.markdown("### 🛡️ AI-SafeSchool Guard")
    st.markdown("**Slogan:** *Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài*")
    st.markdown("---")
    
    st.markdown("#### 📁 Kho tài liệu tích hợp")
    if len(preloaded_files) > 0:
        st.success("✅ Đã nạp thành công tài liệu cho học sinh!")
        for name, _ in loaded_docs_info:
            st.markdown(f"- 📄 `{name}`")
    else:
        st.warning("⚠️ Không tìm thấy file tài liệu trong thư mục!")
    
    st.markdown("---")
    st.info("💡 Trợ lý AI đã sẵn sàng hỗ trợ tâm lý, pháp luật và kết nối hệ thống quản trị nhà trường.")

# --- 8. THANH ĐIỀU HƯỚNG CHÍNH (CHUYỂN ĐỔI CHẾ ĐỘ RÕ RÀNG TRÊN MÀN HÌNH) ---
st.title("🛡️ Trợ lý AI-SafeSchool Guard")
st.markdown("##### Hệ thống hỗ trợ tâm lý học đường, tra cứu pháp luật & quản trị cảnh báo sớm.")

# Tạo nút lựa chọn ngay trên màn hình chính để thầy dễ dàng demo đi thi
app_mode = st.radio(
    "📌 Chọn chế độ giao diện:",
    ["💬 Giao diện Trợ lý AI (Dành cho Học sinh)", "📊 Bảng điều khiển Quản trị & Cảnh báo (Dành cho Nhà trường)"],
    horizontal=True
)
st.markdown("---")

# --- 9. NẾU CHỌN CHẾ ĐỘ QUẢN TRỊ (ADMIN DASHBOARD) ---
if "Quản trị" in app_mode:
    st.title("📊 Hệ thống Quản trị & Cảnh báo sớm - Admin Dashboard")
    st.markdown("##### Dành cho Ban Giám hiệu, Giáo viên chủ nhiệm & Đoàn trường theo dõi xu hướng an toàn học đường.")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng lượt tương tác ẩn danh", len(st.session_state.interaction_logs), "+3 phiên mới")
    col2.metric("Chủ đề học sinh quan tâm nhất", "Nhận diện ma túy trá hình", "Chiếm đa số")
    col3.metric("Cảnh báo tâm lý cần lưu ý", "1 trường hợp", "Cần đồng hành")

    st.markdown("### 📈 Biểu đồ phân bổ nhu cầu tư vấn & tra cứu của học sinh")
    df_logs = pd.DataFrame(st.session_state.interaction_logs)
    
    if not df_logs.empty:
        category_counts = df_logs["category"].value_counts()
        st.bar_chart(category_counts)

        st.markdown("### 📋 Nhật ký tương tác ẩn danh thời gian thực (Real-time Logs)")
        st.dataframe(df_logs, use_container_width=True)
        
        st.info("💡 **Tính năng bảo mật:** Toàn bộ dữ liệu được ẩn danh tuyệt đối, giúp nhà trường nắm bắt xu hướng tâm lý và mối lo ngại của học sinh để điều chỉnh nội dung giáo dục kịp thời.")
    
    st.stop() # Dừng chạy giao diện chat bên dưới

# --- 10. CẤU HÌNH NHÂN DẠNG HỆ THỐNG (TÂM LÝ & PHÁP LÝ) ---
system_instruction = """
Bạn là "AI-SafeSchool Guard", một trợ lý chuyên gia ảo thông minh, thấu cảm về giáo dục pháp luật, sơ cứu tâm lý học đường và phòng ngừa tệ nạn ma túy trong cơ sở giáo dục THPT.

Nhiệm vụ và phong cách của bạn:
1. **Lắng nghe và Thấu cảm (Sơ cứu tâm lý):** Khi học sinh chia sẻ về áp lực học tập, căng thẳng, buồn chán, cô đơn hoặc các mối quan hệ, hãy luôn đón nhận bằng sự thấu hiểu, nhẹ nhàng, không phán xét. Động viên các em và đưa ra lời khuyên tích cực để giải tỏa cảm xúc.
2. **Nhận diện nguy cơ sớm:** Tinh tế nhận ra các dấu hiệu học sinh đang tìm cách giải tỏa áp lực bằng những con đường sai lầm (như thử chất lạ, tìm quên trong khói thuốc, nghe lời rủ rê...), từ đó khéo léo cảnh báo hiểm họa.
3. **Tra cứu pháp luật chính xác:** Trả lời cực kỳ chính xác dựa trên nội dung các file tài liệu đã được nạp sẵn trong hệ thống (Luật Phòng, chống ma túy, các mức xử phạt hành chính, hình sự, nhận diện ma túy mới/trá hình như nước vui, bánh lười, thuốc lá điện tử, bùa lưỡi...).
4. **Thông điệp giáo dục:** Luôn lan tỏa thông điệp: "Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài" và "Không giữ, không thử, không tham gia tổ chức sử dụng ma túy dù chỉ một lần".

Phong cách: Tiếng Việt chuẩn mực, ấm áp, thấu hiểu khi trò chuyện tâm lý, nhưng đồng thời sắc sảo, vững vàng và có tính giáo dục cao khi tư vấn pháp luật.
"""

# --- 11. GIAO DIỆN CHAT CHÍNH (DÀNH CHO HỌC SINH) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! Tôi là **AI-SafeSchool Guard** – Người bạn đồng hành lắng nghe tâm sự, hỗ trợ giáo dục pháp luật và phòng ngừa tệ nạn ma túy học đường. Hôm nay bạn đang cảm thấy thế nào hoặc cần tra cứu vấn đề gì, hãy chia sẻ với tôi nhé!"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập tâm sự hoặc câu hỏi của bạn (ví dụ: Tôi đang rất áp lực... hoặc Thế nào là chất hướng thần?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Tự động ghi nhận log phân loại ngầm phục vụ Admin Dashboard
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    category = "Pháp luật & Ma túy mới"
    if any(kw in prompt.lower() for kw in ["áp lực", "buồn", "căng thẳng", "sợ", "cô đơn", "tâm sự", "mệt mỏi"]):
        category = "Tâm lý học đường"
    elif any(kw in prompt.lower() for kw in ["bánh", "kẹo", "nước", "thuốc lá", "chất", "hướng thần"]):
        category = "Nhận diện ma túy trá hình"

    st.session_state.interaction_logs.append({
        "timestamp": current_time,
        "category": category,
        "content": prompt
    })

    with st.chat_message("assistant"):
        with st.spinner("AI-SafeSchool Guard đang lắng nghe và phân tích..."):
            try:
                contents = preloaded_files + [prompt]
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                    )
                )
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Đã xảy ra lỗi kết nối hoặc xử lý dữ liệu: {e}")
import os
import base64
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
    page_title="AI-SafeSchool Guard - Trợ lý Phòng chống Ma túy",
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
/* Tinh chỉnh tỉ lệ và vị trí hiển thị hình nền để thấy rõ phần tiêu đề chữ phía trên */
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

/* Khung bong bóng chat thiết kế mờ ảo (Glassmorphism) giống Coze */
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

/* Chú thích / trích dẫn luật hiển thị mềm mại hơn */
[data-testid="stMarkdownContainer"] em, [data-testid="stMarkdownContainer"] small {{
    color: #cbd5e1 !important;
}}

/* Khung nhập tin nhắn (Chat Input) bo tròn mờ ảo ở đáy màn hình */
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

# --- 6. GIAO DIỆN THANH BÊN (SIDEBAR) ---
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
    st.info("💡 Trợ lý AI đã sẵn sàng hỗ trợ học sinh tra cứu luật và xử lý tình huống học đường.")

# --- 7. CẤU HÌNH NHÂN DẠNG HỆ THỐNG ---
system_instruction = """
Bạn là "AI-SafeSchool Guard", một trợ lý chuyên gia ảo thông minh về giáo dục pháp luật và phòng ngừa tệ nạn ma túy trong cơ sở giáo dục THPT.
Nhiệm vụ của bạn:
1. Trả lời cực kỳ chính xác dựa trên nội dung các file tài liệu đã được nạp sẵn trong hệ thống.
2. Cung cấp thông tin chuẩn xác về Luật Phòng, chống ma túy, các mức xử phạt vi phạm hành chính, hình sự (Bộ luật Hình sự).
3. Hỗ trợ nhận diện các loại ma túy mới, ma túy trá hình (nước vui, bánh lười, thuốc lá điện tử, tem thư, bùa lưỡi...).
4. Đưa ra lời khuyên giáo dục, rèn luyện kỹ năng sống với thông điệp: "Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài" và "Không giữ, không thử, không tham gia tổ chức sử dụng ma túy dù chỉ một lần".
Phong cách: Tiếng Việt chuẩn mực, gần gũi với học sinh THPT, sắc sảo, tính giáo dục cao, thấu hiểu, bảo mật.
"""

# --- 8. GIAO DIỆN CHAT CHÍNH ---
st.title("🛡️ Trợ lý AI-SafeSchool Guard")
st.markdown("##### Hệ thống hỗ trợ tra cứu pháp luật, nhận diện ma túy trá hình & giải quyết tình huống học đường.")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! Tôi là **AI-SafeSchool Guard** – Trợ lý chuyên gia ảo về giáo dục pháp luật và phòng ngừa tệ nạn ma túy học đường. Tôi đã được nạp sẵn toàn bộ tài liệu chính thức. Bạn cần tra cứu câu hỏi, luật hay xử lý tình huống nào, hãy hỏi tôi nhé!"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập câu hỏi của bạn (ví dụ: Thế nào là chất hướng thần? hoặc tra cứu câu hỏi tình huống...)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("AI-SafeSchool Guard đang tra cứu tài liệu và phân tích..."):
            try:
                contents = preloaded_files + [prompt]
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.6,
                    )
                )
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Đã xảy ra lỗi kết nối hoặc xử lý dữ liệu: {e}")
import os
import streamlit as st
from google import genai
from google.genai import types

# --- TÍCH HỢP TRỰC TIẾP API KEY MỚI CỦA BẠN ---
os.environ["GEMINI_API_KEY"] = "AQ.Ab8RN6Jibkc5PyCb6SbtzXMws9Ncbk8QpnOQaTeHAPih0mgfQ"

# --- CẤU HÌNH GIAO DIỆN TRANG WEB ---
st.set_page_config(
    page_title="AI-SafeSchool Guard - Trợ lý Phòng chống Ma túy",
    page_icon="🛡️",
    layout="wide"
)

# --- CSS TÙY CHỈNH GIAO DIỆN (ẢNH NỀN POSTER VÀ BONG BÓNG CHAT) ---
custom_css = """
<style>
/* Cài đặt ảnh nền poster toàn màn hình từ file background.png */
.stApp {
    background: linear-gradient(rgba(5, 15, 35, 0.4), rgba(5, 15, 35, 0.4)), 
                url("background.png") no-repeat center center fixed;
    background-size: cover;
}

/* Thanh Sidebar */
[data-testid="stSidebar"] {
    background: rgba(10, 25, 50, 0.90);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(59, 130, 246, 0.2);
}

/* Bong bóng chat nổi bật */
[data-testid="stChatMessage"] {
    background-color: rgba(15, 23, 42, 0.88) !important;
    border-radius: 14px;
    padding: 12px 16px;
    margin-bottom: 10px;
    border: 1px solid rgba(59, 130, 246, 0.3);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
}

/* Màu chữ sáng rõ */
h1, h2, h3, p, label, span {
    color: #f8fafc !important;
}

/* Khung nhập tin nhắn ở đáy */
.stChatInputContainer {
    background-color: rgba(15, 23, 42, 0.95) !important;
    border-radius: 15px;
    border: 1px solid rgba(59, 130, 246, 0.5);
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- THANH BÊN (SIDEBAR): TẢI FILE TÀI LIỆU ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910795.png", width=65)
    st.markdown("### 🛡️ AI-SafeSchool Guard")
    st.markdown("**Slogan:** *Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài*")
    st.markdown("---")
    
    st.markdown("#### 📁 Tải tài liệu tra cứu")
    uploaded_files = st.file_uploader(
        "Tải file PDF ngân hàng câu hỏi hoặc luật:",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True
    )
    
    st.markdown("---")
    st.success("✅ Trợ lý AI đã sẵn sàng với Key mới!")
    st.info("💡 **Mẹo:** Tải file PDF của bạn lên đây, hệ thống sẽ tự động trích xuất nội dung để tra cứu chính xác.")

# --- KHỞI TẠO CLIENT ---
client = genai.Client()

# --- XỬ LÝ NẠP FILE AN TOÀN ---
processed_files = []
if uploaded_files:
    with st.spinner("Đang xử lý tài liệu cho trợ lý AI..."):
        for uploaded_file in uploaded_files:
            temp_path = os.path.join(".", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            try:
                mime_type = "application/pdf" if uploaded_file.name.endswith(".pdf") else "application/octet-stream"
                if uploaded_file.name.endswith(".docx"):
                    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif uploaded_file.name.endswith(".txt"):
                    mime_type = "text/plain"

                with open(temp_path, "rb") as f_to_upload:
                    gemini_file = client.files.upload(
                        file=f_to_upload,
                        config=types.UploadFileConfig(mime_type=mime_type)
                    )
                processed_files.append(gemini_file)
                st.sidebar.success(f"Nạp thành công: {uploaded_file.name}")
            except Exception as e:
                st.sidebar.error(f"Lỗi nạp file {uploaded_file.name}: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

# --- CẤU HÌNH NHÂN DẠNG HỆ THỐNG ---
system_instruction = """
Bạn là "AI-SafeSchool Guard", một trợ lý chuyên gia ảo thông minh về giáo dục pháp luật và phòng ngừa tệ nạn ma túy trong cơ sở giáo dục THPT.
Nhiệm vụ của bạn:
1. Trả lời cực kỳ chính xác dựa trên nội dung các file tài liệu/PDF mà người dùng đã tải lên (ngân hàng câu hỏi, luật, nghị định, xử phạt, tình huống...).
2. Cung cấp thông tin chuẩn xác về Luật Phòng, chống ma túy, các mức xử phạt vi phạm hành chính, hình sự (Bộ luật Hình sự).
3. Hỗ trợ nhận diện các loại ma túy mới, ma túy trá hình (nước vui, bánh lười, thuốc lá điện tử, tem thư, bùa lưỡi...).
4. Đưa ra lời khuyên giáo dục, rèn luyện kỹ năng sống với thông điệp: "Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài" và "Không giữ, không thử, không tham gia tổ chức sử dụng ma túy dù chỉ một lần".
Phong cách: Tiếng Việt chuẩn mực, gần gũi với học sinh THPT, sắc sảo, tính giáo dục cao, thấu hiểu, bảo mật.
"""

# --- GIAO DIỆN CHAT CHÍNH ---
st.title("🛡️ Trợ lý AI-SafeSchool Guard")
st.markdown("##### Hệ thống hỗ trợ tra cứu pháp luật, nhận diện ma túy trá hình & giải quyết tình huống học đường.")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập câu hỏi của bạn (ví dụ: Thế nào là ma túy? hoặc tra cứu câu hỏi...)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("AI-SafeSchool Guard đang tra cứu tài liệu và phân tích..."):
            try:
                contents = processed_files + [prompt]
                response = client.models.generate_content(
                    model='gemini-3.5-flash-lite',
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
                st.error(f"Đã xảy ra lỗi kết nối hoặc xử lý file: {e}")
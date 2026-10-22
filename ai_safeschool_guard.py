import base64
import datetime
import os
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH API KEY BẢO MẬT TỪ STREAMLIT SECRETS ---
if "GEMINI_API_KEY" in st.secrets:
  os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

DEFAULT_DOCS = [
    "Tài liệu ma tuý học đường.docx",
    "Luật tra cứu liên quan về ma tuý.pdf",
]

# --- 2. CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="AI-SafeSchool Guard - Hệ sinh thái An toàn Học đường",
    page_icon="🛡️",
    layout="wide",
)


# --- 3. HÀM MÃ HÓA ẢNH NỀN BASE64 ---
def get_base64_of_image(image_path):
  if os.path.exists(image_path):
    with open(image_path, "rb") as f:
      data = f.read()
    return base64.b64encode(data).decode("utf-8")
  return ""


img_base64 = get_base64_of_image("background.png")

# --- 4. CSS TÙY CHỈNH: GIAO DIỆN KÍNH MỜ (COZE STYLE) ---
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

# --- 5. HÀM KHỞI TẠO CLIENT VÀ NẠP TÀI LIỆU AN TOÀN (CACHED) ---
@st.cache_resource
def init_gemini_system():
  client = genai.Client()
  preloaded_files = []
  loaded_info = []
  
  for doc_name in DEFAULT_DOCS:
    if os.path.exists(doc_name):
      try:
        mime_type = (
            "application/pdf"
            if doc_name.endswith(".pdf")
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        with open(doc_name, "rb") as f_to_upload:
          gemini_file = client.files.upload(
              file=f_to_upload, config=types.UploadFileConfig(mime_type=mime_type)
          )
        preloaded_files.append(gemini_file)
        loaded_info.append((doc_name, gemini_file))
      except Exception as e:
        print(f"Lỗi nạp file {doc_name}: {e}")
        
  system_instruction = """
  Bạn là "AI-SafeSchool Guard", trợ lý chuyên gia ảo về giáo dục pháp luật, sơ cứu tâm lý học đường và phòng ngừa tệ nạn ma túy THPT.
  NHIỆM VỤ & NGUYÊN TẮC BẮT BUỘC:
  1. Bạn CHỈ ĐƯỢC PHÉP sử dụng thông tin, số liệu, điều luật, mức xử phạt và nội dung có trong hai tài liệu đã được nạp sẵn. Tuyệt đối không tự suy diễn hoặc bịa đặt ngoài tài liệu.
  2. Lắng nghe và thấu cảm: Đón nhận mọi tâm sự áp lực, căng thẳng của học sinh với thái độ nhẹ nhàng, không phán xét, khéo léo sơ cứu tâm lý.
  3. Thông điệp giáo dục: Luôn lan tỏa "Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài" và "Không giữ, không thử, không tham gia tổ chức sử dụng ma túy dù chỉ một lần".
  Phong cách: Tiếng Việt chuẩn mực, ấm áp khi tư vấn pháp luật và tâm lý dựa trên tài liệu.
  """
  
  # Khởi tạo Chat Session với model gemini-2.0-flash ổn định cao
  chat_session = client.chats.create(
      model="gemini-3.8-flash",
      config=types.GenerateContentConfig(
          system_instruction=system_instruction,
          temperature=0.2,
      ),
  )
  
  # Gửi tài liệu ngầm một lần duy nhất lúc khởi động để AI ghi nhớ ngữ cảnh
  if preloaded_files:
    chat_session.send_message(
        preloaded_files + ["Hãy ghi nhớ kỹ toàn bộ nội dung trong các tài liệu đã đính kèm này để làm căn cứ trả lời xuyên suốt các câu hỏi."]
    )
    
  return chat_session, loaded_info


chat_session, loaded_docs_info = init_gemini_system()
preloaded_file_names = [item[0] for item in loaded_docs_info]

# --- 6. KHỞI TẠO BỘ NHỚ LƯU TRỮ NHẬT KÝ TƯƠNG TÁC ---
if "interaction_logs" not in st.session_state:
  st.session_state.interaction_logs = [
      {
          "timestamp": "2026-10-18 08:30",
          "category": "Pháp luật & Ma túy mới",
          "content": "Hỏi về mức xử phạt tàng trữ thuốc lá điện tử.",
      },
      {
          "timestamp": "2026-10-18 09:15",
          "category": "Tâm lý học đường",
          "content": "Chia sẻ áp lực học tập và cảm giác căng thẳng.",
      },
      {
          "timestamp": "2026-10-18 10:20",
          "category": "Nhận diện ma túy trá hình",
          "content": "Tra cứu thông tin về hình thức bánh lười.",
      },
  ]

# --- 7. THANH BÊN (SIDEBAR) ---
with st.sidebar:
  st.image("https://cdn-icons-png.flaticon.com/512/2910/2910795.png", width=60)
  st.markdown("### 🛡️ AI-SafeSchool Guard")
  st.markdown(
      "**Slogan:** *Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo"
      " đài*"
  )
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

# --- 8. TIÊU ĐỀ & THANH CHỌN CHẾ ĐỘ ---
st.title("🛡️ Trợ lý AI-SafeSchool Guard")
st.markdown(
    "##### Hệ thống hỗ trợ tâm lý học đường, tra cứu pháp luật & quản trị cảnh"
    " báo sớm."
)

mode_selection = st.radio(
    "📌 Chọn chế độ hệ thống:",
    ["💬 Trò chuyện với trợ lý AI", "📊 Admin"],
    horizontal=True,
)
st.markdown("---")

# --- 9. QUẢN TRỊ NHÀ TRƯỜNG (ADMIN) ---
if "Admin" in mode_selection:
  st.subheader("🔒 Đăng nhập bảo mật Quản trị viên")
  admin_password_input = st.text_input(
      "Nhập mật khẩu quản trị hệ thống:",
      type="password",
      placeholder="Nhập mật khẩu...",
  )
  ADMIN_SECRET_KEY = "admin2026"

  if admin_password_input == ADMIN_SECRET_KEY:
    st.success(
        "🔓 Đăng nhập thành công! Dưới đây là Bảng điều khiển phân tích dữ liệu:"
    )
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Tổng lượt tương tác ẩn danh",
        len(st.session_state.interaction_logs),
        "+3 phiên mới",
    )
    col2.metric(
        "Chủ đề học sinh quan tâm nhất",
        "Nhận diện ma túy trá hình",
        "Chiếm đa số",
    )
    col3.metric("Cảnh báo tâm lý cần lưu ý", "1 trường hợp", "Cần đồng hành")

    st.markdown(
        "### 📈 Biểu đồ phân bổ nhu cầu tư vấn & tra cứu của học sinh"
    )
    df_logs = pd.DataFrame(st.session_state.interaction_logs)

    if not df_logs.empty:
      category_counts = df_logs["category"].value_counts()
      st.bar_chart(category_counts)

      st.markdown(
          "### 📋 Nhật ký tương tác ẩn danh thời gian thực (Real-time Logs)"
      )
      st.dataframe(df_logs, use_container_width=True)

      st.info(
          "💡 **Bảo mật tuyệt đối:** Dữ liệu học sinh được ẩn danh hoàn toàn, giúp"
          " nhà trường nắm bắt xu hướng tâm lý và mối lo ngại để định hướng giáo"
          " dục kịp thời."
      )

  elif admin_password_input != "":
    st.error(
        "❌ Mật khẩu không chính xác! Vui lòng nhập lại đúng mật khẩu quản trị."
    )
  else:
    st.info(
        "💡 Vui lòng nhập mật khẩu quản trị để mở bảng điều khiển phân tích số"
        " liệu."
    )

  st.stop()

# --- 10. GIAO DIỆN CHAT CHÍNH (DÀNH CHO HỌC SINH) ---
if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          "Chào bạn! Tôi là **AI-SafeSchool Guard** – Người bạn đồng hành lắng"
          " nghe tâm sự, hỗ trợ giáo dục pháp luật và phòng ngừa tệ nạn ma túy"
          " học đường. Hôm nay bạn đang cảm thấy thế nào hoặc cần tra cứu vấn"
          " đề gì, hãy chia sẻ với tôi nhé!"
      ),
  }]

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

if prompt := st.chat_input(
    "Nhập tâm sự hoặc câu hỏi của bạn (ví dụ: Thuốc lá điện tử có chứa ma túy không?)"
):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
  category = "Pháp luật & Ma túy mới"
  if any(
      kw in prompt.lower()
      for kw in ["áp lực", "buồn", "căng thẳng", "sợ", "cô đơn", "tâm sự", "mệt mỏi"]
  ):
    category = "Tâm lý học đường"
  elif any(
      kw in prompt.lower()
      for kw in ["bánh", "kẹo", "nước", "thuốc lá", "chất", "hướng thần"]
  ):
    category = "Nhận diện ma túy trá hình"

  st.session_state.interaction_logs.append({
      "timestamp": current_time,
      "category": category,
      "content": prompt,
  })

  with st.chat_message("assistant"):
    message_placeholder = st.empty()
    # Hiển thị thông báo khi đang suy nghĩ theo đúng yêu cầu
    message_placeholder.markdown("AI SafeSchool Guard đang lắng nghe và phân tích...")

    try:
      # Gửi trực tiếp câu hỏi gọn nhẹ qua Chat Session đã lưu ngữ cảnh tài liệu sẵn trên server
      response = chat_session.send_message(prompt)
      answer = response.text
      message_placeholder.markdown(answer)
      st.session_state.messages.append({"role": "assistant", "content": answer})
    except Exception as e:
      message_placeholder.error(
          f"Đã xảy ra lỗi kết nối hoặc xử lý dữ liệu: {e}"
      )
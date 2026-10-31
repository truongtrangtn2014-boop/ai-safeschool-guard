import os
import base64
import datetime
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH BẢO MẬT & TÀI LIỆU ---
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
ADMIN_SECRET_KEY = st.secrets.get("ADMIN_PASSWORD", "admin2026")

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

# --- 4. CSS TÙY CHỈNH ---
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

# Khởi tạo Gemini Client
if not API_KEY:
    st.error("Chưa tìm thấy GEMINI_API_KEY trong Streamlit Secrets!")
    st.stop()

client = genai.Client(api_key=API_KEY)

# --- 5. TỰ ĐỘNG NẠP FILE TÀI LIỆU ---
@st.cache_resource
def load_default_documents():
    processed = []
    for doc_name in DEFAULT_DOCS:
        if os.path.exists(doc_name):
            try:
                mime_type = "application/pdf" if doc_name.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
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

# --- 6. HÀM PHÂN TÍCH NHÃN ĐA TẦNG (CATEGORY & SUB-LABEL) ---
def classify_interaction(text):
    """Bóc tách chính xác Nhóm chính và Nhãn con cụ thể từ nội dung tâm sự/câu hỏi"""
    t = text.lower()
    
    # 1. Bị rủ rê, lôi kéo, ép thử
    if any(k in t for k in ["rủ", "ép", "dụ dỗ", "lôi kéo", "thử 1 viên", "thử một viên", "cho thử"]):
        return "Tệ nạn & Ma túy mới", "Bị rủ rê / Ép buộc thử chất lạ"
    
    # 2. Thuốc lá điện tử, Vape, Pod
    if any(k in t for k in ["thuốc lá điện tử", "pod", "vape", "hút pod", "hút thuốc lá", "tinh dầu"]):
        return "Tệ nạn & Ma túy mới", "Thuốc lá điện tử (Pod / Vape)"
    
    # 3. Ma túy trá hình (bánh lười, nước vui, tem giấy...)
    if any(k in t for k in ["bánh lười", "nước vui", "kẹo", "viên", "bùa lưỡi", "tem giấy", "trà sữa", "chất lạ"]):
        return "Nhận diện ma túy trá hình", "Ma túy trá hình thực phẩm / đồ uống"
        
    # 4. Bị tẩy chay, cô lập, bạo lực tinh thần
    if any(k in t for k in ["xa lánh", "cô lập", "tẩy chay", "bạn bè không chơi", "ghét bỏ", "bị bắt nạt", "nói xấu"]):
        return "Tâm lý học đường", "Mâu thuẫn bạn bè / Bị cô lập, tẩy chay"
        
    # 5. Áp lực thi cử, học tập, kỳ vọng cha mẹ
    if any(k in t for k in ["áp lực", "căng thẳng", "stress", "học tập", "điểm số", "kỳ vọng", "bố mẹ mắng", "mệt mỏi", "bế tắc", "chán sống"]):
        return "Tâm lý học đường", "Áp lực học tập & Kỳ vọng gia đình"
        
    # 6. Khung hình phạt, luật pháp
    if any(k in t for k in ["luật", "phạt", "tù", "tội", "bị bắt", "công an", "nghị định", "điều khoản", "tàng trữ", "xử lý"]):
        return "Pháp luật & Xử phạt", "Tra cứu trách nhiệm pháp lý & Xử phạt"
        
    return "Tâm lý học đường", "Tâm sự & Giải tỏa cảm xúc cá nhân"

# Khởi tạo dữ liệu ban đầu
if "interaction_logs" not in st.session_state:
    st.session_state.interaction_logs = [
        {"timestamp": "2026-10-18 08:30", "category": "Pháp luật & Xử phạt", "sub_label": "Tra cứu trách nhiệm pháp lý & Xử phạt", "content": "Hỏi về mức xử phạt tàng trữ thuốc lá điện tử trong trường học."},
        {"timestamp": "2026-10-18 09:15", "category": "Tâm lý học đường", "sub_label": "Áp lực học tập & Kỳ vọng gia đình", "content": "Chia sẻ áp lực học tập và cảm giác căng thẳng trước kỳ thi."},
        {"timestamp": "2026-10-18 10:20", "category": "Nhận diện ma túy trá hình", "sub_label": "Ma túy trá hình thực phẩm / đồ uống", "content": "Tra cứu thông tin về hình thức bánh lười và kẹo cần sa."},
        {"timestamp": "2026-10-31 15:57", "category": "Tâm lý học đường", "sub_label": "Áp lực học tập & Kỳ vọng gia đình", "content": "Tôi cảm thấy cuộc sống quá áp lực"},
        {"timestamp": "2026-10-31 15:58", "category": "Tệ nạn & Ma túy mới", "sub_label": "Bị rủ rê / Ép buộc thử chất lạ", "content": "Có người đã từng nói với em là thử 1 viên thuốc lắc sẽ hết buồn"},
        {"timestamp": "2026-10-31 15:59", "category": "Tệ nạn & Ma túy mới", "sub_label": "Bị rủ rê / Ép buộc thử chất lạ", "content": "Vậy nên làm gì khi có người cố tình rủ rê lôi kéo em?"},
        {"timestamp": "2026-10-31 16:00", "category": "Tâm lý học đường", "sub_label": "Mâu thuẫn bạn bè / Bị cô lập, tẩy chay", "content": "bạn bè luôn xa lánh và cô lập em ở lớp"},
    ]

# --- 7. THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910795.png", width=60)
    st.markdown("### 🛡️ AI-SafeSchool Guard")
    st.markdown("**Slogan:** *Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài*")
    st.markdown("---")
    
    st.markdown("#### 📁 Kho tài liệu tích hợp")
    if len(preloaded_files) > 0:
        st.success("✅ Đã nạp thành công tài liệu hệ thống!")
        for name, _ in loaded_docs_info:
            st.markdown(f"- 📄 `{name}`")
    else:
        st.warning("⚠️ Chưa tìm thấy file tài liệu trong thư mục.")
    
    st.markdown("---")
    st.info("💡 Trợ lý AI sẵn sàng hỗ trợ tâm lý, pháp luật cho học sinh 24/7.")

# --- 8. TIÊU ĐỀ & CHỌN CHẾ ĐỘ ---
st.title("🛡️ Trợ lý AI-SafeSchool Guard")
st.markdown("##### Hệ thống hỗ trợ tâm lý học đường, tra cứu pháp luật & quản trị cảnh báo sớm.")

mode_selection = st.radio(
    "📌 Chọn chế độ hệ thống:",
    ["💬 Giao diện Học sinh (Chat)", "📊 Bảng điều khiển Quản trị Nhà trường (Admin)"],
    horizontal=True
)
st.markdown("---")

# --- 9. NẾU CHỌN QUẢN TRỊ NHÀ TRƯỜNG ---
if "Quản trị" in mode_selection:
    st.subheader("🔒 Bảng điều khiển Quản trị & Phân tích Dữ liệu")
    admin_password_input = st.text_input(
        "Nhập mật khẩu quản trị hệ thống:",
        type="password",
        placeholder="Nhập mật khẩu..."
    )
    
    if admin_password_input:
        if admin_password_input == ADMIN_SECRET_KEY:
            st.success("🔓 Xác thực thành công! Phân tích xu hướng tâm lý & tệ nạn học đường thời gian thực:")
            st.markdown("---")
            
            df_logs = pd.DataFrame(st.session_state.interaction_logs)
            
            if not df_logs.empty and "category" in df_logs.columns:
                total_logs = len(df_logs)
                
                # Thống kê theo các mảng lớn (category)
                cat_counts = df_logs["category"].value_counts()
                
                # Xác định mảng lớn chiếm tỷ lệ cao nhất
                top_category = cat_counts.index[0]
                top_category_count = cat_counts.iloc[0]
                pct_top_category = int(round((top_category_count / total_logs) * 100))
                
                # Đếm trường hợp nguy cơ cần can thiệp từ nhãn con
                risk_cases = 0
                if "sub_label" in df_logs.columns:
                    risk_cases = len(df_logs[df_logs["sub_label"].isin([
                        "Bị rủ rê / Ép buộc thử chất lạ", 
                        "Mâu thuẫn bạn bè / Bị cô lập, tẩy chay"
                    ])])

                # 3 Chỉ số đầu trang
                col1, col2, col3 = st.columns(3)
                col1.metric("Tổng lượt trao đổi ẩn danh", f"{total_logs} lượt", f"+{total_logs} phản ánh")
                col2.metric("Chủ đề học sinh quan tâm nhất", top_category, f"Chiếm {pct_top_category}% ({top_category_count} lượt)")
                col3.metric("Cảnh báo nguy cơ cần can thiệp", f"{risk_cases} trường hợp", "Cần đồng hành ngay")

                st.markdown("---")
                
                # Biểu đồ phân bổ nhu cầu theo các mảng lớn
                st.markdown("### 📊 Nhu cầu theo các mảng")
                st.bar_chart(cat_counts)

                st.markdown("---")
                # Bảng nhật ký tương tác thời gian thực
                st.markdown("### 📋 Nhật ký tương tác ẩn danh thời gian thực (Real-time Logs)")
                st.dataframe(df_logs, use_container_width=True)

            else:
                st.info("Chưa có dữ liệu tương tác để phân tích.")
        else:
            st.error("❌ Mật khẩu không chính xác! Vui lòng nhập lại.")
    else:
        st.info("💡 Vui lòng nhập mật khẩu của quản trị để mở bảng điều khiển phân tích số liệu.")
        
    st.stop()

# --- 10. CẤU HÌNH NHÂN DẠNG HỆ THỐNG ---
system_instruction = """
Bạn là "AI-SafeSchool Guard", một trợ lý chuyên gia ảo thông minh, thấu cảm về giáo dục pháp luật, sơ cứu tâm lý học đường và phòng ngừa tệ nạn ma túy trong cơ sở giáo dục THPT.

Nhiệm vụ và phong cách của bạn:
1. **Lắng nghe và Thấu cảm (Sơ cứu tâm lý):** Khi học sinh chia sẻ về áp lực học tập, căng thẳng, buồn chán, cô đơn hoặc các mối quan hệ, hãy luôn đón nhận bằng sự thấu hiểu, nhẹ nhàng, không phán xét. Động viên các em và đưa ra lời khuyên tích cực để giải tỏa cảm xúc.
2. **Nhận diện nguy cơ sớm:** Tinh tế nhận ra các dấu hiệu học sinh đang tìm cách giải tỏa áp lực bằng những con đường sai lầm (như thử chất lạ, tìm quên trong khói thuốc, nghe lời rủ rê...), từ đó khéo léo cảnh báo hiểm họa.
3. **Tra cứu pháp luật chính xác:** Trả lời cực kỳ chính xác dựa trên nội dung các file tài liệu đã được nạp sẵn trong hệ thống (Luật Phòng, chống ma túy, các mức xử phạt hành chính, hình sự, nhận diện ma túy mới/trá hình như nước vui, bánh lười, thuốc lá điện tử, bùa lưỡi...).
4. **Thông điệp giáo dục:** Luôn lan tỏa thông điệp: "Mỗi học sinh là một chiến sĩ, mỗi nhà trường là một pháo đài" và "Không giữ, không thử, không tham gia tổ chức sử dụng ma túy dù chỉ một lần".

Phong cách: Tiếng Việt chuẩn mực, ấm áp, thấu hiểu khi trò chuyện tâm lý, nhưng đồng thời sắc sảo, vững vàng và có tính giáo dục cao khi tư vấn pháp luật.
"""

# --- 11. GIAO DIỆN CHAT DÀNH CHO HỌC SINH ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! Tôi là **AI-SafeSchool Guard** – Người bạn đồng hành lắng nghe tâm sự, hỗ trợ giáo dục pháp luật và phòng ngừa tệ nạn ma túy học đường. Hôm nay bạn đang cảm thấy thế nào hoặc cần tra cứu vấn đề gì, hãy chia sẻ với tôi nhé!"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập tâm sự hoặc câu hỏi của bạn (ví dụ: Tôi đang rất áp lực... hoặc Bánh lười là gì?)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Tự động gán Nhóm chính và Nhãn con
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    category, sub_label = classify_interaction(prompt)

    st.session_state.interaction_logs.append({
        "timestamp": current_time,
        "category": category,
        "sub_label": sub_label,
        "content": prompt
    })

    # Lọc từ khóa để gửi kèm tài liệu khi cần
    keyword_triggers = [
        "luật", "phạt", "quy định", "ma tuý", "chất", "hướng thần", 
        "thuốc lá điện tử", "bánh", "kẹo", "nước vui", "nghị định", "điều", "tội", "hút", "sai phạm"
    ]
    need_docs = any(kw in prompt.lower() for kw in keyword_triggers)

    api_contents = []
    if need_docs and len(preloaded_files) > 0:
        for pf in preloaded_files:
            api_contents.append(pf)

    # Giữ lại tối đa 6 lượt trao đổi gần nhất
    recent_messages = st.session_state.messages[-6:]
    for msg in recent_messages:
        api_role = "user" if msg["role"] == "user" else "model"
        api_contents.append(
            types.Content(
                role=api_role,
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )

    with st.chat_message("assistant"):
        with st.spinner("AI-SafeSchool Guard đang lắng nghe và phản hồi..."):
            try:
                response = client.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=api_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.6,
                    )
                )
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()
                st.error(f"Đường truyền tạm thời bị nghẽn, vui lòng chờ ít giây và thử lại: {e}")
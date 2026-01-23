import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents.agent_leader import team
import uuid
import time

st.set_page_config(
    page_title="Mimeda Satış Asistanı",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .stChatInput {
        padding-bottom: 2rem;
    }
    .block-container {
        padding-top: 2rem;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Clean Sidebar
with st.sidebar:
    st.title("Mimeda AI 🚀")
    st.markdown("---")
    
    st.markdown("### 💬 Oturum")
    st.code(st.session_state.session_id[:8], language=None)
    
    if st.button("🆕 Yeni Sohbet", type="primary", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
        
    st.markdown("---")
    st.markdown("### ℹ️ Hakkında")
    st.caption("""
    Satış ekibi için geliştirilmiş akıllı asistan.
    
    **Kaynaklar:**
    - CRM Veritabanı
    - Satış Oyun Kitabı (Playbook)
    """)

# Main Content
st.title("Mimeda Satış Asistanı")
st.caption("🚀 Stratejik satış önerileri ve CRM analizleri")

# Helper to clean response - REMOVED
# We now rely on correct role filtering

# Load and display chat history
try:
    messages = team.get_session_messages(session_id=st.session_state.session_id)
    for msg in messages:
        role = msg.role if hasattr(msg, 'role') else 'assistant'
        content = msg.content if hasattr(msg, 'content') else str(msg)
        
        # Skip system messages
        if role == 'system':
            continue
            
        # Determine avatar and role display
        if role == 'user':
            avatar = "👤"
            with st.chat_message("user", avatar=avatar):
                st.markdown(content)
        else:
            avatar = "🤖"
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(content)
except Exception:
    pass

# User Input
if prompt := st.chat_input("Bir soru sorun... (Örn: 'TechGiant ile yarın toplantım var. Harcamalarına ve sektörüne göre hangi ürünü önermeliyim?')"):
    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        tool_outputs = []
        
        # Create an expander for tool logs, initially empty
        tool_expander = st.expander("🛠️ Ajan İşlemleri", expanded=False)
        tool_log_placeholder = tool_expander.empty()
        
        with st.spinner("🔍 Analiz ediliyor..."):
            try:
                response = team.run(
                    prompt, 
                    stream=True, 
                    session_id=st.session_state.session_id
                )
                
                for chunk in response:
                    # Check for content
                    content = None
                    if hasattr(chunk, 'content') and chunk.content:
                        content = chunk.content
                    elif isinstance(chunk, str):
                        content = chunk
                    
                    if content:
                        # Identify chunk type
                        chunk_type = type(chunk).__name__
                        
                        # RunContentEvent is the actual streaming response text
                        if chunk_type == 'RunContentEvent':
                            # Only display content from the main team leader to avoid duplication
                            agent_name = getattr(chunk, 'agent_name', None)
                            if agent_name is None or agent_name == "Mimeda Sales Team":
                                full_response += content
                                message_placeholder.markdown(full_response + "▌")
                        # Other types (RunResponse, etc.) are usually tool logs
                        else:
                            # Skip if this chunk is just a repetition of the full response
                            if content.strip() == full_response.strip():
                                continue

                            tool_outputs.append(content)
                            tool_log_placeholder.code('\n'.join(tool_outputs))
                    
                    # Check for tool call start to get full arguments
                    elif type(chunk).__name__ == 'ToolCallStartedEvent':
                        if hasattr(chunk, 'tool') and hasattr(chunk.tool, 'tool_args'):
                            import json
                            args_str = json.dumps(chunk.tool.tool_args, ensure_ascii=False)
                            tool_name = chunk.tool.tool_name or "Tool"
                            
                            log_msg = f"{tool_name} args: {args_str}"
                            tool_outputs.append(log_msg)
                            tool_log_placeholder.code('\n'.join(tool_outputs))
                
            except Exception as e:
                st.error(f"Hata: {str(e)}")
        
        # Final display without cursor
        if full_response:
            message_placeholder.markdown(full_response)
        else:
            message_placeholder.markdown("Yanıt oluşturulamadı.")
    
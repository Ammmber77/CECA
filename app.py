import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI

st.set_page_config(
    page_title="CECA 中英课程对齐助手",
    page_icon="📚",
    layout="wide"
)

st.title("CECA 中英课程对齐助手")
st.caption("Chinese-English Course Alignment Assistant — 上传英方课程PDF,点击可获得中文对齐结果")

with st.sidebar:
    st.header("设置 ^-^")
    api_key = st.text_input(
        "大模型 API Key",
        type="password",
        help="输入你的API Key，支持OpenAI兼容接口"
    )
    api_base = st.text_input(
        "API Base URL（可选）",
        value="https://api.deepseek.com/v1",
        help="如果使用第三方兼容API，修改此地址"
    )
    model_name = st.text_input(
        "模型名称",
        value="deepseek-chat",
        help="如使用第三方API，填入对应模型名"
    )
    st.divider()
    st.markdown("**使用说明**")
    st.markdown("1. 上传英方课程PDF\n2. 左侧浏览原文段落\n3. 点击段落旁的按钮翻译\n4. 右侧查看对齐结果")

if "pdf_text_blocks" not in st.session_state:
    st.session_state.pdf_text_blocks = []
if "selected_block" not in st.session_state:
    st.session_state.selected_block = None
if "translation_result" not in st.session_state:
    st.session_state.translation_result = None
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False

uploaded_file = st.file_uploader(
    " 上传英方课程PDF",
    type=["pdf"],
    help="支持单次上传一个PDF文件"
)

if uploaded_file is not None and not st.session_state.pdf_uploaded:
    with st.spinner("正在解析PDF..."):
        reader = PdfReader(uploaded_file)
        blocks = []
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                if not paragraphs:
                    
                    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 20]
                for para in paragraphs:
                    blocks.append({
                        "page": page_num + 1,
                        "text": para
                    })
        st.session_state.pdf_text_blocks = blocks
        st.session_state.pdf_uploaded = True
        st.session_state.selected_block = None
        st.session_state.translation_result = None
    st.success(f"解析完成，共 {len(st.session_state.pdf_text_blocks)} 个段落")


if st.session_state.pdf_uploaded:
    col_left, col_right = st.columns([1, 1], gap="medium")

    
    with col_left:
        st.subheader("英方原文")
        for i, block in enumerate(st.session_state.pdf_text_blocks):
            
            is_selected = (st.session_state.selected_block == i)
            label = f"第{i+1}段 · 第{block['page']}页"
            if is_selected:
                label = "▶ " + label

            with st.container(border=is_selected):
                st.markdown(f"**{label}**")
                
                preview = block["text"][:200] + ("..." if len(block["text"]) > 200 else "")
                st.caption(preview)

                if st.button(f"翻译这一段", key=f"btn_{i}"):
                    st.session_state.selected_block = i
                    st.session_state.translation_result = None  

    
    with col_right:
        st.subheader("对齐结果")

        if st.session_state.selected_block is None:
            st.info("请在左侧点击「翻译这一段」按钮")

        else:
            selected = st.session_state.pdf_text_blocks[st.session_state.selected_block]

            
            with st.expander("原文", expanded=True):
                st.write(selected["text"])

            if st.session_state.translation_result is None:
                if not api_key:
                    st.warning("请在左侧设置中填入API Key")
                else:
                    with st.spinner("正在生成翻译和对齐结果..."):
                        try:
                            client = OpenAI(
                                api_key=api_key,
                                base_url="https://api.deepseek.com/v1"
                            )

                            prompt = f"""你是一个中英课程对齐助手，服务于需要的学生。
用户提供了一段英方课程的原文，请你完成以下三件事：

1. **中文翻译**：将原文翻译成学术语境下的中文，不是逐字直译，而是符合中国大学课程语境的表达。

2. **术语对照表**：从原文中提取3-8个关键术语，给出：
   - 英文术语
   - 中文对应词
   - 简要解释（一句话说明这个概念在中文课程中怎么讲）

3. **课程语境提示**：用2-3句话说明这段内容在中文课程体系中可能对应哪个知识点，以及中英教学在这个概念上的侧重点差异。

原文如下：
---
{selected['text']}
---

请按以下格式输出：

## 中文翻译
（翻译内容）

## 术语对照
| 英文术语 | 中文对应 | 课程语境解释 |
|---------|---------|-------------|
| ... | ... | ... |

## 课程语境提示
（提示内容）"""

                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {"role": "system", "content": "你是一个专业的中英课程对齐助手，擅长将英方课程材料翻译为中文并建立术语对照。"},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.3
                            )

                            st.session_state.translation_result = response.choices[0].message.content

                        except Exception as e:
                            st.error(f"API调用失败：{str(e)}")
                            st.session_state.translation_result = None

        
            if st.session_state.translation_result:
                st.markdown(st.session_state.translation_result)

    
                st.download_button(
                    label="下载对齐结果",
                    data=st.session_state.translation_result,
                    file_name=f"ceca_alignment_para{st.session_state.selected_block+1}.md",
                    mime="text/markdown"
                )

else:

    st.info("请先上传一个英方课程PDF文件吧")
    st.markdown("""
    ### 关于 CECA
    
    CECA（中英课程对齐助手）
    
    **它解决什么问题？**
    学生同时面对英方英文讲义和中文课程体系，术语不统一、概念难对应。
    
    **它怎么用？**
    上传英方课程PDF → 左侧浏览原文段落 → 点击段落翻译 → 右侧获得中文翻译、术语对照和课程语境解释。
    
    **它和普通翻译器有什么不同？**
    不同于逐字翻译，ceca结合课程语境，帮你理解英方材料在中文课程体系中的含义。
    """)
import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI

st.set_page_config(
    page_title="CECA 中英课程对齐助手",
    page_icon="📚",
    layout="wide"
)


SAMPLE_TEXT_BLOCKS = [
    {
        "page": 1,
        "text": "The study of economics is guided by a few big ideas. These ideas are central to the economist's view of the world and are useful in understanding how markets work, how governments can improve market outcomes, and how the economy as a whole functions. In this chapter, we look at the Ten Principles of Economics. Don't worry if you don't understand them all at first. We explore these ideas more fully in later chapters."
    },
    {
        "page": 2,
        "text": "The word economy comes from the Greek word oikonomos, which means 'one who manages a household.' At first, this origin might seem peculiar. But in fact, households and economies have much in common. A household faces many decisions. It must decide which household members do which tasks and what each member receives in return. In short, a household must allocate its scarce resources among its various members, taking into account each member's abilities, efforts, and desires."
    },
    {
        "page": 3,
        "text": "One classic trade-off is between 'guns and butter.' The more a society spends on national defense (guns) to protect itself from foreign aggressors, the less it can spend on consumer goods (butter) to raise its standard of living. Also important in modern society is the trade-off between a clean environment and a high level of income. Laws that require firms to reduce pollution raise the cost of producing goods and services."
    },
    {
        "page": 4,
        "text": "The opportunity cost of an item is what you give up to get that item. When making any decision, decision makers should take into account the opportunity costs of each possible action. In fact, they usually do. College athletes who can earn millions dropping out of school and playing professional sports are well aware that their opportunity cost of attending college is very high. Not surprisingly, they often decide that the benefit of a college education is not worth the cost."
    },
    {
        "page": 5,
        "text": "The marginal benefit of an extra unit of a good depends on how many units a person already has. Water is essential, but the marginal benefit of an extra cup is small because water is plentiful. By contrast, no one needs diamonds to survive, but because diamonds are so rare, the marginal benefit of an extra diamond is large. A rational decision maker takes an action if and only if the action's marginal benefit exceeds its marginal cost."
    }
]

st.markdown("""
<style>
    h1, h2, h3 {
        color: #003366 !important;
    }
    .stButton>button {
        background-color: #003366;
        color: white;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #00509e;
    }
</style>
""", unsafe_allow_html=True)

st.title("CECA 中英课程对齐助手")
col_status1, col_status2 = st.columns([3, 1])
with col_status2:
    st.success("模型已连接")
st.info("tip：若页面出现 'Zzz' 休眠提示，点击 'Yes, get this app back up' 唤醒^-^")
st.caption("Chinese-English Course Alignment Assistant — 上传英方课程PDF,点击可获得中文对齐结果")

with st.sidebar:
    st.header("设置 ^-^")
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except (KeyError, FileNotFoundError):
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

    st.divider()
    st.markdown("**快速演示**")
    if st.button(" 一键加载示例教材", use_container_width=True):
        st.session_state.pdf_text_blocks = SAMPLE_TEXT_BLOCKS
        st.session_state.pdf_uploaded = True
        st.session_state.selected_block = 0  
        st.session_state.translation_result = None
        st.rerun()

with st.sidebar:
    st.divider()
    with st.expander("开发日志"):
        st.markdown("""
        - **v1.0 (2026.10.04)**：初始版本上线
        - **v1.1 (2026.10.06)**：优化UI，新增加载动画、错误界面、唤醒提示功能。
        - **v2.0 (规划中)**：引入本地术语库匹配、课程管理、一键导出。
        """)

with st.sidebar:
    st.divider()
    with st.expander("关于作者"):
        st.markdown("""
        **Ammmber77**| 2026级^-^
        独立完成从需求分析、前端开发、后端逻辑到云端部署的全流程
        核心为Prompt工程、PDF结构化切分算法、及云端部署的Secrets安全机制
        由于技术栈尚浅，本项目参考了开源Streamlit框架的基础搭建逻辑（叠甲算是
        """)

# ===== 初始化 session state =====
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


if uploaded_file is not None:

    if st.session_state.get("last_upload_name") != uploaded_file.name:
        st.session_state.last_upload_name = uploaded_file.name
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
                    with st.spinner("正在生成翻译和对齐结果^-^..."):
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
                            error_msg = str(e)
                            if "Authentication" in error_msg or "api_key" in error_msg:
                                st.error("API 密钥失效或未配置，请检查云端 Secrets 设置。")
                            elif "timeout" in error_msg.lower():
                                st.warning("网络超时^-^")
                            elif "rate limit" in error_msg.lower():
                                st.warning("请求过于频繁^-^")
                            else:
                                st.error(f"API调用失败：{error_msg}")
                                st.session_state.translation_result = None

            if st.session_state.translation_result:
                st.markdown(st.session_state.translation_result)

                st.download_button(
                    label="下载对齐结果",
                    data=st.session_state.translation_result,
                    file_name=f"CECA_Translation{st.session_state.selected_block+1}.txt",
                    mime="text/plain"
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
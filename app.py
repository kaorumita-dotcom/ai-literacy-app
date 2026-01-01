import streamlit as st
import database as db
from datetime import datetime
import os

# ページ設定
st.set_page_config(
    page_title="AI学習チェックリスト",
    page_icon="✅",
    layout="wide"
)

# データベース初期化
db.init_database()

# チェックリストデータ
CHECKLIST_CATEGORIES = {
    "AIの基本理解": [
        "AIとは何か説明できる",
        "生成AIと従来のAIの違いがわかる",
        "ChatGPT・Claude・Geminiを知っている",
        "AIは予測していると理解",
        "AIにできること・できないことがわかる"
    ],
    "基本操作": [
        "生成AIを開ける",
        "質問を送信できる",
        "回答を読める",
        "新しい会話を始められる",
        "履歴を見られる"
    ],
    "質問の仕方": [
        "具体的に質問すると良いと知っている",
        "「教えて」と質問できる",
        "「簡単に説明して」と頼める",
        "「例を挙げて」と頼める",
        "続けて質問できる"
    ],
    "実生活での活用": [
        "レシピを聞ける",
        "健康相談できる",
        "旅行計画を相談できる",
        "文章を手伝ってもらえる",
        "言葉の意味を調べられる"
    ],
    "安全な使い方": [
        "個人情報を入力しない",
        "AIが間違うことがあると理解",
        "重要な判断はAIだけに頼らない",
        "詐欺判別に使える",
        "困ったら人に相談"
    ],
    "発展的な使い方": [
        "複数回やりとりできる",
        "役割を与えられる",
        "画像を見せられる",
        "学ぶ意欲がある",
        "他の人に教えられる"
    ]
}

# カスタムCSS（シニア向けの大きな文字とボタン - 改善版）
st.markdown("""
    <style>
    /* ========================================
       高齢者向けUI - 改善版CSS
       ======================================== */

    /* 全体の文字サイズを大きく */
    .main {
        font-size: 22px;
    }

    /* タイトルを大きく */
    h1 {
        font-size: 52px !important;
        font-weight: bold !important;
        color: #1565c0 !important;
        margin-bottom: 30px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }

    /* サブタイトルを大きく */
    h2 {
        font-size: 36px !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
        margin-top: 30px !important;
        margin-bottom: 25px !important;
        border-bottom: 3px solid #1565c0;
        padding-bottom: 10px;
    }

    h3 {
        font-size: 30px !important;
        font-weight: bold !important;
        color: #34495e !important;
        margin-top: 25px !important;
        margin-bottom: 20px !important;
    }

    /* チェックボックスのラベルを大きく */
    .stCheckbox label {
        font-size: 24px !important;
        font-weight: 500 !important;
        padding: 12px 0 !important;
    }

    /* チェックボックス自体を大きく */
    .stCheckbox input[type="checkbox"] {
        width: 35px !important;
        height: 35px !important;
        margin-right: 18px !important;
    }

    /* ========================================
       ボタンスタイル - 高齢者向け改善版
       ======================================== */

    /* 基本ボタン - 大きく、見やすく */
    .stButton button {
        font-size: 26px !important;
        padding: 20px 45px !important;
        font-weight: bold !important;
        border-radius: 15px !important;
        min-height: 80px !important;
        border: 3px solid transparent !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }

    /* ボタンホバー効果 */
    .stButton button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
    }

    /* ボタンクリック時の効果 */
    .stButton button:active {
        transform: translateY(2px) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%) !important;
    }

    /* プライマリボタン（主要アクション） */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%) !important;
        color: white !important;
        border: 3px solid #0d47a1 !important;
    }

    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%) !important;
    }

    /* セカンダリボタン */
    .stButton button[kind="secondary"] {
        background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%) !important;
        color: #333 !important;
        border: 3px solid #9e9e9e !important;
    }

    /* プログレスバーを大きく */
    .stProgress > div > div {
        height: 45px !important;
        border-radius: 10px !important;
    }

    /* メトリクスを大きく */
    [data-testid="stMetricValue"] {
        font-size: 56px !important;
        font-weight: bold !important;
        color: #1565c0 !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 26px !important;
        font-weight: bold !important;
        color: #424242 !important;
    }

    /* カテゴリカードのスタイル */
    .category-card {
        background-color: #f8f9fa;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 35px;
        border: 4px solid #dee2e6;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* 達成済みカテゴリ */
    .category-completed {
        background-color: #d4edda;
        border: 4px solid #28a745;
    }

    /* コントラストの高い色使い */
    .stMarkdown {
        color: #212529 !important;
    }

    /* 進捗表示エリア */
    .progress-area {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 35px;
        border-radius: 20px;
        margin-bottom: 45px;
        border: 4px solid #1976d2;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* サイドバーのスタイル */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    [data-testid="stSidebar"] .stButton button {
        font-size: 22px !important;
        padding: 18px 25px !important;
        min-height: 70px !important;
        margin-bottom: 10px !important;
    }

    /* ========================================
       入力フィールドを大きく・目立つように
       ======================================== */
    
    /* 入力欄を大きく - ボーダーを細めに */
    input[type="text"], 
    input[type="email"], 
    input[type="password"],
    input[type="number"],
    .stTextInput input,
    .stTextInput > div > div > input,
    [data-testid="stTextInput"] input,
    [data-baseweb="input"] input {
        font-size: 22px !important;
        padding: 12px 15px !important;
        border: 2px solid #1976d2 !important;
        border-radius: 10px !important;
        background-color: #ffffff !important;
        color: #333333 !important;
    }

    /* テキストエリアも大きく */
    textarea,
    .stTextArea textarea,
    [data-testid="stTextArea"] textarea {
        font-size: 22px !important;
        padding: 12px 15px !important;
        border: 2px solid #1976d2 !important;
        border-radius: 10px !important;
        background-color: #ffffff !important;
        color: #333333 !important;
    }

    /* プレースホルダーを見やすく */
    input::placeholder, 
    textarea::placeholder,
    .stTextInput input::placeholder, 
    .stTextArea textarea::placeholder {
        color: #999999 !important;
        font-size: 20px !important;
    }

    /* フォーカス時のスタイル */
    input:focus, 
    textarea:focus,
    .stTextInput input:focus, 
    .stTextArea textarea:focus {
        border-color: #ff9800 !important;
        border-width: 3px !important;
        box-shadow: 0 0 0 2px rgba(255, 152, 0, 0.3) !important;
        outline: none !important;
    }

    /* ラベルを青色で大きく */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stDateInput label,
    .stTimeInput label,
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #1565c0 !important;
        margin-bottom: 5px !important;
    }

    /* 日付・時刻入力も見やすく */
    .stDateInput input, 
    .stTimeInput input,
    [data-testid="stDateInput"] input,
    [data-testid="stTimeInput"] input {
        font-size: 20px !important;
        padding: 10px !important;
        border: 2px solid #1976d2 !important;
        border-radius: 10px !important;
        background-color: #ffffff !important;
    }

    /* チェックボックスも見やすく */
    .stCheckbox label {
        font-size: 24px !important;
        padding: 15px !important;
    }

    .stCheckbox label span {
        font-size: 24px !important;
    }

    /* テーブルのスタイル */
    .dataframe {
        font-size: 22px !important;
    }

    /* グループカード */
    .group-card {
        background-color: #fff;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        border: 3px solid #dee2e6;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .group-card:hover {
        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }

    /* ========================================
       Zoom参加ボタン - 特大サイズ
       ======================================== */
    .zoom-join-btn {
        background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%) !important;
        color: white !important;
        font-size: 32px !important;
        font-weight: bold !important;
        padding: 30px 60px !important;
        border-radius: 20px !important;
        border: 4px solid #0d47a1 !important;
        text-decoration: none !important;
        display: inline-block !important;
        text-align: center !important;
        min-width: 350px !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        transition: all 0.3s ease !important;
    }

    .zoom-join-btn:hover {
        background: linear-gradient(135deg, #1976d2 0%, #0d47a1 100%) !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3) !important;
    }

    /* ========================================
       操作手順表示用のスタイル
       ======================================== */
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
        color: white;
        font-size: 28px;
        font-weight: bold;
        border-radius: 50%;
        margin-right: 15px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.2);
    }

    .step-container {
        display: flex;
        align-items: center;
        padding: 20px;
        background-color: #fff8e1;
        border-radius: 15px;
        margin-bottom: 30px;
        border-left: 5px solid #ff9800;
    }

    .step-text {
        font-size: 24px;
        color: #333;
    }

    /* 入力フィールドの上の余白を確保 */
    .stTextInput, .stTextArea, .stSelectbox, .stDateInput, .stTimeInput {
        margin-top: 10px !important;
        margin-bottom: 25px !important;
    }

    /* ========================================
       成功・エラーメッセージ強調
       ======================================== */
    .stSuccess {
        font-size: 24px !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }

    .stError {
        font-size: 24px !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }

    .stWarning {
        font-size: 24px !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }

    .stInfo {
        font-size: 24px !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }

    /* スピナー（処理中表示）を目立たせる */
    .stSpinner > div {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #1565c0 !important;
    }

    .stSpinner > div > div {
        border-width: 4px !important;
    }

    /* タブのスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 22px !important;
        font-weight: bold !important;
        padding: 15px 25px !important;
        border-radius: 10px 10px 0 0 !important;
    }

    /* エクスパンダーのスタイル */
    .streamlit-expanderHeader {
        font-size: 24px !important;
        font-weight: bold !important;
        padding: 15px !important;
    }

    </style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'
if 'success_message' not in st.session_state:
    st.session_state.success_message = None
if 'success_type' not in st.session_state:
    st.session_state.success_type = None

# 進捗計算
def calculate_progress(checklist_data):
    """全体の進捗とカテゴリごとの進捗を計算"""
    total_items = sum(len(items) for items in CHECKLIST_CATEGORIES.values())
    checked_items = sum(1 for item in checklist_data.values() if item)

    category_progress = {}
    for category, items in CHECKLIST_CATEGORIES.items():
        category_total = len(items)
        category_checked = sum(1 for item in items if checklist_data.get(f"{category}_{item}", False))
        category_progress[category] = {
            'checked': category_checked,
            'total': category_total,
            'percentage': (category_checked / category_total * 100) if category_total > 0 else 0
        }

    overall_percentage = (checked_items / total_items * 100) if total_items > 0 else 0

    return {
        'total': total_items,
        'checked': checked_items,
        'percentage': overall_percentage,
        'categories': category_progress
    }

# 操作手順を表示するヘルパー関数
def show_step(number, text):
    """操作手順を番号付きで表示"""
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        padding: 20px;
        background-color: #fff8e1;
        border-radius: 15px;
        margin-top: 30px;
        margin-bottom: 10px;
        border-left: 5px solid #ff9800;
    ">
        <span style="
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
            color: white;
            font-size: 28px;
            font-weight: bold;
            border-radius: 50%;
            margin-right: 15px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.2);
            flex-shrink: 0;
        ">{number}</span>
        <span style="font-size: 24px; color: #333;">{text}</span>
    </div>
    """, unsafe_allow_html=True)
    # 余白を追加
    st.markdown("")

# 成功メッセージを大きく表示するヘルパー関数
def show_success_message(message, message_type="success"):
    """成功メッセージを大きく目立つように表示"""
    if message_type == "success":
        bg_color = "#d4edda"
        border_color = "#28a745"
        text_color = "#155724"
        icon = "🎉"
    elif message_type == "info":
        bg_color = "#d1ecf1"
        border_color = "#17a2b8"
        text_color = "#0c5460"
        icon = "ℹ️"
    else:
        bg_color = "#fff3cd"
        border_color = "#ffc107"
        text_color = "#856404"
        icon = "⚠️"

    st.markdown(f"""
    <div style="
        background-color: {bg_color};
        border: 5px solid {border_color};
        border-radius: 20px;
        padding: 30px;
        margin: 25px 0;
        text-align: center;
        animation: fadeIn 0.5s ease-in;
    ">
        <p style="font-size: 48px; margin: 0;">{icon}</p>
        <p style="font-size: 28px; font-weight: bold; color: {text_color}; margin: 15px 0;">
            {message}
        </p>
    </div>
    <style>
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: scale(0.9); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
    </style>
    """, unsafe_allow_html=True)

# セッション状態の成功メッセージを表示してクリア
def display_and_clear_success_message():
    """セッション状態に保存された成功メッセージを表示してクリア"""
    if st.session_state.success_message:
        show_success_message(
            st.session_state.success_message,
            st.session_state.success_type or "success"
        )
        st.balloons()
        # メッセージをクリア
        st.session_state.success_message = None
        st.session_state.success_type = None

# Zoom参加ボタンを表示するヘルパー関数
def show_zoom_join_button(zoom_url, zoom_passcode=None):
    """大きなZoom参加ボタンを表示"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 35px;
        border-radius: 20px;
        border: 4px solid #1976d2;
        margin: 25px 0;
        text-align: center;
    ">
        <h2 style="color: #1565c0; margin-bottom: 20px; font-size: 32px;">📹 Zoomミーティングに参加</h2>
    """, unsafe_allow_html=True)

    if zoom_passcode:
        st.markdown(f"""
        <p style="font-size: 24px; color: #333; margin-bottom: 20px;">
            🔑 <strong>パスコード：</strong> <span style="background-color: #fff; padding: 8px 15px; border-radius: 8px; font-size: 28px; font-weight: bold;">{zoom_passcode}</span>
        </p>
        """, unsafe_allow_html=True)

    st.markdown(f"""
        <a href="{zoom_url}" target="_blank" class="zoom-join-btn">
            🚀 ここをクリックしてZoomに参加
        </a>
        <p style="font-size: 20px; color: #666; margin-top: 20px;">
            ↑ このボタンを押すとZoomが開きます
        </p>
    </div>
    """, unsafe_allow_html=True)

# ログイン・登録画面
def show_auth_page():
    st.title("✅ AI学習チェックリスト")
    st.markdown("### シニアのためのAI活用ガイド")
    st.markdown("---")

    # 操作説明
    st.markdown("""
    <div style="
        background-color: #fff3e0;
        padding: 25px;
        border-radius: 15px;
        border: 3px solid #ff9800;
        margin-bottom: 30px;
    ">
        <h3 style="color: #e65100; margin-top: 0;">📌 はじめての方へ</h3>
        <p style="font-size: 22px; line-height: 1.8; color: #333;">
            <strong>① 新規登録タブ</strong>で、お名前・メールアドレス・パスワードを入力して登録してください。<br>
            <strong>② ログインタブ</strong>で、登録したメールアドレスとパスワードでログインしてください。
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 ログイン", "📝 新規登録"])

    with tab1:
        st.markdown("## 🔑 ログイン")
        st.markdown("")

        show_step(1, "メールアドレスを入力してください")
        email = st.text_input("メールアドレス", key="login_email", placeholder="例: yamada@example.com")

        show_step(2, "パスワードを入力してください")
        password = st.text_input("パスワード", type="password", key="login_password", placeholder="パスワードを入力")

        st.markdown("")
        show_step(3, "下の青いボタンを押してください")
        st.markdown("")

        if st.button("🔓 ログインする", key="login_button", type="primary", use_container_width=True):
            if email and password:
                user = db.authenticate_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success("✅ ログインしました！画面が切り替わります...")
                    st.rerun()
                else:
                    st.error("❌ メールアドレスまたはパスワードが間違っています")
            else:
                st.warning("⚠️ メールアドレスとパスワードを入力してください")

    with tab2:
        st.markdown("## 📝 新規登録")
        st.markdown("")

        show_step(1, "お名前を入力してください")
        name = st.text_input("お名前", key="register_name", placeholder="例: 山田 太郎")

        show_step(2, "メールアドレスを入力してください")
        email = st.text_input("メールアドレス", key="register_email", placeholder="例: yamada@example.com")

        show_step(3, "パスワードを決めてください（6文字以上）")
        password = st.text_input("パスワード", type="password", key="register_password", placeholder="6文字以上のパスワード")

        show_step(4, "同じパスワードをもう一度入力してください")
        password_confirm = st.text_input("パスワード（確認）", type="password", key="register_password_confirm", placeholder="同じパスワードを入力")

        show_step(5, "あなたの役割を選んでください")
        role = st.selectbox(
            "役割を選択",
            options=["participant", "host"],
            format_func=lambda x: "👤 参加者（学習する人）" if x == "participant" else "👑 ホスト（教える人・グループを作る人）",
            key="register_role"
        )

        st.markdown("")
        show_step(6, "下の青いボタンを押して登録してください")
        st.markdown("")

        if st.button("📝 登録する", key="register_button", type="primary", use_container_width=True):
            if not all([name, email, password, password_confirm]):
                st.warning("⚠️ すべての項目を入力してください")
            elif password != password_confirm:
                st.error("❌ パスワードが一致しません")
            elif len(password) < 6:
                st.warning("⚠️ パスワードは6文字以上にしてください")
            else:
                success, message = db.create_user(name, email, password, role)
                if success:
                    st.success(f"✅ {message}")
                    st.info("👆 上の「ログイン」タブからログインしてください")
                else:
                    st.error(f"❌ {message}")

# ダッシュボード
def show_dashboard():
    user = st.session_state.user

    st.title(f"👋 こんにちは、{user['name']}さん")
    st.markdown(f"**役割:** {'👑 ホスト（教える人）' if user['role'] == 'host' else '👤 参加者（学習する人）'}")

    # 成功メッセージがあれば表示
    display_and_clear_success_message()

    st.markdown("---")

    # チェックリスト進捗
    checklist_data = db.load_user_checklist(user['id'])
    progress = calculate_progress(checklist_data)

    st.markdown('<div class="progress-area">', unsafe_allow_html=True)
    st.markdown("## 📊 あなたの学習進捗")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="達成項目",
            value=f"{progress['checked']} / {progress['total']}"
        )

    with col2:
        st.metric(
            label="達成率",
            value=f"{progress['percentage']:.1f}%"
        )

    with col3:
        completed_categories = sum(1 for cat_prog in progress['categories'].values() if cat_prog['percentage'] == 100)
        st.metric(
            label="完了カテゴリ",
            value=f"{completed_categories} / {len(CHECKLIST_CATEGORIES)}"
        )

    st.progress(progress['percentage'] / 100)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # グループ情報
    st.markdown("## 👥 所属グループ")

    groups = db.get_groups_by_member(user['id'])

    if groups:
        for group in groups:
            st.markdown(f'<div class="group-card">', unsafe_allow_html=True)
            st.markdown(f"### 📁 {group['name']}")
            if group['description']:
                st.markdown(f"**説明:** {group['description']}")
            st.markdown(f"**ホスト:** {group['host_name']}")
            st.markdown(f"**メンバー数:** {group['member_count']}名")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📭 まだグループに参加していません")

    st.markdown("---")

    # ホストの場合、自分が作成したグループを表示
    if user['role'] == 'host':
        st.markdown("## 🎯 あなたが管理しているグループ")

        hosted_groups = db.get_groups_by_host(user['id'])

        if hosted_groups:
            for group in hosted_groups:
                st.markdown(f'<div class="group-card">', unsafe_allow_html=True)
                st.markdown(f"### 📁 {group['name']}")
                if group['description']:
                    st.markdown(f"**説明:** {group['description']}")
                st.markdown(f"**メンバー数:** {group['member_count']}名")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("📭 まだグループを作成していません")

    st.markdown("---")

    # ホストの場合：リマインダー送信が必要なミーティングをチェック
    if user['role'] == 'host':
        # リマインダーテーブルを初期化
        db.init_reminder_table()

        meetings_needing_reminder = db.get_meetings_needing_reminder(user['id'], hours_before=24)

        if meetings_needing_reminder:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
                color: white;
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 25px;
            ">
                <h2 style="margin: 0; color: white; font-size: 28px;">🔔 リマインダー送信のお知らせ</h2>
                <p style="margin: 10px 0 0 0; font-size: 20px;">
                    24時間以内に開催予定のミーティングがあります。参加者にリマインダーを送信しましょう！
                </p>
            </div>
            """, unsafe_allow_html=True)

            for meeting in meetings_needing_reminder:
                scheduled_dt = datetime.fromisoformat(meeting['scheduled_at'])
                hours_until = (scheduled_dt - datetime.now()).total_seconds() / 3600

                st.markdown(f"""
                <div class="group-card" style="border: 4px solid #ff9800; background-color: #fff3e0;">
                    <h3 style="color: #e65100;">⏰ {meeting['title']}</h3>
                    <p><strong>日時：</strong>{scheduled_dt.strftime('%Y年%m月%d日 %H:%M')}</p>
                    <p><strong>あと約{int(hours_until)}時間</strong>で開催</p>
                    <p><strong>参加者数：</strong>{meeting['participant_count']}名</p>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📧 リマインダーを送信", key=f"send_reminder_{meeting['id']}", type="primary", use_container_width=True):
                        with st.spinner("📤 リマインダーを送信中..."):
                            success, message, sent_count = db.send_auto_reminder(meeting['id'], 'reminder_24h')
                            if success:
                                st.success(f"✅ {message}")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                with col2:
                    if meeting.get('zoom_url'):
                        st.info(f"📹 Zoom設定済み")
                    else:
                        st.warning(f"⚠️ Zoom未設定")

                st.markdown("")

            # 一括送信ボタン
            if len(meetings_needing_reminder) > 1:
                st.markdown("---")
                if st.button("📨 全てのリマインダーを一括送信", type="primary", use_container_width=True):
                    with st.spinner("📤 リマインダーを一括送信中..."):
                        total_sent = 0
                        for meeting in meetings_needing_reminder:
                            success, message, sent_count = db.send_auto_reminder(meeting['id'], 'reminder_24h')
                            if success:
                                total_sent += sent_count
                        st.success(f"✅ {len(meetings_needing_reminder)}件のミーティングにリマインダーを送信しました！")
                        st.rerun()

            st.markdown("---")

    # 今後のミーティング予定（リマインダー）
    st.markdown("## 📅 今後のミーティング予定")

    upcoming_meetings = db.get_upcoming_meetings(user['id'], days_ahead=7)

    if upcoming_meetings:
        from datetime import datetime

        for meeting in upcoming_meetings:
            # 日数計算
            scheduled_dt = datetime.fromisoformat(meeting['scheduled_at'])
            now = datetime.now()
            days_until = (scheduled_dt - now).days

            # カードの色を日数によって変更
            if days_until <= 1:
                card_style = 'background-color: #fff3cd; border: 4px solid #ffc107;'  # 黄色（緊急）
                urgency_color = '#856404'
            elif days_until <= 3:
                card_style = 'background-color: #d1ecf1; border: 4px solid #17a2b8;'  # 青（近い）
                urgency_color = '#0c5460'
            else:
                card_style = 'background-color: #d4edda; border: 4px solid #28a745;'  # 緑（余裕あり）
                urgency_color = '#155724'

            st.markdown(f'<div class="group-card" style="{card_style}">', unsafe_allow_html=True)

            # リマインダーメッセージ
            if days_until == 0:
                reminder_text = "🔔 **本日開催！**"
            elif days_until == 1:
                reminder_text = "⏰ **明日開催！**"
            else:
                reminder_text = f"📆 **あと{days_until}日**"

            st.markdown(f"### {reminder_text} {meeting['title']}")
            st.markdown(f"**グループ:** {meeting['group_name']}")
            st.markdown(f"**日時:** {scheduled_dt.strftime('%Y年%m月%d日 %H:%M')}")
            st.markdown(f"**ホスト:** {meeting['host_name']}")

            # Zoom URLがある場合は参加ボタンを表示
            if meeting.get('zoom_url'):
                st.markdown("---")
                show_zoom_join_button(meeting['zoom_url'], meeting.get('zoom_passcode'))

            # 詳細を見るボタン
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📝 詳細を見る", key=f"view_meeting_{meeting['id']}", use_container_width=True):
                    st.session_state.selected_meeting = meeting['id']
                    st.session_state.page = 'meeting_detail'
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("")
    else:
        st.info("📭 今後7日間の予定はありません")

    # 招待通知
    invitations = db.get_user_invitations(user['email'])
    if invitations:
        st.markdown("---")
        st.markdown("## 📧 グループへの招待")

        for invitation in invitations:
            st.markdown(f'<div class="group-card" style="border: 4px solid #28a745; background-color: #d4edda;">', unsafe_allow_html=True)
            st.markdown(f"### 🎉 {invitation['group_name']} への招待")
            st.markdown(f"**説明:** {invitation['description']}")
            st.markdown(f"**招待者:** {invitation['invited_by_name']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ 参加する", key=f"accept_{invitation['id']}", type="primary", use_container_width=True):
                    success, message = db.accept_invitation(invitation['id'], user['id'])
                    if success:
                        st.success(f"🎉 {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            with col2:
                if st.button(f"❌ 辞退する", key=f"decline_{invitation['id']}", use_container_width=True):
                    success, message = db.decline_invitation(invitation['id'])
                    if success:
                        st.info(f"📝 {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

            st.markdown('</div>', unsafe_allow_html=True)

# チェックリストページ
def show_checklist_page():
    user = st.session_state.user

    st.title("✅ AI学習チェックリスト")
    st.markdown("### シニアのためのAI活用ガイド")

    # 操作説明
    st.markdown("""
    <div style="
        background-color: #e8f5e9;
        padding: 20px;
        border-radius: 15px;
        border: 3px solid #4caf50;
        margin-bottom: 25px;
    ">
        <p style="font-size: 22px; color: #2e7d32; margin: 0;">
            💡 <strong>使い方：</strong>できるようになった項目の □ をクリックして ✓ を付けましょう！
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ユーザーのチェックリストを読み込み
    checklist_data = db.load_user_checklist(user['id'])

    # 進捗表示
    progress = calculate_progress(checklist_data)

    st.markdown('<div class="progress-area">', unsafe_allow_html=True)
    st.markdown("## 📊 学習の進捗")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="達成項目",
            value=f"{progress['checked']} / {progress['total']}"
        )

    with col2:
        st.metric(
            label="達成率",
            value=f"{progress['percentage']:.1f}%"
        )

    with col3:
        completed_categories = sum(1 for cat_prog in progress['categories'].values() if cat_prog['percentage'] == 100)
        st.metric(
            label="完了カテゴリ",
            value=f"{completed_categories} / {len(CHECKLIST_CATEGORIES)}"
        )

    st.progress(progress['percentage'] / 100)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # カテゴリごとのチェックリスト
    for category, items in CHECKLIST_CATEGORIES.items():
        cat_progress = progress['categories'][category]
        is_completed = cat_progress['percentage'] == 100

        # カテゴリカード
        card_class = "category-completed" if is_completed else "category-card"
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

        # カテゴリヘッダー
        completion_icon = "🏆" if is_completed else "📝"
        st.markdown(f"### {completion_icon} {category}")

        # カテゴリの進捗
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(cat_progress['percentage'] / 100)
        with col2:
            st.markdown(f"**{cat_progress['checked']}/{cat_progress['total']} 項目**")

        st.markdown("")

        # チェックボックス
        for item in items:
            item_id = f"{category}_{item}"
            checked = checklist_data.get(item_id, False)

            new_checked = st.checkbox(item, value=checked, key=item_id)

            if new_checked != checked:
                db.save_checklist_item(user['id'], item_id, new_checked)
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("")

    st.markdown("---")

    if progress['percentage'] == 100:
        st.balloons()
        st.success("🎉🏆 おめでとうございます！すべての項目を達成しました！素晴らしいです！")

    # フッター
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #6c757d; font-size: 20px; padding: 25px;
                    background-color: #f8f9fa; border-radius: 15px;'>
            🌟 このチェックリストで、AIを楽しく学びましょう！<br>
            わからないことがあれば、いつでも周りの人に聞いてくださいね。
        </div>
    """, unsafe_allow_html=True)

# グループ管理ページ
def show_groups_page():
    user = st.session_state.user

    st.title("👥 グループ管理")
    st.markdown("---")

    if user['role'] == 'host':
        # ホストの場合：グループ作成とグループ管理
        tab1, tab2 = st.tabs(["➕ グループ作成", "📋 管理中のグループ"])

        with tab1:
            st.markdown("## ➕ 新しいグループを作成")
            st.markdown("")

            # 操作説明
            st.markdown("""
            <div style="
                background-color: #e3f2fd;
                padding: 20px;
                border-radius: 15px;
                border: 3px solid #2196f3;
                margin-bottom: 25px;
            ">
                <p style="font-size: 20px; color: #1565c0; margin: 0;">
                    💡 グループを作成すると、メンバーを招待してミーティングを開催できます。
                </p>
            </div>
            """, unsafe_allow_html=True)

            show_step(1, "グループ名を入力してください")
            group_name = st.text_input("グループ名", key="new_group_name", placeholder="例: AI学習会 第1グループ")

            show_step(2, "グループの説明を入力してください（任意）")
            group_description = st.text_area("グループの説明", key="new_group_description", height=150,
                                             placeholder="例: 毎週水曜日に集まってAIについて学ぶグループです")

            st.markdown("")
            show_step(3, "下のボタンを押してグループを作成してください")
            st.markdown("")

            if st.button("✨ グループを作成", type="primary", use_container_width=True):
                if group_name:
                    with st.spinner("🔄 グループを作成中です...しばらくお待ちください"):
                        import time
                        time.sleep(0.5)  # 処理中であることを視覚的に示す
                        success, message, group_id = db.create_group(group_name, group_description, user['id'])

                    if success:
                        # 成功メッセージを大きく表示
                        st.markdown(f"""
                        <div style="
                            background-color: #d4edda;
                            border: 5px solid #28a745;
                            border-radius: 20px;
                            padding: 40px;
                            margin: 30px 0;
                            text-align: center;
                        ">
                            <p style="font-size: 60px; margin: 0;">🎉</p>
                            <p style="font-size: 32px; font-weight: bold; color: #155724; margin: 20px 0;">
                                グループ「{group_name}」を作成しました！
                            </p>
                            <p style="font-size: 20px; color: #155724;">
                                3秒後に画面が切り替わります...
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                        import time
                        time.sleep(3)  # 3秒間メッセージを表示
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ グループ名を入力してください")

        with tab2:
            st.markdown("## 📋 管理中のグループ")
            st.markdown("")

            groups = db.get_groups_by_host(user['id'])

            if groups:
                for group in groups:
                    st.markdown(f'<div class="group-card">', unsafe_allow_html=True)
                    st.markdown(f"### 📁 {group['name']}")
                    if group['description']:
                        st.markdown(f"**説明:** {group['description']}")
                    st.markdown(f"**メンバー数:** {group['member_count']}名")

                    # メンバー表示
                    with st.expander("👥 メンバー一覧を見る"):
                        members = db.get_group_members(group['id'])
                        for member in members:
                            role_text = "👑 ホスト" if member['role'] == 'host' else "👤 参加者"
                            st.markdown(f"- {member['name']} ({member['email']}) - {role_text}")

                    # メンバー招待
                    with st.expander("📧 メンバーを招待する"):
                        st.markdown("招待したい方のメールアドレスを入力してください")
                        invite_email = st.text_input(
                            "招待するメールアドレス",
                            key=f"invite_email_{group['id']}",
                            placeholder="例: tanaka@example.com"
                        )
                        if st.button("📨 招待を送る", key=f"invite_button_{group['id']}", type="primary"):
                            if invite_email:
                                success, message = db.invite_to_group(group['id'], invite_email, user['id'])
                                if success:
                                    st.success(f"✅ {message}")
                                else:
                                    st.error(f"❌ {message}")
                            else:
                                st.warning("⚠️ メールアドレスを入力してください")

                    # グループメンバーの進捗表示
                    with st.expander("📊 メンバーの学習進捗を見る"):
                        progress_data = db.get_group_progress(group['id'])
                        if progress_data:
                            for member_progress in progress_data:
                                completed = member_progress['completed_items']
                                total = 30  # 全チェックリスト項目数
                                percentage = (completed / total * 100) if total > 0 else 0

                                st.markdown(f"**{member_progress['name']}**")
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.progress(percentage / 100)
                                with col2:
                                    st.markdown(f"{completed}/{total} 項目")
                                st.markdown("")

                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown("")
            else:
                st.info("📭 まだグループを作成していません。「グループ作成」タブから作成してください。")

    else:
        # 参加者の場合：所属グループの表示
        st.markdown("## 👥 あなたが参加しているグループ")
        st.markdown("")

        groups = db.get_groups_by_member(user['id'])

        if groups:
            for group in groups:
                st.markdown(f'<div class="group-card">', unsafe_allow_html=True)
                st.markdown(f"### 📁 {group['name']}")
                if group['description']:
                    st.markdown(f"**説明:** {group['description']}")
                st.markdown(f"**ホスト:** {group['host_name']}")
                st.markdown(f"**メンバー数:** {group['member_count']}名")

                # メンバー表示
                with st.expander("👥 メンバー一覧を見る"):
                    members = db.get_group_members(group['id'])
                    for member in members:
                        role_text = "👑 ホスト" if member['role'] == 'host' else "👤 参加者"
                        st.markdown(f"- {member['name']} - {role_text}")

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")
        else:
            st.info("📭 まだグループに参加していません。ホストからの招待をお待ちください。")

# ミーティング管理ページ
def show_meetings_page():
    user = st.session_state.user

    st.title("📹 ミーティング")
    st.markdown("---")

    # タブで機能を分割
    if user['role'] == 'host':
        tab1, tab2 = st.tabs(["📋 ミーティング一覧", "➕ 新規作成"])

        with tab1:
            show_meetings_list(user)

        with tab2:
            show_create_meeting(user)
    else:
        show_meetings_list(user)

def show_meetings_list(user):
    """ミーティング一覧を表示"""
    st.markdown("## 📋 参加するミーティング")
    st.markdown("")

    # 成功メッセージがあれば表示
    display_and_clear_success_message()

    meetings = db.get_meetings_by_user(user['id'])

    if meetings:
        for meeting in meetings:
            st.markdown(f'<div class="group-card">', unsafe_allow_html=True)
            st.markdown(f"### 📹 {meeting['title']}")

            if meeting['description']:
                st.markdown(f"**説明:** {meeting['description']}")

            st.markdown(f"**グループ:** {meeting['group_name']}")
            st.markdown(f"**ホスト:** {meeting['host_name']}")
            st.markdown(f"**参加者数:** {meeting['participant_count']}名")

            if meeting['scheduled_at']:
                from datetime import datetime
                try:
                    scheduled_dt = datetime.fromisoformat(meeting['scheduled_at'])
                    st.markdown(f"**日時:** {scheduled_dt.strftime('%Y年%m月%d日 %H:%M')}")
                except:
                    st.markdown(f"**日時:** {meeting['scheduled_at']}")

            # Zoom URLがある場合は参加ボタンを表示
            if meeting.get('zoom_url'):
                st.markdown("---")
                show_zoom_join_button(meeting['zoom_url'], meeting.get('zoom_passcode'))

            # 議事録表示
            recording = db.get_recording_by_meeting(meeting['id'])

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 詳細・議事録を見る", key=f"view_minutes_{meeting['id']}", type="primary", use_container_width=True):
                    st.session_state.selected_meeting = meeting['id']
                    st.session_state.page = 'meeting_detail'
                    st.rerun()

            with col2:
                if recording:
                    st.success("✅ 議事録あり")
                else:
                    st.info("📝 議事録なし")

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("")
    else:
        st.info("📭 参加予定のミーティングはありません")

def show_create_meeting(user):
    """ミーティング作成フォーム（Zoom連携対応）"""
    st.markdown("## ➕ 新しいミーティングを作成")
    st.markdown("")

    # ホストが管理しているグループを取得
    groups = db.get_groups_by_host(user['id'])

    if not groups:
        st.warning("⚠️ ミーティングを作成するには、まずグループを作成してください")
        if st.button("📁 グループを作成する", type="primary"):
            st.session_state.page = 'groups'
            st.rerun()
        return

    # 操作説明
    st.markdown("""
    <div style="
        background-color: #e3f2fd;
        padding: 20px;
        border-radius: 15px;
        border: 3px solid #2196f3;
        margin-bottom: 25px;
    ">
        <p style="font-size: 20px; color: #1565c0; margin: 0;">
            💡 ミーティングを作成すると、グループの全員に自動的に参加権限が付与されます。<br>
            Zoom URLを設定すると、参加者が簡単にZoomに参加できるようになります。
        </p>
    </div>
    """, unsafe_allow_html=True)

    # グループ選択
    show_step(1, "グループを選択してください")
    group_options = {g['id']: f"{g['name']} ({g['member_count']}名)" for g in groups}
    selected_group_id = st.selectbox(
        "グループを選択",
        options=list(group_options.keys()),
        format_func=lambda x: group_options[x],
        key="meeting_group"
    )

    show_step(2, "ミーティングのタイトルを入力してください")
    meeting_title = st.text_input("ミーティングタイトル", key="meeting_title",
                                  placeholder="例: 第3回 AI学習会")

    show_step(3, "ミーティングの説明を入力してください（任意）")
    meeting_description = st.text_area("ミーティングの説明", key="meeting_description", height=100,
                                       placeholder="例: 今回はChatGPTの使い方を学びます")

    show_step(4, "日時を設定してください")
    col1, col2 = st.columns(2)
    with col1:
        meeting_date = st.date_input("日付", key="meeting_date")
    with col2:
        meeting_time = st.time_input("時刻", key="meeting_time")

    st.markdown("---")

    # Zoom設定セクション
    st.markdown("""
    <div style="
        background-color: #e3f2fd;
        padding: 25px;
        border-radius: 15px;
        border: 3px solid #2196f3;
        margin: 20px 0;
    ">
        <h3 style="color: #1565c0; margin-top: 0;">📹 Zoom設定（任意）</h3>
        <p style="font-size: 18px; color: #333;">
            ZoomのURLを入力すると、参加者が簡単にZoomに参加できるボタンが表示されます。
        </p>
    </div>
    """, unsafe_allow_html=True)

    show_step(5, "Zoom URLを入力してください（任意）")
    zoom_url = st.text_input("Zoom URL", key="meeting_zoom_url",
                             placeholder="例: https://zoom.us/j/1234567890")

    col_zoom1, col_zoom2 = st.columns(2)
    with col_zoom1:
        zoom_meeting_id = st.text_input("ZoomミーティングID（任意）", key="meeting_zoom_id",
                                        placeholder="例: 123 456 7890")
    with col_zoom2:
        zoom_passcode = st.text_input("Zoomパスコード（任意）", key="meeting_zoom_passcode",
                                      placeholder="例: abc123")

    st.markdown("---")
    show_step(6, "招待メールを送信するか選択してください")

    send_invitation = st.checkbox(
        "✉️ 参加者全員に招待メールを自動送信する（Zoom情報含む）",
        value=True,
        key="send_invitation_email"
    )

    st.markdown("")
    show_step(7, "下のボタンを押してミーティングを作成してください")
    st.markdown("")

    if st.button("✨ ミーティングを作成", type="primary", use_container_width=True):
        if meeting_title and selected_group_id:
            with st.spinner("🔄 ミーティングを作成中です...しばらくお待ちください"):
                import time
                time.sleep(0.5)  # 処理中であることを視覚的に示す

                from datetime import datetime
                scheduled_at = datetime.combine(meeting_date, meeting_time).isoformat()

                success, message, meeting_id = db.create_meeting(
                    meeting_title,
                    meeting_description,
                    selected_group_id,
                    user['id'],
                    scheduled_at,
                    zoom_url if zoom_url else None,
                    zoom_meeting_id if zoom_meeting_id else None,
                    zoom_passcode if zoom_passcode else None
                )

            if success:
                # 招待メール送信
                email_result = ""
                pending_email_result = ""
                if send_invitation:
                    with st.spinner("📧 参加者に招待メールを送信中..."):
                        # リマインダーテーブルを初期化
                        db.init_reminder_table()

                        # グループ情報を取得
                        group = db.get_group_by_id(selected_group_id)

                        # 1. 登録済みメンバーにメール送信
                        participants = db.get_meeting_participants(meeting_id)
                        recipients = [{'name': p['name'], 'email': p['email']} for p in participants]

                        if recipients:
                            email_success, email_message, success_list, failed_list = db.send_meeting_invitation_email(
                                meeting_id=meeting_id,
                                meeting_title=meeting_title,
                                meeting_description=meeting_description,
                                scheduled_at=scheduled_at,
                                host_name=user['name'],
                                group_name=group['name'] if group else '',
                                recipients=recipients,
                                zoom_url=zoom_url if zoom_url else None,
                                zoom_passcode=zoom_passcode if zoom_passcode else None
                            )

                            if email_success:
                                email_result = f"<br>📧 登録済み: {email_message}"

                        # 2. 未登録の招待者にもメール送信
                        pending_invitations = db.get_pending_invitations_by_group(selected_group_id)
                        pending_emails = [inv['email'] for inv in pending_invitations]

                        if pending_emails:
                            # アプリのURLを取得（Streamlit Cloud用）
                            app_url = "https://ai-literacy-app-9wdvlbxqk77oscqse9rpkq.streamlit.app"

                            pending_success, pending_message, pending_success_list, pending_failed_list = db.send_meeting_invitation_to_pending(
                                meeting_title=meeting_title,
                                meeting_description=meeting_description,
                                scheduled_at=scheduled_at,
                                host_name=user['name'],
                                group_name=group['name'] if group else '',
                                pending_emails=pending_emails,
                                app_url=app_url,
                                zoom_url=zoom_url if zoom_url else None,
                                zoom_passcode=zoom_passcode if zoom_passcode else None
                            )

                            if pending_success and pending_success_list:
                                pending_email_result = f"<br>📧 未登録者: {pending_message}"

                # 成功メッセージを大きく表示
                combined_email_result = email_result + pending_email_result
                if not combined_email_result and send_invitation:
                    combined_email_result = "<br>📧 送信対象者がいませんでした"

                st.markdown(f"""
                <div style="
                    background-color: #d4edda;
                    border: 5px solid #28a745;
                    border-radius: 20px;
                    padding: 40px;
                    margin: 30px 0;
                    text-align: center;
                ">
                    <p style="font-size: 60px; margin: 0;">🎉</p>
                    <p style="font-size: 32px; font-weight: bold; color: #155724; margin: 20px 0;">
                        ミーティング「{meeting_title}」を作成しました！
                    </p>
                    <p style="font-size: 22px; color: #155724;">
                        {combined_email_result}
                    </p>
                    <p style="font-size: 20px; color: #155724; margin-top: 15px;">
                        3秒後に画面が切り替わります...
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                import time
                time.sleep(3)  # 3秒間メッセージを表示
                st.session_state.selected_meeting = meeting_id
                st.session_state.page = 'meetings'
                st.rerun()
            else:
                st.error(f"❌ {message}")
        else:
            st.warning("⚠️ タイトルとグループを選択してください")

# ミーティング詳細・議事録ページ
def show_meeting_detail_page():
    user = st.session_state.user
    meeting_id = st.session_state.get('selected_meeting')

    if not meeting_id:
        st.error("❌ ミーティングが選択されていません")
        return

    meeting = db.get_meeting_by_id(meeting_id)
    if not meeting:
        st.error("❌ ミーティングが見つかりません")
        return

    st.title(f"📹 {meeting['title']}")
    st.markdown(f"**グループ:** {meeting['group_name']}")
    st.markdown(f"**ホスト:** {meeting['host_name']}")

    if meeting['scheduled_at']:
        from datetime import datetime
        try:
            scheduled_dt = datetime.fromisoformat(meeting['scheduled_at'])
            st.markdown(f"**日時:** {scheduled_dt.strftime('%Y年%m月%d日 %H:%M')}")
        except:
            st.markdown(f"**日時:** {meeting['scheduled_at']}")

    # Zoom参加ボタン（大きく目立つように）
    if meeting.get('zoom_url'):
        st.markdown("---")
        show_zoom_join_button(meeting['zoom_url'], meeting.get('zoom_passcode'))

    st.markdown("---")

    # フォローアップミーティング情報
    follow_up = db.get_follow_up_meeting(meeting_id)
    original = db.get_original_meeting(meeting_id)

    if follow_up:
        st.info(f"📅 フォローアップミーティング: {follow_up['title']} ({follow_up['scheduled_at'][:10] if follow_up.get('scheduled_at') else '日時未定'})")
    elif original:
        st.info(f"🔙 このミーティングは「{original['title']}」のフォローアップです")

    st.markdown("---")

    # 参加者リスト
    with st.expander("👥 参加者一覧"):
        participants = db.get_meeting_participants(meeting_id)
        for participant in participants:
            role_text = "👑 ホスト" if participant['role'] == 'host' else "👤 参加者"
            st.markdown(f"- {participant['name']} - {role_text}")

    st.markdown("---")

    # ホストのみ：Zoom情報の編集
    if user['role'] == 'host' and user['id'] == meeting['host_id']:
        with st.expander("⚙️ Zoom情報を編集"):
            st.markdown("Zoom URLやパスコードを変更できます")

            new_zoom_url = st.text_input("Zoom URL", value=meeting.get('zoom_url') or '',
                                         key="edit_zoom_url")
            col1, col2 = st.columns(2)
            with col1:
                new_zoom_id = st.text_input("ZoomミーティングID",
                                            value=meeting.get('zoom_meeting_id') or '',
                                            key="edit_zoom_id")
            with col2:
                new_zoom_passcode = st.text_input("Zoomパスコード",
                                                   value=meeting.get('zoom_passcode') or '',
                                                   key="edit_zoom_passcode")

            if st.button("💾 Zoom情報を保存", type="primary"):
                success, message = db.update_meeting_zoom_info(
                    meeting_id,
                    new_zoom_url if new_zoom_url else None,
                    new_zoom_id if new_zoom_id else None,
                    new_zoom_passcode if new_zoom_passcode else None
                )
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

            # Zoomリマインダーメール送信
            st.markdown("---")
            st.markdown("### 📧 参加者にZoomリマインダーを送信")
            if meeting.get('zoom_url'):
                if st.button("📨 Zoomリマインダーメールを送信", type="primary"):
                    with st.spinner("📤 メールを送信中..."):
                        participants = db.get_meeting_participants(meeting_id)
                        recipients = [{'name': p['name'], 'email': p['email']} for p in participants]

                        success, message, success_list, failed_list = db.send_zoom_reminder_email(
                            meeting['title'],
                            meeting.get('scheduled_at', ''),
                            recipients,
                            meeting['zoom_url'],
                            meeting.get('zoom_passcode')
                        )

                        if success:
                            st.success(f"🎉 {message}")
                        else:
                            st.error(f"❌ {message}")
            else:
                st.warning("⚠️ Zoom URLが設定されていません")

    st.markdown("---")

    # 録音・議事録セクション
    recording = db.get_recording_by_meeting(meeting_id)

    tab1, tab2, tab3, tab4 = st.tabs(["📝 議事録", "🤖 AIに質問", "📚 学んだこと", "🎤 録音"])

    with tab1:
        show_minutes_tab(user, meeting, meeting_id, recording)

    with tab2:
        show_ai_chat_tab(user, meeting_id, recording)

    with tab3:
        show_learning_notes_tab(user, meeting_id)

    with tab4:
        show_recording_tab(user, meeting, meeting_id, recording)

    st.markdown("---")

    # フォローアップミーティング作成（ホストのみ）
    if user['role'] == 'host' and user['id'] == meeting['host_id']:
        if not follow_up:
            with st.expander("📅 フォローアップミーティングを設定"):
                st.markdown("このミーティングの1週間後にフォローアップミーティングを作成できます。")

                if st.button("🔄 フォローアップミーティングを作成", type="primary"):
                    from datetime import datetime, timedelta

                    # 1週間後の日時を計算
                    if meeting['scheduled_at']:
                        original_dt = datetime.fromisoformat(meeting['scheduled_at'])
                        followup_dt = original_dt + timedelta(days=7)
                    else:
                        followup_dt = datetime.now() + timedelta(days=7)

                    # フォローアップミーティングを作成
                    followup_title = f"{meeting['title']} - フォローアップ"
                    followup_description = f"前回のミーティングのフォローアップです。学んだことを共有し、質問があれば解決しましょう。"

                    success, message, followup_id = db.create_meeting(
                        followup_title,
                        followup_description,
                        meeting['group_id'],
                        user['id'],
                        followup_dt.isoformat(),
                        meeting.get('zoom_url'),  # Zoom情報を引き継ぐ
                        meeting.get('zoom_meeting_id'),
                        meeting.get('zoom_passcode')
                    )

                    if success:
                        # フォローアップとして関連付け
                        db.create_follow_up_meeting(meeting_id, followup_id)
                        st.success("✅ フォローアップミーティングを作成しました！")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

    st.markdown("---")

    if st.button("← ミーティング一覧に戻る", use_container_width=True):
        st.session_state.page = 'meetings'
        st.rerun()


def show_minutes_tab(user, meeting, meeting_id, recording):
    """議事録タブの内容"""
    st.markdown("## 📝 議事録")

    if recording and recording['transcript']:
        # AIによる議事録生成セクション
        st.markdown("""
        <div style="
            background-color: #e8f5e9;
            padding: 25px;
            border-radius: 15px;
            border: 3px solid #4caf50;
            margin-bottom: 25px;
        ">
            <h3 style="color: #2e7d32; margin-top: 0;">🤖 AI議事録の自動生成</h3>
            <p style="font-size: 20px; color: #333;">
                文字起こし結果から、AIが自動的に見やすい議事録を生成します。
            </p>
        </div>
        """, unsafe_allow_html=True)

        show_step(1, "下のボタンを押すとAIが議事録を作成します")
        st.markdown("")

        if st.button("✨ 議事録を自動生成する", type="primary", use_container_width=True, key="generate_minutes_btn"):
            with st.spinner("🤖 AIが議事録を生成中です。少々お待ちください..."):
                success, message, formatted_minutes = db.generate_minutes_with_gpt4o(recording['transcript'])

                if success:
                    # 生成された議事録を保存
                    save_success, save_message = db.save_formatted_minutes(meeting_id, formatted_minutes)

                    if save_success:
                        st.success("✅ 議事録の生成が完了しました！")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ 保存エラー: {save_message}")
                else:
                    st.error(f"❌ {message}")

        st.markdown("---")

        # 生成された議事録の表示
        if recording['summary']:
            st.markdown("### 📋 生成された議事録")

            # 高齢者向けの見やすいスタイルで表示
            st.markdown(f"""
            <div style="
                background-color: #f8f9fa;
                padding: 35px;
                border-radius: 20px;
                border: 4px solid #1976d2;
                font-size: 22px;
                line-height: 2;
                color: #212529;
            ">
            {recording['summary'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")

            # ダウンロードボタン
            from datetime import datetime
            download_filename = f"議事録_{meeting['title']}_{datetime.now().strftime('%Y%m%d')}.txt"

            st.download_button(
                label="📥 議事録をダウンロード",
                data=recording['summary'],
                file_name=download_filename,
                mime="text/plain",
                key="download_minutes",
                use_container_width=True
            )

            st.markdown("")

            # メール送信セクション
            show_email_section(meeting, meeting_id, recording)

        # 元の文字起こしテキスト
        st.markdown("### 📄 文字起こしテキスト（元データ）")
        with st.expander("文字起こしテキストを表示"):
            st.text_area(
                "文字起こし内容",
                value=recording['transcript'],
                height=300,
                key="view_transcript",
                disabled=True
            )

        st.markdown("")
        st.markdown(f"**作成者:** {recording['created_by_name']}")
        st.markdown(f"**最終更新:** {recording['updated_at']}")
    else:
        st.markdown("""
        <div style="
            background-color: #fff3e0;
            padding: 30px;
            border-radius: 15px;
            border: 3px solid #ff9800;
            text-align: center;
        ">
            <h3 style="color: #e65100;">📝 まだ議事録が作成されていません</h3>
            <p style="font-size: 22px; color: #333;">
                「🎤 録音」タブから音声ファイルをアップロードして、<br>
                文字起こしを行ってください。
            </p>
        </div>
        """, unsafe_allow_html=True)


def show_email_section(meeting, meeting_id, recording):
    """メール送信セクション"""
    st.markdown("""
    <div style="
        background-color: #e8f4fd;
        padding: 30px;
        border-radius: 15px;
        border: 3px solid #2196f3;
        margin: 25px 0;
    ">
        <h3 style="color: #1565c0; font-size: 28px; margin-bottom: 15px;">📧 参加者にメールで議事録を送る</h3>
        <p style="font-size: 22px; line-height: 1.8; color: #333; margin: 0;">
            ミーティングに参加した全員に、議事録をメールで送信できます。<br>
            下のボタンを押すと、グループのメンバー全員にメールが届きます。
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 参加者一覧を取得して表示
    participants = db.get_meeting_participants(meeting_id)

    if participants:
        with st.expander("📋 送信先の確認（クリックして開く）"):
            st.markdown("**以下の方々にメールが送信されます：**")
            for p in participants:
                st.markdown(f"- {p['name']} （{p['email']}）")

        show_step(1, "下のボタンを押してメールを送信してください")
        st.markdown("")

        if st.button("📧 参加者全員にメールを送信", type="primary", use_container_width=True, key="send_email_btn"):
            with st.spinner("📤 メールを送信中です。しばらくお待ちください..."):
                # 参加者リストを送信用に整形
                recipients = [{'name': p['name'], 'email': p['email']} for p in participants]

                # メール送信（Zoom情報含む）
                success, message, success_list, failed_list = db.send_minutes_email(
                    meeting_id=meeting_id,
                    meeting_title=meeting['title'],
                    scheduled_at=meeting.get('scheduled_at', ''),
                    minutes_content=recording['summary'],
                    recipients=recipients,
                    zoom_url=meeting.get('zoom_url'),
                    zoom_passcode=meeting.get('zoom_passcode')
                )

                if success:
                    st.success(f"🎉 {message}")
                    st.balloons()
                    if success_list:
                        st.markdown("**送信成功:**")
                        for email in success_list:
                            st.markdown(f"- ✅ {email}")
                else:
                    st.error(f"😢 {message}")
                    show_email_setup_guide()

                if failed_list:
                    st.warning("**送信失敗:**")
                    for fail in failed_list:
                        st.markdown(f"- ❌ {fail}")
    else:
        st.info("📭 参加者情報が見つかりません")


def show_email_setup_guide():
    """メール設定ガイドを表示"""
    st.markdown("---")
    st.markdown("### 📌 メール設定の方法")

    tab_email_local, tab_email_cloud = st.tabs(["💻 ローカル環境", "☁️ Streamlit Cloud"])

    with tab_email_local:
        st.markdown("""
        **ローカルで実行する場合：**
        1. プロジェクトのルートディレクトリの `.env` ファイルを開く
        2. 以下の内容を追加してください:
        ```
        EMAIL_ADDRESS=your_gmail@gmail.com
        EMAIL_PASSWORD=your_app_password
        ```
        3. **重要:** `EMAIL_PASSWORD` には通常のGmailパスワードではなく、
           **Gmailアプリパスワード**を設定してください

        **アプリパスワードの取得方法:**
        1. Googleアカウント → セキュリティ → 2段階認証を有効化
        2. セキュリティ → アプリパスワード → 「メール」を選択
        3. 生成された16文字のパスワードを使用
        """)

    with tab_email_cloud:
        st.markdown("""
        **Streamlit Cloudで実行する場合：**
        1. Streamlit Cloudのダッシュボードでアプリを選択
        2. "Settings" → "Secrets" を開く
        3. 以下の内容を追加してください:
        ```
        EMAIL_ADDRESS = "your_gmail@gmail.com"
        EMAIL_PASSWORD = "your_app_password"
        ```
        4. "Save" をクリック

        **アプリパスワードの取得方法:**
        1. Googleアカウント → セキュリティ → 2段階認証を有効化
        2. セキュリティ → アプリパスワード → 「メール」を選択
        3. 生成された16文字のパスワードを使用
        """)


def show_ai_chat_tab(user, meeting_id, recording):
    """AIチャットタブの内容"""
    # 高齢者向けのタイトルとスタイル
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 30px;
    ">
        <h2 style="margin: 0; font-size: 34px; color: white;">🤖 AIと議事録について対話する</h2>
        <p style="margin: 15px 0 0 0; font-size: 22px; color: #f0f0f0;">
            議事録の内容について、AIに質問できます。優しいAIがわかりやすくお答えします。
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 議事録の有無を確認
    if not recording or not recording['transcript']:
        st.warning("⚠️ まだ議事録が作成されていません。「📝 議事録」タブから議事録を作成すると、その内容についてAIに質問できます。")
        st.markdown("---")

    # 質問の例を表示（高齢者向けに大きく見やすく）
    st.markdown("""
    <div style="
        background-color: #e8f5e9;
        padding: 30px;
        border-radius: 20px;
        border: 4px solid #4caf50;
        margin-bottom: 30px;
    ">
        <h3 style="color: #2e7d32; font-size: 28px; margin-bottom: 20px;">💡 こんな質問ができます（例）</h3>
        <ul style="font-size: 24px; line-height: 2.2; color: #333; margin: 0; padding-left: 30px;">
            <li>「この会議の重要なポイントは？」</li>
            <li>「次回までにやるべきことは？」</li>
            <li>「〇〇についてもっと詳しく教えて」</li>
            <li>「AIの使い方がよくわからないので教えて」</li>
            <li>「今日学んだことを簡単にまとめて」</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # チャット履歴を表示
    chat_history = db.get_chat_history(meeting_id)

    if chat_history:
        # 履歴のヘッダーとクリアボタン
        col_header, col_clear = st.columns([3, 1])
        with col_header:
            st.markdown("### 💬 会話の履歴")
        with col_clear:
            if st.button("🗑️ 履歴をクリア", key="clear_chat"):
                success, message = db.clear_chat_history(meeting_id)
                if success:
                    st.success("✅ チャット履歴をクリアしました")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

        # チャット履歴を表示（高齢者向けに大きく見やすく）
        for msg in chat_history:
            if msg['is_ai']:
                st.markdown(f"""
                <div style="
                    background-color: #e3f2fd;
                    padding: 25px;
                    border-radius: 20px;
                    margin-bottom: 20px;
                    border-left: 6px solid #2196f3;
                    font-size: 22px;
                    line-height: 2;
                ">
                    <strong style="color: #1565c0; font-size: 24px;">🤖 AI:</strong><br>
                    <span style="color: #333;">{msg["message"].replace(chr(10), '<br>')}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    background-color: #fff8e1;
                    padding: 25px;
                    border-radius: 20px;
                    margin-bottom: 20px;
                    border-left: 6px solid #ffc107;
                    font-size: 22px;
                    line-height: 2;
                ">
                    <strong style="color: #f57c00; font-size: 24px;">👤 {msg["user_name"]}さん:</strong><br>
                    <span style="color: #333;">{msg["message"].replace(chr(10), '<br>')}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

    # チャット入力（高齢者向けに大きく見やすく）
    st.markdown("""
    <div style="
        background-color: #f5f5f5;
        padding: 30px;
        border-radius: 20px;
        border: 3px solid #9e9e9e;
        margin-bottom: 25px;
    ">
        <h3 style="color: #424242; font-size: 28px; margin-bottom: 15px;">✍️ 質問を入力してください</h3>
        <p style="font-size: 20px; color: #666; margin: 0;">
            下のボックスに質問を入力して、「質問する」ボタンを押してください。
        </p>
    </div>
    """, unsafe_allow_html=True)

    user_question = st.text_area(
        "質問内容",
        height=150,
        placeholder="ここに質問を入力してください。\n例：「この会議の重要なポイントを教えて」",
        key="ai_question",
        label_visibility="collapsed"
    )

    # 質問送信ボタン（大きく目立つように）
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💬 質問する", type="primary", key="send_question", use_container_width=True):
            if user_question:
                with st.spinner("🤖 AIが回答を作成中です。少々お待ちください..."):
                    # ユーザーのメッセージを保存
                    db.save_chat_message(meeting_id, user['id'], user_question, is_ai=False)

                    # AI応答を生成
                    ai_response = db.generate_ai_response(meeting_id, user_question)

                    # AI応答を保存
                    db.save_chat_message(meeting_id, user['id'], ai_response, is_ai=True)

                    st.success("✅ 回答が届きました！")
                    st.rerun()
            else:
                st.warning("⚠️ 質問を入力してください")

    # 補足情報（高齢者向け）
    st.markdown("---")
    st.markdown("""
    <div style="
        background-color: #fff3e0;
        padding: 25px;
        border-radius: 15px;
        border: 3px solid #ff9800;
        margin-top: 25px;
    ">
        <h4 style="color: #e65100; font-size: 24px; margin-bottom: 15px;">📌 ヒント</h4>
        <ul style="font-size: 20px; line-height: 2; color: #333; margin: 0; padding-left: 25px;">
            <li>質問は<strong>具体的</strong>に書くと、より良い回答が得られます</li>
            <li>何度でも質問できます。遠慮なく聞いてください！</li>
            <li>AIの回答がわかりにくかったら、「もっと簡単に説明して」と聞いてみましょう</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


def show_learning_notes_tab(user, meeting_id):
    """学びのメモタブの内容"""
    st.markdown("## 📚 学んだこと")
    st.markdown("""
    <div style="
        background-color: #e8f5e9;
        padding: 20px;
        border-radius: 15px;
        border: 3px solid #4caf50;
        margin-bottom: 25px;
    ">
        <p style="font-size: 22px; color: #2e7d32; margin: 0;">
            💡 このミーティングで学んだことを記録しましょう。後で振り返ることができます！
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 自分の学びのメモ
    user_note = db.get_user_learning_note(meeting_id, user['id'])

    st.markdown("### 📝 あなたの学びのメモ")

    show_step(1, "学んだことを下のボックスに入力してください")
    learning_note = st.text_area(
        "学んだことを記録",
        value=user_note['note'] if user_note else "",
        height=200,
        placeholder="例：今日はAIへの質問の仕方を学びました。具体的に聞くことが大切だとわかりました。",
        key="learning_note",
        label_visibility="collapsed"
    )

    show_step(2, "下のボタンを押して保存してください")
    st.markdown("")

    if st.button("💾 学びを保存", type="primary", use_container_width=True):
        if learning_note:
            success, message = db.save_learning_note(meeting_id, user['id'], learning_note)
            if success:
                st.success(f"✅ {message}")
                st.balloons()
                st.rerun()
            else:
                st.error(f"❌ {message}")
        else:
            st.warning("⚠️ 学んだことを入力してください")

    st.markdown("---")

    # 他の参加者の学びのメモを表示
    st.markdown("### 👥 みんなの学び")
    all_notes = db.get_learning_notes(meeting_id)

    if all_notes:
        for note in all_notes:
            if note['user_id'] != user['id']:  # 自分以外のメモを表示
                st.markdown(f'<div class="group-card">', unsafe_allow_html=True)
                st.markdown(f"**{note['user_name']}さんの学び**")
                st.markdown(note['note'])
                st.markdown(f"_記録日: {note['created_at'][:10]}_")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")
    else:
        st.info("📭 まだ誰も学びを記録していません")


def show_recording_tab(user, meeting, meeting_id, recording):
    """録音タブの内容"""
    st.markdown("## 🎤 録音・文字起こし")
    st.markdown("")

    # 録音ファイルの表示
    if recording and recording['audio_file_path']:
        st.markdown("### 📁 保存済み音声ファイル")
        st.audio(recording['audio_file_path'])
        st.markdown(f"**ファイル:** {os.path.basename(recording['audio_file_path'])}")
    else:
        st.info("📭 録音ファイルはまだアップロードされていません")

    st.markdown("---")

    # 音声ファイルアップロード機能
    if user['role'] == 'host' or user['id'] == meeting['host_id']:
        st.markdown("""
        <div style="
            background-color: #e3f2fd;
            padding: 25px;
            border-radius: 15px;
            border: 3px solid #2196f3;
            margin-bottom: 25px;
        ">
            <h3 style="color: #1565c0; margin-top: 0;">🎙️ 音声ファイルから議事録を作成</h3>
            <p style="font-size: 20px; color: #333;">
                音声ファイル（mp3, wav, m4a）をアップロードすると、<br>
                自動的に文字起こしして議事録を作成します。
            </p>
        </div>
        """, unsafe_allow_html=True)

        show_step(1, "下のボタンから音声ファイルを選択してください")
        audio_file = st.file_uploader(
            "音声ファイルを選択",
            type=["mp3", "wav", "m4a"],
            help="ファイルサイズは25MB以下にしてください",
            key="audio_upload"
        )

        if audio_file is not None:
            # ファイルサイズを表示
            file_size_mb = len(audio_file.getvalue()) / (1024 * 1024)
            st.info(f"📊 ファイルサイズ: {file_size_mb:.2f} MB")

            if file_size_mb > 25:
                st.error("⚠️ ファイルサイズが25MBを超えています。ファイルを圧縮するか、短い音声ファイルを選択してください。")
            else:
                st.markdown("")
                show_step(2, "下のボタンを押して文字起こしを開始してください")
                st.markdown("")

                if st.button("🚀 文字起こしを開始", type="primary", use_container_width=True, key="start_transcription"):
                    with st.spinner("🎙️ 音声を文字起こし中です。しばらくお待ちください..."):
                        success, message, transcript = db.save_audio_and_transcribe(
                            meeting_id,
                            audio_file,
                            user['id']
                        )

                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            st.markdown("### 📝 文字起こし結果")
                            st.text_area(
                                "文字起こしされた内容",
                                value=transcript,
                                height=300,
                                disabled=True,
                                key="transcription_result"
                            )

                            # 次のステップへの案内
                            st.markdown("""
                            <div style="
                                background-color: #d1ecf1;
                                padding: 30px;
                                border-radius: 20px;
                                border: 4px solid #17a2b8;
                                margin: 25px 0;
                            ">
                                <h3 style="color: #0c5460; font-size: 30px; margin-bottom: 20px;">🎯 次のステップ</h3>
                                <p style="font-size: 24px; line-height: 2; color: #0c5460; margin: 0;">
                                    文字起こしが完了しました！<br>
                                    <strong>「📝 議事録」タブ</strong>に移動して、<br>
                                    <strong>「✨ 議事録を自動生成する」</strong>ボタンを押してください。<br>
                                    AIが見やすい議事録を自動的に作成します。
                                </p>
                            </div>
                            """, unsafe_allow_html=True)

                            st.rerun()
                        else:
                            st.error(f"❌ エラー: {message}")
    else:
        st.info("📌 音声ファイルのアップロードはホストのみが行えます")

    st.markdown("---")
    st.markdown("""
    <div style="
        background-color: #fff3e0;
        padding: 20px;
        border-radius: 15px;
        border: 3px solid #ff9800;
    ">
        <h4 style="color: #e65100; margin-top: 0;">💡 ヒント</h4>
        <ul style="font-size: 18px; line-height: 1.8; color: #333; margin: 0; padding-left: 20px;">
            <li><strong>対応形式:</strong> mp3, wav, m4a</li>
            <li><strong>ファイルサイズ上限:</strong> 25MB</li>
            <li><strong>言語:</strong> 日本語に最適化されています</li>
            <li><strong>処理時間:</strong> ファイルの長さによって数秒〜数分かかります</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# サイドバー
def show_sidebar():
    with st.sidebar:
        user = st.session_state.user

        st.markdown(f"### 👤 {user['name']}")
        st.markdown(f"**{user['email']}**")
        st.markdown(f"**役割:** {'👑 ホスト' if user['role'] == 'host' else '👤 参加者'}")
        st.markdown("---")

        st.markdown("### 📋 メニュー")
        st.markdown("")

        if st.button("🏠 ダッシュボード", key="nav_dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()

        if st.button("✅ チェックリスト", key="nav_checklist", use_container_width=True):
            st.session_state.page = 'checklist'
            st.rerun()

        if st.button("👥 グループ", key="nav_groups", use_container_width=True):
            st.session_state.page = 'groups'
            st.rerun()

        if st.button("📹 ミーティング", key="nav_meetings", use_container_width=True):
            st.session_state.page = 'meetings'
            st.rerun()

        st.markdown("---")

        if st.button("🚪 ログアウト", key="logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = 'dashboard'
            st.rerun()

# メインアプリ
def main():
    if st.session_state.user is None:
        show_auth_page()
    else:
        show_sidebar()

        if st.session_state.page == 'dashboard':
            show_dashboard()
        elif st.session_state.page == 'checklist':
            show_checklist_page()
        elif st.session_state.page == 'groups':
            show_groups_page()
        elif st.session_state.page == 'meetings':
            show_meetings_page()
        elif st.session_state.page == 'meeting_detail':
            show_meeting_detail_page()

if __name__ == "__main__":
    main()

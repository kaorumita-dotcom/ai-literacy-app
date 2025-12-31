import streamlit as st
import database as db
from datetime import datetime

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

# カスタムCSS（シニア向けの大きな文字とボタン）
st.markdown("""
    <style>
    /* 全体の文字サイズを大きく */
    .main {
        font-size: 20px;
    }

    /* タイトルを大きく */
    h1 {
        font-size: 48px !important;
        font-weight: bold !important;
        color: #1f77b4 !important;
        margin-bottom: 30px !important;
    }

    /* サブタイトルを大きく */
    h2 {
        font-size: 32px !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
        margin-top: 25px !important;
        margin-bottom: 20px !important;
    }

    h3 {
        font-size: 28px !important;
        font-weight: bold !important;
        color: #34495e !important;
        margin-top: 20px !important;
        margin-bottom: 15px !important;
    }

    /* チェックボックスのラベルを大きく */
    .stCheckbox label {
        font-size: 22px !important;
        font-weight: 500 !important;
        padding: 10px 0 !important;
    }

    /* チェックボックス自体を大きく */
    .stCheckbox input[type="checkbox"] {
        width: 30px !important;
        height: 30px !important;
        margin-right: 15px !important;
    }

    /* ボタンを大きく */
    .stButton button {
        font-size: 24px !important;
        padding: 15px 40px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        min-height: 60px !important;
    }

    /* プログレスバーを大きく */
    .stProgress > div > div {
        height: 40px !important;
    }

    /* メトリクスを大きく */
    [data-testid="stMetricValue"] {
        font-size: 48px !important;
        font-weight: bold !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 24px !important;
        font-weight: bold !important;
    }

    /* カテゴリカードのスタイル */
    .category-card {
        background-color: #f8f9fa;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 30px;
        border: 3px solid #dee2e6;
    }

    /* 達成済みカテゴリ */
    .category-completed {
        background-color: #d4edda;
        border: 3px solid #28a745;
    }

    /* コントラストの高い色使い */
    .stMarkdown {
        color: #212529 !important;
    }

    /* 進捗表示エリア */
    .progress-area {
        background-color: #e9ecef;
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 40px;
        border: 3px solid #adb5bd;
    }

    /* サイドバーのスタイル */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    /* 入力フィールドを大きく */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        font-size: 20px !important;
        padding: 12px !important;
        min-height: 50px !important;
    }

    .stTextInput label, .stTextArea label, .stSelectbox label {
        font-size: 22px !important;
        font-weight: bold !important;
    }

    /* テーブルのスタイル */
    .dataframe {
        font-size: 20px !important;
    }

    /* グループカード */
    .group-card {
        background-color: #fff;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 2px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

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

# ログイン・登録画面
def show_auth_page():
    st.title("✅ AI学習チェックリスト")
    st.markdown("### シニアのためのAI活用ガイド")
    st.markdown("---")

    tab1, tab2 = st.tabs(["ログイン", "新規登録"])

    with tab1:
        st.markdown("## ログイン")
        st.markdown("")

        email = st.text_input("メールアドレス", key="login_email")
        password = st.text_input("パスワード", type="password", key="login_password")

        st.markdown("")

        if st.button("ログイン", key="login_button", type="primary"):
            if email and password:
                user = db.authenticate_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success("ログインしました！")
                    st.rerun()
                else:
                    st.error("メールアドレスまたはパスワードが間違っています")
            else:
                st.warning("メールアドレスとパスワードを入力してください")

    with tab2:
        st.markdown("## 新規登録")
        st.markdown("")

        name = st.text_input("お名前", key="register_name")
        email = st.text_input("メールアドレス", key="register_email")
        password = st.text_input("パスワード", type="password", key="register_password")
        password_confirm = st.text_input("パスワード（確認）", type="password", key="register_password_confirm")
        role = st.selectbox(
            "役割を選択",
            options=["participant", "host"],
            format_func=lambda x: "参加者（学習する人）" if x == "participant" else "ホスト（教える人・グループを作る人）",
            key="register_role"
        )

        st.markdown("")

        if st.button("登録する", key="register_button", type="primary"):
            if not all([name, email, password, password_confirm]):
                st.warning("すべての項目を入力してください")
            elif password != password_confirm:
                st.error("パスワードが一致しません")
            elif len(password) < 6:
                st.warning("パスワードは6文字以上にしてください")
            else:
                success, message = db.create_user(name, email, password, role)
                if success:
                    st.success(message)
                    st.info("ログインタブからログインしてください")
                else:
                    st.error(message)

# ダッシュボード
def show_dashboard():
    user = st.session_state.user

    st.title(f"👋 こんにちは、{user['name']}さん")
    st.markdown(f"**役割:** {'ホスト（教える人）' if user['role'] == 'host' else '参加者（学習する人）'}")
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
        st.info("まだグループに参加していません")

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
            st.info("まだグループを作成していません")

    # 招待通知
    invitations = db.get_user_invitations(user['email'])
    if invitations:
        st.markdown("---")
        st.markdown("## 📧 グループへの招待")

        for invitation in invitations:
            st.markdown(f'<div class="group-card">', unsafe_allow_html=True)
            st.markdown(f"### {invitation['group_name']}")
            st.markdown(f"**説明:** {invitation['description']}")
            st.markdown(f"**招待者:** {invitation['invited_by_name']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"参加する", key=f"accept_{invitation['id']}"):
                    success, message = db.accept_invitation(invitation['id'], user['id'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            with col2:
                if st.button(f"辞退する", key=f"decline_{invitation['id']}"):
                    success, message = db.decline_invitation(invitation['id'])
                    if success:
                        st.info(message)
                        st.rerun()
                    else:
                        st.error(message)

            st.markdown('</div>', unsafe_allow_html=True)

# チェックリストページ
def show_checklist_page():
    user = st.session_state.user

    st.title("✅ AI学習チェックリスト")
    st.markdown("### シニアのためのAI活用ガイド")

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
        completion_icon = "✅" if is_completed else "📝"
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
        st.success("🎉 おめでとうございます！すべての項目を達成しました！")

    # フッター
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #6c757d; font-size: 18px; padding: 20px;'>
            このチェックリストで、AIを楽しく学びましょう！<br>
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
        tab1, tab2 = st.tabs(["グループ作成", "管理中のグループ"])

        with tab1:
            st.markdown("## 新しいグループを作成")
            st.markdown("")

            group_name = st.text_input("グループ名", key="new_group_name")
            group_description = st.text_area("グループの説明", key="new_group_description", height=150)

            st.markdown("")

            if st.button("グループを作成", type="primary"):
                if group_name:
                    success, message, group_id = db.create_group(group_name, group_description, user['id'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("グループ名を入力してください")

        with tab2:
            st.markdown("## 管理中のグループ")
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
                    with st.expander("メンバー一覧を見る"):
                        members = db.get_group_members(group['id'])
                        for member in members:
                            role_text = "ホスト" if member['role'] == 'host' else "参加者"
                            st.markdown(f"- {member['name']} ({member['email']}) - {role_text}")

                    # メンバー招待
                    with st.expander("メンバーを招待する"):
                        invite_email = st.text_input(
                            "招待するメールアドレス",
                            key=f"invite_email_{group['id']}"
                        )
                        if st.button("招待を送る", key=f"invite_button_{group['id']}"):
                            if invite_email:
                                success, message = db.invite_to_group(group['id'], invite_email, user['id'])
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                            else:
                                st.warning("メールアドレスを入力してください")

                    # グループメンバーの進捗表示
                    with st.expander("メンバーの学習進捗を見る"):
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
                st.info("まだグループを作成していません")

    else:
        # 参加者の場合：所属グループの表示
        st.markdown("## あなたが参加しているグループ")
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
                with st.expander("メンバー一覧を見る"):
                    members = db.get_group_members(group['id'])
                    for member in members:
                        role_text = "ホスト" if member['role'] == 'host' else "参加者"
                        st.markdown(f"- {member['name']} - {role_text}")

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")
        else:
            st.info("まだグループに参加していません")

# ミーティング管理ページ
def show_meetings_page():
    user = st.session_state.user

    st.title("📹 ミーティング")
    st.markdown("---")

    # タブで機能を分割
    if user['role'] == 'host':
        tab1, tab2 = st.tabs(["ミーティング一覧", "新規作成"])

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

            # 議事録表示
            recording = db.get_recording_by_meeting(meeting['id'])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 議事録を見る", key=f"view_minutes_{meeting['id']}"):
                    st.session_state.selected_meeting = meeting['id']
                    st.session_state.page = 'meeting_detail'
                    st.rerun()

            with col2:
                if recording:
                    st.success("✅ 議事録あり")
                else:
                    st.info("議事録なし")

            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("")
    else:
        st.info("参加予定のミーティングはありません")

def show_create_meeting(user):
    """ミーティング作成フォーム"""
    st.markdown("## 新しいミーティングを作成")
    st.markdown("")

    # ホストが管理しているグループを取得
    groups = db.get_groups_by_host(user['id'])

    if not groups:
        st.warning("ミーティングを作成するには、まずグループを作成してください")
        if st.button("グループを作成する"):
            st.session_state.page = 'groups'
            st.rerun()
        return

    # グループ選択
    group_options = {g['id']: f"{g['name']} ({g['member_count']}名)" for g in groups}
    selected_group_id = st.selectbox(
        "グループを選択",
        options=list(group_options.keys()),
        format_func=lambda x: group_options[x],
        key="meeting_group"
    )

    meeting_title = st.text_input("ミーティングタイトル", key="meeting_title")
    meeting_description = st.text_area("ミーティングの説明", key="meeting_description", height=150)

    col1, col2 = st.columns(2)
    with col1:
        meeting_date = st.date_input("日付", key="meeting_date")
    with col2:
        meeting_time = st.time_input("時刻", key="meeting_time")

    st.markdown("")

    if st.button("ミーティングを作成", type="primary"):
        if meeting_title and selected_group_id:
            from datetime import datetime
            scheduled_at = datetime.combine(meeting_date, meeting_time).isoformat()

            success, message, meeting_id = db.create_meeting(
                meeting_title,
                meeting_description,
                selected_group_id,
                user['id'],
                scheduled_at
            )

            if success:
                st.success(message)
                st.session_state.selected_meeting = meeting_id
                st.rerun()
            else:
                st.error(message)
        else:
            st.warning("タイトルとグループを選択してください")

# ミーティング詳細・議事録ページ
def show_meeting_detail_page():
    user = st.session_state.user
    meeting_id = st.session_state.get('selected_meeting')

    if not meeting_id:
        st.error("ミーティングが選択されていません")
        return

    meeting = db.get_meeting_by_id(meeting_id)
    if not meeting:
        st.error("ミーティングが見つかりません")
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

    st.markdown("---")

    # 参加者リスト
    with st.expander("👥 参加者一覧"):
        participants = db.get_meeting_participants(meeting_id)
        for participant in participants:
            role_text = "ホスト" if participant['role'] == 'host' else "参加者"
            st.markdown(f"- {participant['name']} - {role_text}")

    st.markdown("---")

    # 録音・議事録セクション
    recording = db.get_recording_by_meeting(meeting_id)

    tab1, tab2 = st.tabs(["📝 議事録", "🎤 録音"])

    with tab1:
        st.markdown("## 議事録")

        if recording and recording['transcript']:
            st.markdown("### 現在の議事録")
            st.text_area(
                "議事録内容",
                value=recording['transcript'],
                height=400,
                key="view_transcript",
                disabled=True
            )

            if recording['summary']:
                st.markdown("### サマリー")
                st.info(recording['summary'])

            st.markdown("")
            st.markdown(f"**作成者:** {recording['created_by_name']}")
            st.markdown(f"**最終更新:** {recording['updated_at']}")
        else:
            st.info("まだ議事録が作成されていません")

        # 議事録編集（ホストまたは作成者のみ）
        if user['role'] == 'host' or (recording and recording['created_by'] == user['id']):
            st.markdown("---")
            st.markdown("### 議事録を編集")

            new_transcript = st.text_area(
                "議事録を入力",
                value=recording['transcript'] if recording else "",
                height=300,
                key="edit_transcript",
                placeholder="ミーティングの内容を入力してください..."
            )

            new_summary = st.text_area(
                "サマリー（要約）",
                value=recording['summary'] if recording and recording['summary'] else "",
                height=150,
                key="edit_summary",
                placeholder="ミーティングの要点をまとめてください..."
            )

            if st.button("議事録を保存", type="primary"):
                success, message, _ = db.save_recording(meeting_id, None, new_transcript, user['id'])
                if success and new_summary:
                    db.update_recording_summary(meeting_id, new_summary)

                if success:
                    st.success("議事録を保存しました")
                    st.rerun()
                else:
                    st.error(message)

    with tab2:
        st.markdown("## 録音")
        st.markdown("")

        # 録音ファイルの表示（将来実装）
        if recording and recording['audio_file_path']:
            st.audio(recording['audio_file_path'])
        else:
            st.info("録音ファイルはまだアップロードされていません")

        st.markdown("---")
        st.markdown("### 🎤 ブラウザで録音（準備中）")
        st.info("ブラウザベースの録音機能は今後のバージョンで実装予定です。現在は手動で議事録を入力してください。")

        # 将来的にはここに録音UIを追加
        # - 録音開始/停止ボタン
        # - 録音した音声のプレビュー
        # - 文字起こし（Whisper API連携）

    st.markdown("---")

    if st.button("← ミーティング一覧に戻る"):
        st.session_state.page = 'meetings'
        st.rerun()

# サイドバー
def show_sidebar():
    with st.sidebar:
        user = st.session_state.user

        st.markdown(f"### 👤 {user['name']}")
        st.markdown(f"**{user['email']}**")
        st.markdown(f"**役割:** {'ホスト' if user['role'] == 'host' else '参加者'}")
        st.markdown("---")

        st.markdown("### 📋 メニュー")

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

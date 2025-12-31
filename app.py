import streamlit as st
import json
import os
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="AI学習チェックリスト",
    page_icon="✅",
    layout="wide"
)

# データファイルのパス
DATA_FILE = "checklist_data.json"

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
    .stMetric label {
        font-size: 24px !important;
        font-weight: bold !important;
    }

    .stMetric .metric-value {
        font-size: 48px !important;
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
    </style>
""", unsafe_allow_html=True)

# データの読み込み
def load_data():
    """JSONファイルからチェック状態を読み込む"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

# データの保存
def save_data(data):
    """JSONファイルにチェック状態を保存する"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, indent=2, ensure_ascii=False, fp=f)

# 初期化
if 'checklist' not in st.session_state:
    st.session_state.checklist = load_data()

# 進捗計算
def calculate_progress():
    """全体の進捗とカテゴリごとの進捗を計算"""
    total_items = sum(len(items) for items in CHECKLIST_CATEGORIES.values())
    checked_items = sum(1 for item in st.session_state.checklist.values() if item)

    category_progress = {}
    for category, items in CHECKLIST_CATEGORIES.items():
        category_total = len(items)
        category_checked = sum(1 for item in items if st.session_state.checklist.get(f"{category}_{item}", False))
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

# メインアプリ
def main():
    st.title("✅ AI学習チェックリスト")
    st.markdown("### シニアのためのAI活用ガイド")

    # 進捗表示
    progress = calculate_progress()

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

    # プログレスバー
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
            key = f"{category}_{item}"
            checked = st.session_state.checklist.get(key, False)

            if st.checkbox(item, value=checked, key=key):
                st.session_state.checklist[key] = True
                save_data(st.session_state.checklist)
            else:
                st.session_state.checklist[key] = False
                save_data(st.session_state.checklist)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("")

    st.markdown("---")

    # リセットボタン
    st.markdown("### 🔄 データ管理")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("すべてリセット", type="secondary"):
            st.session_state.checklist = {}
            save_data({})
            st.rerun()

    with col2:
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

if __name__ == "__main__":
    main()

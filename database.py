"""
データベース管理モジュール
ユーザー、グループ、チェックリストの永続化を管理
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple

DB_FILE = "ai_literacy.db"

def get_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """データベースとテーブルを初期化"""
    conn = get_connection()
    cursor = conn.cursor()

    # ユーザーテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('host', 'participant')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # グループテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            host_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (host_id) REFERENCES users(id)
        )
    """)

    # グループメンバーテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(group_id, user_id)
        )
    """)

    # ユーザーチェックリストテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            checked BOOLEAN DEFAULT 0,
            checked_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, item_id)
        )
    """)

    # グループ招待テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            invited_by INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'declined')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (invited_by) REFERENCES users(id),
            UNIQUE(group_id, email)
        )
    """)

    # ミーティングテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            group_id INTEGER NOT NULL,
            host_id INTEGER NOT NULL,
            scheduled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (host_id) REFERENCES users(id)
        )
    """)

    # ミーティング参加者テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meeting_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(meeting_id, user_id)
        )
    """)

    # 録音・議事録テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            audio_file_path TEXT,
            transcript TEXT,
            summary TEXT,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # AI対話履歴テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_ai BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 学びのメモテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # フォローアップミーティングテーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS follow_up_meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_meeting_id INTEGER NOT NULL,
            follow_up_meeting_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (original_meeting_id) REFERENCES meetings(id),
            FOREIGN KEY (follow_up_meeting_id) REFERENCES meetings(id),
            UNIQUE(original_meeting_id, follow_up_meeting_id)
        )
    """)

    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

# ユーザー関連の関数

def create_user(name: str, email: str, password: str, role: str) -> Tuple[bool, str]:
    """新規ユーザーを作成"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        password_hash = hash_password(password)

        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, role)
        )
        conn.commit()
        conn.close()
        return True, "ユーザー登録が完了しました"
    except sqlite3.IntegrityError:
        return False, "このメールアドレスは既に登録されています"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """ユーザー認証"""
    conn = get_connection()
    cursor = conn.cursor()
    password_hash = hash_password(password)

    cursor.execute(
        "SELECT * FROM users WHERE email = ? AND password_hash = ?",
        (email, password_hash)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)
    return None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """ユーザーIDからユーザー情報を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)
    return None

def get_user_by_email(email: str) -> Optional[Dict]:
    """メールアドレスからユーザー情報を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)
    return None

# グループ関連の関数

def create_group(name: str, description: str, host_id: int) -> Tuple[bool, str, Optional[int]]:
    """新規グループを作成"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO groups (name, description, host_id) VALUES (?, ?, ?)",
            (name, description, host_id)
        )
        group_id = cursor.lastrowid

        # ホストを自動的にグループメンバーに追加
        cursor.execute(
            "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
            (group_id, host_id)
        )

        conn.commit()
        conn.close()
        return True, "グループを作成しました", group_id
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}", None

def get_groups_by_host(host_id: int) -> List[Dict]:
    """ホストが作成したグループ一覧を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.*, COUNT(gm.user_id) as member_count
        FROM groups g
        LEFT JOIN group_members gm ON g.id = gm.group_id
        WHERE g.host_id = ?
        GROUP BY g.id
        ORDER BY g.created_at DESC
    """, (host_id,))
    groups = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return groups

def get_groups_by_member(user_id: int) -> List[Dict]:
    """ユーザーが参加しているグループ一覧を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.*, u.name as host_name, COUNT(gm2.user_id) as member_count
        FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        JOIN users u ON g.host_id = u.id
        LEFT JOIN group_members gm2 ON g.id = gm2.group_id
        WHERE gm.user_id = ?
        GROUP BY g.id
        ORDER BY gm.joined_at DESC
    """, (user_id,))
    groups = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return groups

def get_group_by_id(group_id: int) -> Optional[Dict]:
    """グループIDからグループ情報を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.*, u.name as host_name
        FROM groups g
        JOIN users u ON g.host_id = u.id
        WHERE g.id = ?
    """, (group_id,))
    group = cursor.fetchone()
    conn.close()

    if group:
        return dict(group)
    return None

def get_group_members(group_id: int) -> List[Dict]:
    """グループメンバー一覧を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.name, u.email, u.role, gm.joined_at
        FROM group_members gm
        JOIN users u ON gm.user_id = u.id
        WHERE gm.group_id = ?
        ORDER BY gm.joined_at ASC
    """, (group_id,))
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return members

def invite_to_group(group_id: int, email: str, invited_by: int) -> Tuple[bool, str]:
    """グループに招待"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO group_invitations (group_id, email, invited_by) VALUES (?, ?, ?)",
            (group_id, email, invited_by)
        )
        conn.commit()
        conn.close()
        return True, "招待を送信しました"
    except sqlite3.IntegrityError:
        return False, "このメールアドレスは既に招待されています"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

def get_user_invitations(email: str) -> List[Dict]:
    """ユーザーへの招待一覧を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT gi.*, g.name as group_name, g.description, u.name as invited_by_name
        FROM group_invitations gi
        JOIN groups g ON gi.group_id = g.id
        JOIN users u ON gi.invited_by = u.id
        WHERE gi.email = ? AND gi.status = 'pending'
        ORDER BY gi.created_at DESC
    """, (email,))
    invitations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return invitations

def accept_invitation(invitation_id: int, user_id: int) -> Tuple[bool, str]:
    """招待を承認してグループに参加"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 招待情報を取得
        cursor.execute("SELECT * FROM group_invitations WHERE id = ?", (invitation_id,))
        invitation = cursor.fetchone()

        if not invitation:
            return False, "招待が見つかりません"

        if invitation['status'] != 'pending':
            return False, "この招待は既に処理されています"

        # グループメンバーに追加
        cursor.execute(
            "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
            (invitation['group_id'], user_id)
        )

        # 招待ステータスを更新
        cursor.execute(
            "UPDATE group_invitations SET status = 'accepted' WHERE id = ?",
            (invitation_id,)
        )

        conn.commit()
        conn.close()
        return True, "グループに参加しました"
    except sqlite3.IntegrityError:
        return False, "既にこのグループに参加しています"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

def decline_invitation(invitation_id: int) -> Tuple[bool, str]:
    """招待を辞退"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE group_invitations SET status = 'declined' WHERE id = ?",
            (invitation_id,)
        )
        conn.commit()
        conn.close()
        return True, "招待を辞退しました"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

# チェックリスト関連の関数

def save_checklist_item(user_id: int, item_id: str, checked: bool) -> bool:
    """チェックリスト項目を保存"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if checked:
            checked_at = datetime.now().isoformat()
        else:
            checked_at = None

        cursor.execute("""
            INSERT INTO user_checklists (user_id, item_id, checked, checked_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, item_id)
            DO UPDATE SET checked = ?, checked_at = ?
        """, (user_id, item_id, checked, checked_at, checked, checked_at))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving checklist: {e}")
        return False

def load_user_checklist(user_id: int) -> Dict[str, bool]:
    """ユーザーのチェックリストを読み込み"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT item_id, checked FROM user_checklists WHERE user_id = ?",
        (user_id,)
    )
    checklist = {row['item_id']: bool(row['checked']) for row in cursor.fetchall()}
    conn.close()
    return checklist

def get_group_progress(group_id: int) -> List[Dict]:
    """グループメンバーの進捗を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            u.id,
            u.name,
            u.email,
            COUNT(CASE WHEN uc.checked = 1 THEN 1 END) as completed_items,
            COUNT(uc.item_id) as total_tracked_items
        FROM group_members gm
        JOIN users u ON gm.user_id = u.id
        LEFT JOIN user_checklists uc ON u.id = uc.user_id
        WHERE gm.group_id = ?
        GROUP BY u.id
        ORDER BY u.name
    """, (group_id,))
    progress = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return progress

# ミーティング関連の関数

def create_meeting(title: str, description: str, group_id: int, host_id: int, scheduled_at: str) -> Tuple[bool, str, Optional[int]]:
    """新規ミーティングを作成"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO meetings (title, description, group_id, host_id, scheduled_at) VALUES (?, ?, ?, ?, ?)",
            (title, description, group_id, host_id, scheduled_at)
        )
        meeting_id = cursor.lastrowid

        # グループメンバーを自動的に参加者に追加
        cursor.execute("""
            INSERT INTO meeting_participants (meeting_id, user_id)
            SELECT ?, user_id FROM group_members WHERE group_id = ?
        """, (meeting_id, group_id))

        conn.commit()
        conn.close()
        return True, "ミーティングを作成しました", meeting_id
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}", None

def get_meetings_by_group(group_id: int) -> List[Dict]:
    """グループのミーティング一覧を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, u.name as host_name, COUNT(mp.user_id) as participant_count
        FROM meetings m
        JOIN users u ON m.host_id = u.id
        LEFT JOIN meeting_participants mp ON m.id = mp.meeting_id
        WHERE m.group_id = ?
        GROUP BY m.id
        ORDER BY m.scheduled_at DESC, m.created_at DESC
    """, (group_id,))
    meetings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return meetings

def get_meetings_by_user(user_id: int) -> List[Dict]:
    """ユーザーが参加するミーティング一覧を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, u.name as host_name, g.name as group_name, COUNT(mp2.user_id) as participant_count
        FROM meetings m
        JOIN meeting_participants mp ON m.id = mp.meeting_id
        JOIN users u ON m.host_id = u.id
        JOIN groups g ON m.group_id = g.id
        LEFT JOIN meeting_participants mp2 ON m.id = mp2.meeting_id
        WHERE mp.user_id = ?
        GROUP BY m.id
        ORDER BY m.scheduled_at DESC, m.created_at DESC
    """, (user_id,))
    meetings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return meetings

def get_meeting_by_id(meeting_id: int) -> Optional[Dict]:
    """ミーティングIDからミーティング情報を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, u.name as host_name, g.name as group_name
        FROM meetings m
        JOIN users u ON m.host_id = u.id
        JOIN groups g ON m.group_id = g.id
        WHERE m.id = ?
    """, (meeting_id,))
    meeting = cursor.fetchone()
    conn.close()

    if meeting:
        return dict(meeting)
    return None

def get_meeting_participants(meeting_id: int) -> List[Dict]:
    """ミーティング参加者一覧を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.name, u.email, u.role, mp.joined_at
        FROM meeting_participants mp
        JOIN users u ON mp.user_id = u.id
        WHERE mp.meeting_id = ?
        ORDER BY mp.joined_at ASC
    """, (meeting_id,))
    participants = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return participants

def save_recording(meeting_id: int, audio_file_path: Optional[str], transcript: str, created_by: int) -> Tuple[bool, str, Optional[int]]:
    """録音・議事録を保存"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 既存の録音があるか確認
        cursor.execute("SELECT id FROM recordings WHERE meeting_id = ?", (meeting_id,))
        existing = cursor.fetchone()

        if existing:
            # 更新
            cursor.execute("""
                UPDATE recordings
                SET audio_file_path = ?, transcript = ?, updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ?
            """, (audio_file_path, transcript, meeting_id))
            recording_id = existing['id']
            message = "議事録を更新しました"
        else:
            # 新規作成
            cursor.execute(
                "INSERT INTO recordings (meeting_id, audio_file_path, transcript, created_by) VALUES (?, ?, ?, ?)",
                (meeting_id, audio_file_path, transcript, created_by)
            )
            recording_id = cursor.lastrowid
            message = "議事録を保存しました"

        conn.commit()
        conn.close()
        return True, message, recording_id
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}", None

def get_recording_by_meeting(meeting_id: int) -> Optional[Dict]:
    """ミーティングの録音・議事録を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, u.name as created_by_name
        FROM recordings r
        JOIN users u ON r.created_by = u.id
        WHERE r.meeting_id = ?
    """, (meeting_id,))
    recording = cursor.fetchone()
    conn.close()

    if recording:
        return dict(recording)
    return None

def update_recording_summary(meeting_id: int, summary: str) -> Tuple[bool, str]:
    """議事録のサマリーを更新"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE recordings
            SET summary = ?, updated_at = CURRENT_TIMESTAMP
            WHERE meeting_id = ?
        """, (summary, meeting_id))
        conn.commit()
        conn.close()
        return True, "サマリーを更新しました"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

# AI対話関連の関数

def save_chat_message(meeting_id: int, user_id: int, message: str, is_ai: bool = False) -> Tuple[bool, str]:
    """チャットメッセージを保存"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (meeting_id, user_id, message, is_ai) VALUES (?, ?, ?, ?)",
            (meeting_id, user_id, message, is_ai)
        )
        conn.commit()
        conn.close()
        return True, "メッセージを保存しました"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

def get_chat_history(meeting_id: int) -> List[Dict]:
    """チャット履歴を取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ch.*, u.name as user_name
        FROM chat_history ch
        JOIN users u ON ch.user_id = u.id
        WHERE ch.meeting_id = ?
        ORDER BY ch.created_at ASC
    """, (meeting_id,))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history

def generate_ai_response(meeting_id: int, user_message: str) -> str:
    """模擬AI応答を生成"""
    import random

    # 議事録を取得してコンテキストとして使用
    recording = get_recording_by_meeting(meeting_id)
    transcript = recording['transcript'] if recording and recording['transcript'] else ""

    # キーワードベースの簡単な応答ロジック
    user_message_lower = user_message.lower()

    if "詳しく" in user_message or "もっと" in user_message or "教えて" in user_message:
        responses = [
            f"議事録を確認したところ、その部分について説明いたします。{transcript[:100] if transcript else 'まだ議事録が入力されていませんが、'}一般的には、AIの学習では基礎から応用まで段階的に理解を深めることが重要です。",
            "その点についてですが、シニアの方々がAIを学ぶ際は、まず実際に使ってみることが大切です。失敗を恐れず、気軽に試してみましょう。",
            "良い質問ですね。AIを活用する上では、具体的な例から学ぶのが効果的です。例えば、日常の困りごとをAIに相談してみるなど、身近なことから始めてみてください。"
        ]
    elif "どう" in user_message or "方法" in user_message or "やり方" in user_message:
        responses = [
            "その方法ですが、まずは簡単なことから始めるのがおすすめです。例えば、AIに「今日の天気を教えて」といった質問から始めて、徐々に複雑な質問に挑戦していきましょう。",
            "手順としては、①まず試してみる、②うまくいかなかったら質問の仕方を変えてみる、③成功したパターンを覚えておく、という流れが効果的です。",
            "実践的な方法として、ミーティングで学んだことを日常生活で使ってみることをお勧めします。繰り返し使うことで自然と身につきます。"
        ]
    elif "例" in user_message or "具体的" in user_message:
        responses = [
            "具体例をいくつか挙げますと、①レシピの検索、②健康に関する質問、③旅行の計画、④メールの文章作成などがあります。どれも日常的に使える便利な機能です。",
            "例えば、「高血圧に良い食事を教えて」「孫へのお誕生日メッセージを考えて」「東京の桜の名所を教えて」といった質問ができます。",
            "実際の使用例として、料理中に「この食材の代わりになるものは？」と聞いたり、「この文章を丁寧な言い方に直して」とお願いしたりできます。"
        ]
    elif "わからない" in user_message or "難しい" in user_message:
        responses = [
            "大丈夫です、最初は誰でも難しく感じます。まずは簡単なことから一つずつ覚えていけば、必ずできるようになります。焦らずゆっくり学んでいきましょう。",
            "難しいと感じたら、いつでもグループのメンバーやホストに相談してくださいね。一人で悩まず、みんなで助け合いながら学習を進めましょう。",
            "わからないことがあるのは当然です。次のミーティングでその点を重点的に学習することもできますので、遠慮なく質問してください。"
        ]
    elif "ありがとう" in user_message or "感謝" in user_message:
        responses = [
            "どういたしまして！引き続き学習を楽しんでくださいね。わからないことがあれば、いつでも質問してください。",
            "お役に立てて嬉しいです。これからも一緒にAIの活用方法を学んでいきましょう！",
            "こちらこそ、積極的に学習されている姿勢が素晴らしいです。この調子で続けてください！"
        ]
    else:
        responses = [
            f"ご質問ありがとうございます。議事録によると、{transcript[:100] if transcript else 'ミーティングでは様々なことを学びました。'}具体的にどの部分について詳しく知りたいですか？",
            "その点について考えてみましょう。AIの学習では、実践を重ねることが一番の近道です。まずは気軽に試してみることをお勧めします。",
            "良い着眼点ですね。ミーティングで学んだことを復習しながら、少しずつスキルアップしていきましょう。何か具体的に知りたいことはありますか？"
        ]

    return random.choice(responses)

# 学びのメモ関連の関数

def save_learning_note(meeting_id: int, user_id: int, note: str) -> Tuple[bool, str]:
    """学びのメモを保存"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 既存のメモがあるか確認
        cursor.execute(
            "SELECT id FROM learning_notes WHERE meeting_id = ? AND user_id = ?",
            (meeting_id, user_id)
        )
        existing = cursor.fetchone()

        if existing:
            # 更新
            cursor.execute("""
                UPDATE learning_notes
                SET note = ?, updated_at = CURRENT_TIMESTAMP
                WHERE meeting_id = ? AND user_id = ?
            """, (note, meeting_id, user_id))
            message = "学びのメモを更新しました"
        else:
            # 新規作成
            cursor.execute(
                "INSERT INTO learning_notes (meeting_id, user_id, note) VALUES (?, ?, ?)",
                (meeting_id, user_id, note)
            )
            message = "学びのメモを保存しました"

        conn.commit()
        conn.close()
        return True, message
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

def get_learning_notes(meeting_id: int) -> List[Dict]:
    """ミーティングの学びのメモを取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ln.*, u.name as user_name
        FROM learning_notes ln
        JOIN users u ON ln.user_id = u.id
        WHERE ln.meeting_id = ?
        ORDER BY ln.created_at DESC
    """, (meeting_id,))
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes

def get_user_learning_note(meeting_id: int, user_id: int) -> Optional[Dict]:
    """ユーザーの学びのメモを取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM learning_notes
        WHERE meeting_id = ? AND user_id = ?
    """, (meeting_id, user_id))
    note = cursor.fetchone()
    conn.close()

    if note:
        return dict(note)
    return None

# フォローアップミーティング関連の関数

def create_follow_up_meeting(original_meeting_id: int, follow_up_meeting_id: int) -> Tuple[bool, str]:
    """フォローアップミーティングを関連付け"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO follow_up_meetings (original_meeting_id, follow_up_meeting_id) VALUES (?, ?)",
            (original_meeting_id, follow_up_meeting_id)
        )
        conn.commit()
        conn.close()
        return True, "フォローアップミーティングを設定しました"
    except sqlite3.IntegrityError:
        return False, "既に設定されています"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

def get_follow_up_meeting(original_meeting_id: int) -> Optional[Dict]:
    """元のミーティングのフォローアップを取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, u.name as host_name, g.name as group_name
        FROM follow_up_meetings fm
        JOIN meetings m ON fm.follow_up_meeting_id = m.id
        JOIN users u ON m.host_id = u.id
        JOIN groups g ON m.group_id = g.id
        WHERE fm.original_meeting_id = ?
    """, (original_meeting_id,))
    meeting = cursor.fetchone()
    conn.close()

    if meeting:
        return dict(meeting)
    return None

def get_original_meeting(follow_up_meeting_id: int) -> Optional[Dict]:
    """フォローアップの元のミーティングを取得"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, u.name as host_name, g.name as group_name
        FROM follow_up_meetings fm
        JOIN meetings m ON fm.original_meeting_id = m.id
        JOIN users u ON m.host_id = u.id
        JOIN groups g ON m.group_id = g.id
        WHERE fm.follow_up_meeting_id = ?
    """, (follow_up_meeting_id,))
    meeting = cursor.fetchone()
    conn.close()

    if meeting:
        return dict(meeting)
    return None

def get_upcoming_meetings(user_id: int, days_ahead: int = 7) -> List[Dict]:
    """今後のミーティングを取得"""
    from datetime import datetime, timedelta

    conn = get_connection()
    cursor = conn.cursor()

    # 現在時刻とN日後の時刻
    now = datetime.now().isoformat()
    future = (datetime.now() + timedelta(days=days_ahead)).isoformat()

    cursor.execute("""
        SELECT m.*, u.name as host_name, g.name as group_name,
               COUNT(mp2.user_id) as participant_count
        FROM meetings m
        JOIN meeting_participants mp ON m.id = mp.meeting_id
        JOIN users u ON m.host_id = u.id
        JOIN groups g ON m.group_id = g.id
        LEFT JOIN meeting_participants mp2 ON m.id = mp2.meeting_id
        WHERE mp.user_id = ?
          AND m.scheduled_at IS NOT NULL
          AND m.scheduled_at >= ?
          AND m.scheduled_at <= ?
        GROUP BY m.id
        ORDER BY m.scheduled_at ASC
    """, (user_id, now, future))
    meetings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return meetings

# データベース初期化
if __name__ == "__main__":
    init_database()
    print("データベースを初期化しました")

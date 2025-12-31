"""
データベース管理モジュール
ユーザー、グループ、チェックリストの永続化を管理
"""

import sqlite3
import hashlib
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from dotenv import load_dotenv
from openai import OpenAI

# 環境変数を読み込み
load_dotenv()

DB_FILE = "ai_literacy.db"

def get_openai_api_key() -> Optional[str]:
    """
    OpenAI APIキーを取得
    優先順位：
    1. st.secrets (Streamlit Cloud用)
    2. os.environ (ローカル.env用)
    """
    # Streamlit Cloudの場合
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            return st.secrets['OPENAI_API_KEY']
    except (ImportError, Exception):
        pass

    # ローカル環境の場合
    return os.getenv('OPENAI_API_KEY')

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

def generate_ai_response_with_gpt4o(meeting_id: int, user_message: str, chat_history: List[Dict] = None) -> Tuple[bool, str, str]:
    """
    GPT-4oを使って議事録に基づいたAI応答を生成

    Args:
        meeting_id: ミーティングID
        user_message: ユーザーの質問
        chat_history: 過去のチャット履歴

    Returns:
        (成功, メッセージ, AI応答)
    """
    try:
        # APIキーを取得
        api_key = get_openai_api_key()
        if not api_key:
            return False, "OPENAI_API_KEYが設定されていません。", ""

        # OpenAIクライアントを初期化
        client = OpenAI(api_key=api_key)

        # 議事録を取得
        recording = get_recording_by_meeting(meeting_id)
        transcript = recording['transcript'] if recording and recording['transcript'] else ""
        summary = recording['summary'] if recording and recording['summary'] else ""

        # システムプロンプトを構築（シニア向け、議事録コンテキスト付き）
        system_prompt = f"""あなたは高齢者向けのAI学習会をサポートする優しいアシスタントです。
以下の議事録の内容に基づいて、ユーザーの質問に答えてください。

【重要な注意点】
- 高齢者にもわかりやすい、丁寧で優しい言葉を使ってください
- 専門用語は避け、必要な場合は簡単な説明を添えてください
- 回答は簡潔にまとめ、箇条書きなどを活用して見やすくしてください
- 議事録に関係ない質問でも、親切に対応してください
- 励ましの言葉を適度に入れてください

【議事録の内容】
{summary if summary else transcript if transcript else '（議事録はまだ作成されていません）'}

【文字起こしテキスト】
{transcript[:2000] if transcript else '（文字起こしはまだありません）'}
"""

        # メッセージを構築
        messages = [{"role": "system", "content": system_prompt}]

        # チャット履歴があれば追加（最新10件まで）
        if chat_history:
            for msg in chat_history[-10:]:
                role = "assistant" if msg.get('is_ai') else "user"
                messages.append({"role": role, "content": msg['message']})

        # ユーザーの新しい質問を追加
        messages.append({"role": "user", "content": user_message})

        # GPT-4oで応答を生成
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        ai_response = response.choices[0].message.content.strip()

        return True, "応答を生成しました", ai_response

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower():
            return False, "OpenAI APIキーが無効です。設定を確認してください。", ""
        return False, f"エラーが発生しました: {error_msg}", ""


def generate_ai_response(meeting_id: int, user_message: str) -> str:
    """
    AI応答を生成（後方互換性のためのラッパー関数）
    GPT-4oを使用し、失敗した場合はフォールバック応答を返す
    """
    # チャット履歴を取得
    chat_history = get_chat_history(meeting_id)

    # GPT-4oで応答を生成
    success, message, ai_response = generate_ai_response_with_gpt4o(meeting_id, user_message, chat_history)

    if success:
        return ai_response

    # フォールバック応答（API接続失敗時）
    recording = get_recording_by_meeting(meeting_id)
    transcript = recording['transcript'] if recording and recording['transcript'] else ""

    fallback_responses = [
        f"申し訳ありません。現在AIとの接続に問題が発生しています。\n\n議事録の内容を確認したいときは、「📝 議事録」タブをご覧ください。\n\n({message})",
        f"ただいまAIが応答できない状態です。しばらくお待ちいただいてから、もう一度お試しください。\n\n({message})"
    ]

    import random
    return random.choice(fallback_responses)


def clear_chat_history(meeting_id: int) -> Tuple[bool, str]:
    """
    ミーティングのチャット履歴をクリア

    Args:
        meeting_id: ミーティングID

    Returns:
        (成功, メッセージ)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE meeting_id = ?", (meeting_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return True, f"チャット履歴をクリアしました（{deleted_count}件削除）"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"


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

def transcribe_audio_with_whisper(audio_file_path: str) -> Tuple[bool, str, Optional[str]]:
    """
    Whisper APIを使って音声ファイルを文字起こし

    Args:
        audio_file_path: 音声ファイルのパス

    Returns:
        (成功, メッセージ, 文字起こしテキスト)
    """
    try:
        # APIキーを取得（Streamlit Cloud優先）
        api_key = get_openai_api_key()
        if not api_key:
            return False, "OPENAI_API_KEYが設定されていません。Streamlit Cloudの場合はSecretsに、ローカルの場合は.envファイルに設定してください。", None

        # OpenAIクライアントを初期化
        client = OpenAI(api_key=api_key)

        # ファイルサイズチェック（25MB = 26,214,400 bytes）
        file_size = os.path.getsize(audio_file_path)
        max_size = 25 * 1024 * 1024  # 25MB

        if file_size > max_size:
            return False, f"ファイルサイズが大きすぎます（上限25MB）。現在のサイズ: {file_size / (1024*1024):.1f}MB", None

        # 音声ファイルを開いて文字起こし
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ja"  # 日本語に指定
            )

        return True, "文字起こしが完了しました", transcript.text

    except FileNotFoundError:
        return False, f"音声ファイルが見つかりません: {audio_file_path}", None
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower():
            return False, "OpenAI APIキーが無効です。.envファイルを確認してください。", None
        return False, f"文字起こし中にエラーが発生しました: {error_msg}", None

def save_audio_and_transcribe(meeting_id: int, audio_file, created_by: int) -> Tuple[bool, str, Optional[str]]:
    """
    音声ファイルを保存してWhisper APIで文字起こし、議事録として保存

    Args:
        meeting_id: ミーティングID
        audio_file: Streamlitのアップロードファイルオブジェクト
        created_by: 作成者のユーザーID

    Returns:
        (成功, メッセージ, 文字起こしテキスト)
    """
    try:
        # アップロードディレクトリを作成
        upload_dir = "audio_uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # ファイル名を生成（ミーティングID + タイムスタンプ + 元のファイル名）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio_file.name)[1]
        safe_filename = f"meeting_{meeting_id}_{timestamp}{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)

        # ファイルを保存
        with open(file_path, "wb") as f:
            f.write(audio_file.getbuffer())

        # Whisper APIで文字起こし
        success, message, transcript = transcribe_audio_with_whisper(file_path)

        if not success:
            # エラーの場合、保存したファイルを削除
            if os.path.exists(file_path):
                os.remove(file_path)
            return False, message, None

        # 議事録としてデータベースに保存
        save_success, save_message, _ = save_recording(meeting_id, file_path, transcript, created_by)

        if not save_success:
            # データベース保存失敗の場合、ファイルを削除
            if os.path.exists(file_path):
                os.remove(file_path)
            return False, f"議事録の保存に失敗しました: {save_message}", None

        return True, "音声ファイルの文字起こしと議事録保存が完了しました", transcript

    except Exception as e:
        return False, f"処理中にエラーが発生しました: {str(e)}", None

def generate_minutes_with_gpt4o(transcript: str) -> Tuple[bool, str, Optional[str]]:
    """
    GPT-4oを使って文字起こしから議事録を自動生成

    Args:
        transcript: 文字起こしテキスト

    Returns:
        (成功, メッセージ, 整形された議事録)
    """
    try:
        # APIキーを取得（Streamlit Cloud優先）
        api_key = get_openai_api_key()
        if not api_key:
            return False, "OPENAI_API_KEYが設定されていません。Streamlit Cloudの場合はSecretsに、ローカルの場合は.envファイルに設定してください。", None

        # OpenAIクライアントを初期化
        client = OpenAI(api_key=api_key)

        # プロンプトを構築（シニア向けにわかりやすく）
        prompt = f"""
以下は会議の文字起こしテキストです。このテキストから、高齢者にもわかりやすい議事録を作成してください。

【文字起こし】
{transcript}

【議事録フォーマット】
以下の形式で議事録を作成してください：

## 📝 会議の要約
（会議の内容を3-5文で簡潔にまとめてください。高齢者にもわかりやすい言葉を使用してください。）

## 📌 主要なトピック
- （重要なトピック1）
- （重要なトピック2）
- （重要なトピック3）
（必要に応じて追加してください）

## ✅ 決定事項
- （決定事項1）
- （決定事項2）
（決定事項がない場合は「特になし」と記載してください）

## 🔄 次回への申し送り事項
- （申し送り事項1）
- （申し送り事項2）
（申し送り事項がない場合は「特になし」と記載してください）

重要：
- 専門用語は避け、平易な日本語を使用してください
- 箇条書きは簡潔にまとめてください
- 高齢者の方々が読みやすいように配慮してください
"""

        # GPT-4oで議事録を生成
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは高齢者向けのAI学習会の議事録作成アシスタントです。わかりやすく、丁寧な言葉で議事録を作成してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        formatted_minutes = response.choices[0].message.content.strip()

        return True, "議事録の生成が完了しました", formatted_minutes

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower():
            return False, "OpenAI APIキーが無効です。.envファイルを確認してください。", None
        return False, f"議事録生成中にエラーが発生しました: {error_msg}", None

def save_formatted_minutes(meeting_id: int, formatted_minutes: str) -> Tuple[bool, str]:
    """
    整形された議事録をデータベースに保存

    Args:
        meeting_id: ミーティングID
        formatted_minutes: 整形された議事録

    Returns:
        (成功, メッセージ)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE recordings
            SET summary = ?, updated_at = CURRENT_TIMESTAMP
            WHERE meeting_id = ?
        """, (formatted_minutes, meeting_id))

        conn.commit()
        conn.close()

        return True, "議事録を保存しました"
    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

# メール送信関連の関数

def get_email_config() -> Tuple[Optional[str], Optional[str]]:
    """
    メール設定を取得
    優先順位：
    1. st.secrets (Streamlit Cloud用)
    2. os.environ (ローカル.env用)

    Returns:
        (メールアドレス, アプリパスワード)
    """
    email_address = None
    email_password = None

    # Streamlit Cloudの場合
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            if 'EMAIL_ADDRESS' in st.secrets:
                email_address = st.secrets['EMAIL_ADDRESS']
            if 'EMAIL_PASSWORD' in st.secrets:
                email_password = st.secrets['EMAIL_PASSWORD']
    except (ImportError, Exception):
        pass

    # ローカル環境の場合（未設定の場合のみ）
    if not email_address:
        email_address = os.getenv('EMAIL_ADDRESS')
    if not email_password:
        email_password = os.getenv('EMAIL_PASSWORD')

    return email_address, email_password

def send_minutes_email(
    meeting_id: int,
    meeting_title: str,
    scheduled_at: str,
    minutes_content: str,
    recipients: List[Dict]
) -> Tuple[bool, str, List[str], List[str]]:
    """
    議事録をメールで参加者に送信

    Args:
        meeting_id: ミーティングID
        meeting_title: ミーティングタイトル
        scheduled_at: 開催日時
        minutes_content: 議事録の内容
        recipients: 送信先リスト [{'name': '名前', 'email': 'メールアドレス'}, ...]

    Returns:
        (成功, メッセージ, 送信成功リスト, 送信失敗リスト)
    """
    # メール設定を取得
    sender_email, sender_password = get_email_config()

    if not sender_email or not sender_password:
        return False, "メール設定が見つかりません。EMAIL_ADDRESS と EMAIL_PASSWORD を設定してください。", [], []

    # 日時の整形
    try:
        dt = datetime.fromisoformat(scheduled_at)
        formatted_date = dt.strftime('%Y年%m月%d日 %H:%M')
    except:
        formatted_date = scheduled_at

    # 送信結果を追跡
    success_list = []
    failed_list = []

    # Gmail SMTPサーバーに接続
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
    except smtplib.SMTPAuthenticationError:
        return False, "メールの認証に失敗しました。EMAIL_ADDRESS と EMAIL_PASSWORD（Gmailアプリパスワード）を確認してください。", [], []
    except Exception as e:
        return False, f"メールサーバーへの接続に失敗しました: {str(e)}", [], []

    # 各受信者にメールを送信
    for recipient in recipients:
        try:
            # メールを作成
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"【議事録】{meeting_title}"
            msg['From'] = sender_email
            msg['To'] = recipient['email']

            # プレーンテキスト版のメール本文（高齢者向けにわかりやすく）
            text_body = f"""
{recipient['name']} 様

お疲れ様です。
以下のミーティングの議事録をお送りいたします。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 ミーティング名：{meeting_title}
📆 開催日時：{formatted_date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{minutes_content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

このメールは自動送信されています。
ご不明な点がございましたら、ホストにお問い合わせください。

AI学習チェックリスト
            """

            # HTML版のメール本文（より見やすいフォーマット）
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'メイリオ', 'ヒラギノ角ゴ Pro W3', sans-serif;
            font-size: 18px;
            line-height: 1.8;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .meeting-info {{
            background-color: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border-left: 5px solid #007bff;
            margin-bottom: 30px;
        }}
        .meeting-info p {{
            margin: 10px 0;
            font-size: 20px;
        }}
        .minutes-content {{
            background-color: #fff;
            padding: 30px;
            border-radius: 15px;
            border: 2px solid #dee2e6;
            margin-bottom: 30px;
        }}
        .footer {{
            text-align: center;
            color: #6c757d;
            font-size: 16px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 議事録のお知らせ</h1>
    </div>

    <p style="font-size: 22px;"><strong>{recipient['name']}</strong> 様</p>
    <p>お疲れ様です。<br>以下のミーティングの議事録をお送りいたします。</p>

    <div class="meeting-info">
        <p>📅 <strong>ミーティング名：</strong>{meeting_title}</p>
        <p>📆 <strong>開催日時：</strong>{formatted_date}</p>
    </div>

    <div class="minutes-content">
        {minutes_content.replace(chr(10), '<br>')}
    </div>

    <div class="footer">
        <p>このメールは自動送信されています。<br>
        ご不明な点がございましたら、ホストにお問い合わせください。</p>
        <p><strong>AI学習チェックリスト</strong></p>
    </div>
</body>
</html>
            """

            # プレーンテキストとHTMLを追加
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)

            # メール送信
            server.send_message(msg)
            success_list.append(recipient['email'])

        except Exception as e:
            failed_list.append(f"{recipient['email']} ({str(e)})")

    # サーバー接続を閉じる
    server.quit()

    # 結果メッセージを作成
    if len(failed_list) == 0:
        result_message = f"✅ {len(success_list)}名全員にメールを送信しました！"
        return True, result_message, success_list, failed_list
    elif len(success_list) == 0:
        result_message = f"❌ メールの送信に失敗しました"
        return False, result_message, success_list, failed_list
    else:
        result_message = f"⚠️ {len(success_list)}名に送信成功、{len(failed_list)}名に送信失敗"
        return True, result_message, success_list, failed_list


# データベース初期化
if __name__ == "__main__":
    init_database()
    print("データベースを初期化しました")

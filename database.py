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

# データベース初期化
if __name__ == "__main__":
    init_database()
    print("データベースを初期化しました")

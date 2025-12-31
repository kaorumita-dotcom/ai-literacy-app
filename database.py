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

# データベース初期化
if __name__ == "__main__":
    init_database()
    print("データベースを初期化しました")

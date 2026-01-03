# Digital Nagaya v2 開発ログ - 2026年1月3日

## 本日の作業内容

### Replitでのアプリ構築

#### Step 1: プロジェクト作成
- Replit（https://replit.com）にログイン
- 新しいUIで「App」タブから開始
- 設計書のプロンプトを貼り付け

#### Step 2: Replit Agentによる自動構築
- Agentがプロンプトを解析
- OpenAI管理インテグレーションは「Dismiss」（自分のAPIキーを使用）
- 約12分で構築完了（10/10タスク）

#### 構築されたもの
- Flask + PostgreSQL + SQLAlchemy
- 認証システム（ユーザー登録・ログイン）
- セッション管理（作成・予約・キャンセル）
- 議事録アップロード・AI生成
- AIおしゃべり（Web Speech API）
- CSRF保護追加
- 非公開セッションのアクセス制御

#### Step 3: Secrets（環境変数）設定
| Secret | 用途 |
|--------|------|
| OPENAI_API_KEY | AI機能（議事録要約・AIチャット） |
| EMAIL_ADDRESS | 議事録メール送信の送信元アドレス |
| EMAIL_PASSWORD | Gmailアプリパスワード |
| SECRET_KEY | Flask暗号化用キー |

## 完成したアプリ

### URL
**https://nagaya-ai--kaorumita.replit.app**

### 機能一覧
- ✅ ユーザー登録・ログイン（host/participant）
- ✅ セッション作成・編集・キャンセル
- ✅ セッション予約・キャンセル
- ✅ 議事録アップロード（Nottaからコピペ）
- ✅ AI議事録生成（GPT-4o）
- ✅ 議事録メール送信
- ✅ AIおしゃべり（音声対話対応）
- ✅ フォローアップセッション
- ✅ 自動リマインダー（APScheduler）

## 明日のタスク

### テスト項目
1. 新規登録（host / participant）
2. ログイン
3. セッション作成（hostとして）
4. セッション予約（participantとして）
5. 議事録アップロード → AI議事録生成
6. AIおしゃべり（音声対話）
7. メール送信テスト

## 技術構成（確定）

| 項目 | 技術 |
|------|------|
| Backend | Python 3.11+ / Flask |
| Database | PostgreSQL（Replit組み込み） |
| Frontend | Jinja2 + Bootstrap 5 + JavaScript |
| AI | OpenAI API（GPT-4o） |
| Email | Gmail SMTP |
| 音声 | Web Speech API |
| 文字起こし | Notta（手動コピー＆ペースト） |
| ホスティング | Replit |

## 月額コスト（見込み）

| サービス | 月額 |
|---------|------|
| Notta プレミアム | ¥1,980 |
| OpenAI API | 〜¥500 |
| **合計** | **約¥2,500** |

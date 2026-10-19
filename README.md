# google-meet-link-creator

Google Meet REST API を使って、新しいオンライン会議を作成し、参加リンクを表示する Python プログラムです。

- 実行するだけで、新しい会議のリンクが1つ作られます（入力はありません）
- 招待されていない人がリンクを開くと「参加をリクエスト」になり、主催者（自分）が承認すると入れます（個人の Gmail の既定の設定）
- 自分の Google アカウントでログインする OAuth 方式を使っています

## しくみ

1. OAuth で自分の Google アカウントにログインする（2回目からは `token.json` を使う）
2. Meet API の `spaces.create` で**会議スペース**（Meet の「会議室」のようなもの）を作る。
   参加の方法（`accessType`）は指定せず、アカウントの既定の設定に任せる（下の「注意」を参照）
3. Google から返ってきた**参加リンク**（`meetingUri`）と**会議コード**（`meetingCode`）を表示する

## ファイル構成

```
google-meet-link-creator/
├── main.py            # プログラム本体
├── README.md          # このファイル
├── 要件定義書.md       # 要件定義書
└── .gitignore         # GitHub に載せないファイルの一覧
```

次の2つのファイルは、秘密の情報なのでリポジトリには含めていません。

| ファイル | 内容 | 用意の仕方 |
|---|---|---|
| `credentials.json` | OAuth クライアントの鍵 | 下の「事前準備」の手順で各自作成して置く |
| `token.json` | ログインしたときにできる許可証 | 初回ログインで自動で作られる |

## 必要な環境

- Python 3
- Google アカウント（個人の Gmail で使えます）
- Google Cloud のプロジェクト

## 事前準備（Google Cloud Console で行う）

1. [Google Cloud Console](https://console.cloud.google.com/) で、使うプロジェクトを選ぶ
2. **Google Meet REST API** を有効にする
   - 「API とサービス」→「ライブラリ」で `Google Meet REST API` を検索して「有効にする」
3. **OAuth 同意画面**を設定する
   - 対象：**外部**
   - テストユーザー：自分の Gmail アドレスを追加する
4. **OAuth クライアントID** を作成する
   - 「API とサービス」→「認証情報」→「認証情報を作成」→「OAuth クライアントID」
   - アプリケーションの種類：**デスクトップアプリ**
5. 作成したクライアントの JSON をダウンロードし、名前を `credentials.json` に変えて、`main.py` と同じフォルダに置く

> 権限の範囲は `meetings.space.created`（このプログラムが作った会議だけを扱える）にしています。
> 既存の会議やカレンダーを読んだり書き換えたりすることはありません。

## インストール方法

1. このリポジトリをダウンロードする

   ```bash
   git clone https://github.com/m-tsuna/google-meet-link-creator.git
   cd google-meet-link-creator
   ```

2. 必要なライブラリをインストールする

   ```bash
   pip install google-api-python-client google-auth google-auth-oauthlib
   ```

3. 「事前準備」で用意した `credentials.json` を、`main.py` と同じフォルダに置く

## 使い方

1. ターミナルで実行する

   ```bash
   python main.py
   ```

2. 初回だけ、ブラウザで Google のログイン画面が開きます。ログインして「許可」を押してください
   - 「このアプリは Google で確認されていません」と表示された場合は、「続行」を押して進めます（自分で作ったテスト中のアプリのため）
   - 許可すると `token.json` が作られ、次回からはログインしなくても使えます

3. 作成した会議の参加リンクと会議コードが表示されます。リンクをブラウザで開くと会議に入れます

### 実行例

```
会議を作成しました。
参加リンク: https://meet.google.com/abc-defg-hij
会議コード: abc-defg-hij
参加の方法: 招待されていない人は、主催者の承認で参加できます（招待された人・組織内の人は承認なし）
```

## 注意

- 実行するたびに、新しい会議（別のリンク）が作られます。一度作ったリンクは、あとから何度でも使えます
- 参加の方法（`accessType`）を API で指定できるのは Google Workspace のアカウントだけです。個人の Gmail で指定すると `updateAccessType is not available to the user` というエラーになるため、指定していません
- OAuth 同意画面が「テスト中」の場合、ログインの有効期限は7日ほどです。期限が切れると、次に実行したときに自動でログイン画面が開きます
- 「Google Meet を操作する許可がありません」と出た場合は、Google Meet REST API が有効になっているか確認してください
- `credentials.json` と `token.json` は、自分のアカウントに入るための鍵と許可証です。他の人に渡したり、GitHub に載せたりしないでください（`.gitignore` で除外しています）

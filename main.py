"""
Google Meet 会議リンク作成プログラム（課題3：Google ミート API）

Google Meet REST API で新しい会議（会議スペース）を作成し、参加リンクを表示する。

使い方：ターミナルで  python main.py  を実行する。
"""

import sys
from pathlib import Path

from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ============================================================
# 設定（ここをまとめて書いておく）
# ============================================================

# このプログラム（main.py）が置いてあるフォルダ
BASE_DIR = Path(__file__).resolve().parent

# OAuth クライアントの鍵（Google Cloud Console からダウンロードしたもの）
CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# 初回ログインで自動で作られる許可証
TOKEN_FILE = BASE_DIR / "token.json"

# プログラムに許可する範囲。meetings.space.created は「このプログラムが作った会議だけ」を扱える
SCOPES = ["https://www.googleapis.com/auth/meetings.space.created"]

# 参加の方法（Google から返ってきた設定）を表示するときの日本語
# ※ 参加の方法を API で指定できるのは Google Workspace のアカウントだけ。
#    個人の Gmail で指定すると「updateAccessType is not available to the user」で失敗するため、
#    作成時には指定せず、アカウントの既定の設定に任せる
ACCESS_TYPE_LABELS = {
    "OPEN": "誰でも参加できます（リンクを知っていれば承認なしで入れます）",
    "TRUSTED": "招待されていない人は、主催者の承認で参加できます（招待された人・組織内の人は承認なし）",
    "RESTRICTED": "承認制（招待されていない人は、主催者の承認で参加できます）",
}


# ============================================================
# F1 ログイン（認証）
# ============================================================
def login():
    """
    Google にログインして、Meet を操作するための「サービス」を返す。

    1. token.json があれば、それを読み込む
    2. 期限切れで更新できるなら、自動で更新する
    3. token.json が無い・更新できない場合は、ブラウザでログイン画面を開く
    4. 許可されたら、次回のために token.json を保存する
    """
    creds = None

    # token.json があれば読み込む（壊れていたら無視して、ログインからやり直す）
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except ValueError:
            creds = None

    # 期限切れだが更新できる場合は、自動で更新する
    if creds and not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            # 同意画面が「テスト中」だと約7日で更新できなくなる → ログインし直す
            print("ログインの有効期限が切れていたため、もう一度ログインします。")
            creds = None

    # まだ使える許可証が無い場合は、ブラウザでログインする
    if not creds or not creds.valid:
        # credentials.json が無いとログインできないので、理由を表示して終了する（F4）
        if not CREDENTIALS_FILE.exists():
            show_error_and_exit(
                f"{CREDENTIALS_FILE.name} が見つかりません。\n"
                f"Google Cloud Console で OAuth クライアントID（デスクトップアプリ）を作成し、\n"
                f"ダウンロードした JSON を「{CREDENTIALS_FILE.name}」という名前で\n"
                f"次のフォルダに置いてください: {BASE_DIR}"
            )

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
        except ValueError:
            show_error_and_exit(
                f"{CREDENTIALS_FILE.name} の中身が正しくありません。\n"
                "OAuth クライアントID（デスクトップアプリ）の JSON をダウンロードし直してください。"
            )

        # ブラウザが開き、ログインして「許可」を押すと続きに進む
        creds = flow.run_local_server(port=0)

        # 次回からログインしなくていいように、許可証を保存する
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    # Meet を操作するための「サービス」を作って返す
    return build("meet", "v2", credentials=creds)


# ============================================================
# F2 会議の作成
# ============================================================
def create_meeting(service):
    """
    新しい会議スペース（Meet の「会議室」のようなもの）を作り、Google から返ってきた情報を返す。
    返ってくる情報には、参加リンク（meetingUri）・会議コード（meetingCode）・設定（config）が入っている。
    設定は指定しない（個人の Gmail では指定できないため。上の「設定」の説明を参照）。
    """
    return service.spaces().create(body={}).execute()


# ============================================================
# F3 結果の表示
# ============================================================
def show_result(space):
    """
    作った会議の参加リンク・会議コード・参加の方法を表示する。
    """
    access_type = space.get("config", {}).get("accessType", "")
    access_label = ACCESS_TYPE_LABELS.get(access_type, access_type)

    print("会議を作成しました。")
    print(f"参加リンク: {space['meetingUri']}")
    print(f"会議コード: {space['meetingCode']}")
    print(f"参加の方法: {access_label}")


# ============================================================
# F4 エラー表示
# ============================================================
def show_error_and_exit(message):
    """
    原因が分かる日本語のエラーメッセージを表示して、プログラムを終了する。
    """
    print(f"エラー: {message}", file=sys.stderr)
    sys.exit(1)


def explain_http_error(error):
    """
    Google とのやりとりで起きたエラー（HttpError）を、日本語の説明に直して返す。
    """
    # Meet API が有効になっていない、または権限が足りない
    if error.status_code == 403:
        return (
            "Google Meet を操作する許可がありません。\n"
            "Google Cloud Console の「API とサービス」→「ライブラリ」で\n"
            "「Google Meet REST API」が有効になっているか確認してください。\n"
            "有効になっている場合は、このアカウントでは使えない設定を指定している可能性があります。\n"
            f"詳細: {error.reason}"
        )
    return (
        "Google Meet とのやりとりに失敗しました。\n"
        f"ステータスコード: {error.status_code}\n"
        f"詳細: {error.reason}"
    )


# ============================================================
# メインの処理（上の関数を順番に呼ぶ）
# ============================================================
def main():
    """
    プログラム全体の流れ：
    ログイン → 会議の作成 → 結果の表示
    """
    try:
        # F1 ログイン
        service = login()

        # F2 会議の作成
        space = create_meeting(service)

        # F3 結果の表示
        show_result(space)

    except HttpError as error:
        # Google とのやりとりで失敗した（F4）
        show_error_and_exit(explain_http_error(error))
    except (TransportError, OSError) as error:
        # インターネットにつながらない など（F4）
        show_error_and_exit(
            "Google につながりませんでした。インターネット接続を確認してください。\n"
            f"詳細: {error}"
        )
    except KeyboardInterrupt:
        # Ctrl + C で途中でやめた場合（ログインの待ち中など）
        print("\n中断しました。")
        sys.exit(1)


# このファイルを直接実行したときだけ main() を動かす
if __name__ == "__main__":
    main()

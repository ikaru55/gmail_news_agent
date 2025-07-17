import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import sys
import traceback

# credentials.json 파일은 항상 필요합니다.
# token.json은 최초 인증 후 생성되며, 이후에는 갱신만 하면 됩니다
# token.json을 반드시 발급받아야 합니다.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailHelper:
    def __init__(self):
        self.service = None
        creds = None

        try:
            print("GmailHelper 초기화를 시작합니다...")

            token_path = "gmail_helper/token.json"
            creds_path = "gmail_helper/credentials.json"

            # 1. credentials.json 파일이 필요합니다.
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"!!! 심각한 오류: {creds_path} 파일을 찾을 수 없습니다."
                )
            print(f">>> {creds_path} 파일 확인 완료.")

            # 2. 기존 token.json이 있으면 자격 증명을 로드합니다.
            if os.path.exists(token_path):
                print(f">>> {token_path} 파일이 존재하여 자격 증명을 로드합니다.")
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            # 3. 자격 증명이 없거나 유효하지 않으면 새로 만들거나 갱신합니다.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("자격 증명이 만료되어 새로고침을 시도합니다.")
                    creds.refresh(Request())
                    print(">>> 자격 증명 새로고침 성공.")
                else:
                    # 이 부분은 주로 로컬에서 최초 인증 시 실행됩니다.
                    print(
                        f">>> {token_path} 파일이 없거나 유효하지 않아, 새 인증 절차를 시작합니다."
                    )
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    print(">>> 새 자격 증명 생성 완료.")

                # 새로 만들거나 갱신된 자격 증명을 token.json 파일에 저장합니다.
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
                print(f">>> 갱신된 자격 증명을 {token_path}에 저장했습니다.")

            print("Gmail API 서비스 빌드를 시작합니다...")
            self.service = build("gmail", "v1", credentials=creds)
            print(">>> Gmail API 서비스 빌드 성공. GmailHelper 초기화 완료.")

        except Exception as e:
            print(f"!!! GmailHelper 초기화 중 심각한 오류 발생: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

    def get_unread_messages(self, user_id="me", sender_email=None):
        if not self.service:
            print("Gmail 서비스가 초기화되지 않았습니다.")
            return []
        try:
            query = "is:unread"
            if sender_email:
                query += f" from:{sender_email}"

            response = (
                self.service.users().messages().list(userId=user_id, q=query).execute()
            )
            messages = response.get("messages", [])
            print(f"'{query}' 조건으로 {len(messages)}개의 메일을 찾았습니다.")
            return messages
        except HttpError as error:
            print(f"읽지 않은 메일을 가져오는 중 오류 발생: {error}")
            return []

    def get_message_detail(self, message_id, user_id="me"):
        if not self.service:
            print("Gmail 서비스가 초기화되지 않았습니다.")
            return None
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId=user_id, id=message_id, format="full")
                .execute()
            )
            return message
        except HttpError as error:
            print(f"메일 상세 내용을 가져오는 중 오류 발생: {error}")
            return None

    def _parse_message_body(self, message_payload):
        if "parts" in message_payload:
            for part in message_payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        body_data = part["body"]["data"]
                        return base64.urlsafe_b64decode(body_data).decode("utf-8")
                elif "parts" in part:
                    result = self._parse_message_body(part)
                    if result:
                        return result
        elif "body" in message_payload and "data" in message_payload["body"]:
            body_data = message_payload["body"]["data"]
            return base64.urlsafe_b64decode(body_data).decode("utf-8")
        return "메일 본문을 찾을 수 없습니다."

    def send_email_with_attachment(
        self, to, subject, message_text, audio_data, user_id="me"
    ):
        if not self.service:
            print("Gmail 서비스가 초기화되지 않았습니다.")
            return None
        try:
            mime_message = MIMEMultipart()
            mime_message["to"] = to
            mime_message["subject"] = subject

            text_part = MIMEText(message_text, "plain", "utf-8")
            mime_message.attach(text_part)

            # Gemini가 mp3를 지원한다면 wav 대신 mp3로 처리하는 것이 효율적일 수 있습니다.
            # 여기서는 제공된 코드에 따라 wav로 처리합니다.
            audio_part = MIMEAudio(
                audio_data, "mpeg"
            )  # audio_data가 mp3 형식이라고 가정
            audio_part.add_header(
                "Content-Disposition", "attachment", filename="summary_voice.mp3"
            )
            mime_message.attach(audio_part)

            encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            send_message = (
                self.service.users()
                .messages()
                .send(userId=user_id, body=create_message)
                .execute()
            )
            print(
                f"첨부파일 포함 메일이 성공적으로 발송되었습니다. ID: {send_message['id']}"
            )
            return send_message
        except HttpError as error:
            print(f"메일 발송 중 오류 발생: {error}")
            return None

    def send_email(self, to, subject, message_text, user_id="me"):
        if not self.service:
            print("Gmail 서비스가 초기화되지 않았습니다.")
            return None
        try:
            message = MIMEText(message_text, "plain", "utf-8")
            message["to"] = to
            message["subject"] = subject

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            send_message = (
                self.service.users()
                .messages()
                .send(userId=user_id, body=create_message)
                .execute()
            )
            print(f"메일이 성공적으로 발송되었습니다. ID: {send_message['id']}")
            return send_message
        except HttpError as error:
            print(f"메일 발송 중 오류 발생: {error}")
            return None

    def mark_as_read(self, message_id, user_id="me"):
        if not self.service:
            print("Gmail 서비스가 초기화되지 않았습니다.")
            return None
        try:
            self.service.users().messages().modify(
                userId=user_id, id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()
        except HttpError as error:
            print(f"메시지를 읽음 처리하는 중 오류 발생: {error}")

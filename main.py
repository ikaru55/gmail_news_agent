from gmail_helper.email_helper import GmailHelper
from gemini.gemini_helper import generate_gemini_answer, generate_gemini_voice
import os
from flask import Flask
import sys
import traceback

app = Flask(__name__)

# --- [설정] ---
TARGET_SENDER = [
    "access@interactive.wsj.com",
    "linas@substack.com",
    "FT@newsletters.ft.com",
    "FT@news-alerts.ft.com",
]
RECIPIENT_EMAIL = "your_email@example.com"

try:
    print("애플리케이션 초기화를 시작합니다...")
    gmail_helper = GmailHelper()
    print(">>> 애플리케이션 초기화 성공.")
except Exception as e:
    print(f"!!! 애플리케이션 초기화 중 심각한 오류 발생: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)


def run_email_summary_job():
    try:
        if not gmail_helper or not gmail_helper.service:
            raise RuntimeError("GmailHelper가 올바르게 초기화되지 않았습니다.")

        # 1. 특정 발신자가 보낸 읽지 않은 메일 목록 가져오기
        unread_msgs = []
        for target in TARGET_SENDER:
            unread_msgs.extend(gmail_helper.get_unread_messages(sender_email=target))

        if not unread_msgs:
            print(f"{TARGET_SENDER}로부터 온 읽지 않은 메일이 없습니다.")
            return "읽지 않은 메일 없음"

        all_email_bodies = []
        print(f"\n--- {len(unread_msgs)}개의 메일 요약을 시작합니다 ---")

        for msg in unread_msgs:
            message_detail = gmail_helper.get_message_detail(msg["id"])
            if message_detail:
                subject = next(
                    (
                        h["value"]
                        for h in message_detail["payload"]["headers"]
                        if h["name"].lower() == "subject"
                    ),
                    "제목 없음",
                )
                body = gmail_helper._parse_message_body(message_detail["payload"])
                full_content = f"제목: {subject}\n본문:\n{body}\n\n"
                all_email_bodies.append(full_content)

        if not all_email_bodies:
            return "메일 본문을 처리할 수 없었습니다."

        # 2. Gemini API를 사용하여 번역 및 요약
        system_prompt = (
            "당신은 매니저의 투자 관련 뉴스를 정리해서 알려주는 비서 Damos야"
            "주어진 여러 개의 이메일 본문을 하나도 빠짐없이 모두 읽고 투자관련 소식들 위주로 핵심만 요약해줘 "
            "전체 내용을 종합하여 핵심만 간결하게 하나의 리포트로 요약해주세요. 그리고 이후에는 이 투자 정보들이 정확히 어떤 투자 아이디어로 연결될 수 있을지 고민해서 알려줘"
            "모든 이메일 내용은 한글로 정리되어야 합니다."
            "이메일 내용은 나에게 업무 보고 하듯이 작성해줘 항상 첫문장은 잘 잤는지 아침인사. 나에게 보고하는 대본만 작성하고 이외의 내용은 포함하지마."
        )
        user_prompt = "이메일 내용:\n\n---\n" + "\n---\n".join(all_email_bodies)

        print("\nGemini API로 요약을 요청합니다...")
        summary = generate_gemini_answer(user_prompt, system_instruction=system_prompt)

        if not summary:
            print(
                f"Gemini API로부터 요약 내용을 받아오지 못했습니다 {summary}",
                file=sys.stderr,
            )
            return "Gemini API로부터 요약 내용을 받아오지 못했습니다."

        print("요약이 완료되었습니다.")
        voice_data = None  # 음성 파일 생성은 일단 주석 처리합니다.
        # if voice_data:
        #     summary_subject = "음성 요약 리포트"
        #     gmail_helper.send_email_with_attachment(
        #         RECIPIENT_EMAIL, summary_subject, summary, voice_data
        #     )
        # else:
        summary_subject = "지난밤 투자 요약 리포트"
        gmail_helper.send_email(RECIPIENT_EMAIL, summary_subject, summary)

        print("\n처리한 메일을 '읽음' 상태로 변경합니다.")
        for msg in unread_msgs:
            gmail_helper.mark_as_read(msg["id"])

        print("모든 작업이 완료되었습니다.")
        return "작업 성공"

    except Exception as e:
        print(f"!!! run_email_summary_job 실행 중 오류 발생: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return f"오류 발생: {e}"


@app.route("/")
def handle_request():
    print("요청을 받아 이메일 요약 작업을 시작합니다.")
    status_message = run_email_summary_job()
    print(f"작업 상태: {status_message}")
    return status_message, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

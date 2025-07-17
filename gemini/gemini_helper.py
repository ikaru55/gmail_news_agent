from google import genai
from google.genai import types
import json
import sys
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. Cloud Run의 Secret 설정을 확인하세요."
    )

client = genai.Client(api_key=GEMINI_API_KEY)

try:
    with open("gemini/prompt.json", "r", encoding="utf-8") as file:
        prompt_data = json.load(file)
except FileNotFoundError:
    print(
        "gemini/prompt.json 파일을 찾을 수 없습니다. 파일이 app/gemini/ 폴더 안에 있는지 확인하세요."
    )
    raise


def generate_gemini_answer(message, system_instruction=None, model="gemini-2.5-flash"):
    """
    Gemini API를 사용하여 채팅 응답을 생성합니다.

    :param message: 대화 텍스트
    :param model: 사용할 모델 이름
    :return: 모델의 응답 내용
    """
    try:
        response = client.models.generate_content(
            model=model,
            config=types.GenerateContentConfig(system_instruction=system_instruction),
            contents=message,
        )
        return response.text
    except Exception as e:
        print(f"API 호출 또는 예상치 못한 오류 발생: {e}", file=sys.stderr)
        return None


def generate_gemini_voice(script):
    print("음성 생성 시작...")
    voice_instruct = prompt_data["voice"]["ver_1"]

    script = voice_instruct + script
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=script,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Leda",
                    )
                )
            ),
        ),
    )

    data = response.candidates[0].content.parts[0].inline_data.data
    if not data:
        print("음성 데이터가 없습니다.", file=sys.stderr)
        return None
    return data

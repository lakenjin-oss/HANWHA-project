# Gemini 주민 대화 실행하기 (Windows PowerShell)

주민 앞에서 E키를 누르면 질문창이 열립니다. 루미(레이다·위성), 모아(전투체계), 토비(엔진·지상방산), 별이(발사체), 파도(선박·해양설비)는 자기 집 자료를 근거로 답합니다. 최근 5회 질문/답변을 후속 질문의 문맥으로 전달하며, 창을 닫으면 대화는 지워집니다. 질문과 최근 대화, 관련 자료는 Gemini로 전송됩니다.

## 1. 준비
Node.js와 Python 3.10 이상이 필요합니다. 이 변경이 들어 있는 프로젝트 폴더에서 터미널을 엽니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

## 2. 서버 터미널에 키 설정 및 실행

```powershell
$env:GEMINI_API_KEY = "본인이_발급받은_키"
$env:GEMINI_MODEL = "gemini-2.5-flash"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

모델은 계정에서 사용 가능한 generateContent 및 구조화 JSON 출력을 지원하는 모델 ID로 바꿀 수 있습니다. 키가 둘 다 있으면 Gemini가 우선입니다. Gemini에서는 OpenAI 임베딩을 호출하지 않습니다. 키를 VITE_ 변수나 소스 코드에 넣거나 GitHub에 올리지 마세요. backend/.env.example은 설명용이며 자동으로 읽지 않습니다. 환경변수는 현재 터미널에서만 유지됩니다.

## 3. 게임 연결
프로젝트 최상위 `.env` 파일을 생성하고 아래 한 줄을 저장합니다. 기존 설정이 있으면 보존하세요.

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

새 터미널에서 실행합니다.

```powershell
npm install
npm run dev
```

http://127.0.0.1:5173 에 접속합니다. 서버 두 개를 모두 켜두세요. `.env`를 바꾸면 게임 서버를 재시작하세요.

## 4. 확인
탐지의 집에서 루미 앞에 서서 E키 → 위성 주제 선택 → 질문 보내기 → “더 쉽게 설명해줘”를 보냅니다. 답변의 ‘AI 답변’과 출처를 확인하세요. 다른 주민에게도 담당 주제를 질문하세요. 키가 없으면 ‘도감 모드’로 동작합니다. /api/health의 llm 표시는 키 설정 여부일 뿐, 실제 연결 성공은 질문 응답으로 확인해야 합니다.

연결 오류 시 키, 모델 접근 권한, Google AI Studio의 사용 한도 및 서버 터미널을 확인하세요. 실패 시 입력을 유지하며 질문을 다시 보낼 수 있습니다. 서버의 하루 호출 한도 기본값은 100회이며 프로세스 재시작 시 초기화됩니다. 공개 배포에는 별도 Python 서버 호스팅과 인증/사용량 관리가 필요합니다.

## 검증 범위
키 없이 자동 테스트와 빌드를 검증합니다. 실제 Gemini 응답 품질·계정 권한·요금제 및 브라우저에서의 3D 조작은 별도 확인이 필요합니다.

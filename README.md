# mm-brief: Mattermost 아침 브리핑

Mattermost 공지 채널에서 일정을 뽑아 **일정표**(근거 링크가 붙은 지식베이스)를 쌓고, 매일 아침 **나와의 DM**으로 브리핑을 보내는 Claude Code 플러그인입니다.
어느 Mattermost 서버에서나 쓸 수 있습니다. 서버 주소, 읽을 채널, 내 소속은 설치할 때 정합니다.

```
#### 아침 브리핑 · 11월 10일 (화) · 서울 15반

**오늘**
- 12:00 **점심 라이브** (11/2~11/30 평일) · 줌 링크는 공지 참고 [공지사항 11/02](…)

**앞으로 7일**
- 11/12 (목) 15:00 **역량테스트 신청** (11/3~11/12) · 신청서 제출 [행사 11/03](…)
```

## 필요한 것
- Claude Code (유료 플랜으로 로그인된 상태). 공지를 일정으로 정리하는 데 내 Claude를 씁니다.
- Python 3.8 이상과 Pillow (첨부 이미지를 줄이는 데 씀. 없으면 setup이 `python -m pip install pillow` 를 안내합니다)
- Mattermost 계정 (봇이나 관리자 권한은 필요 없습니다)
- Windows 또는 mac

## 설치 (Claude Code 안에서)
```
/plugin marketplace add ssafy-jinhyeok/mm-brief
/plugin install mm-brief@mm-brief
/mm-brief:setup
```
setup이 순서대로 안내합니다.
1. 서버 주소와 내 소속을 입력합니다.
2. 새 터미널에서 로그인합니다.
3. Claude가 내 채널 목록을 보고 공지 채널을 추천하면, 그중에서 고릅니다.
4. 미리보기를 봅니다.
5. 매일 받을 시각을 정합니다.

그다음부터는 `/mm-brief:brief` 로 미리보기, 지금 보내기, 채널·소속·시간 바꾸기, 끄기를 할 수 있어요.

## 하는 일
- **쌓기:** 고른 채널의 최근 30일 글과 **첨부 이미지**(포스터, 시간표)를 시간 순서로 조금씩 Claude에 보냅니다. Claude는 일정표에 더하거나 고칠 일정만 돌려줍니다.
  - 일정표는 `~/.mm-brief/events.json` 에 저장되고, 표로 보는 `~/.mm-brief/일정표.md` 도 함께 만들어집니다.
  - 다음 날부터는 **새 글과 고쳐진 글만** 읽습니다. 한 번 들어간 일정은 끝날 때까지 남아 있으니, 날마다 같은 글을 다시 읽다가 일정이 빠지는 일이 없습니다. 이미 끝난 일정은 일정표에서 버립니다.
  - 공지가 일정을 바꾸거나 취소하면, 일정표의 그 일정을 고치거나 지웁니다.
- **꺼내 쓰기:** 일정표에서 오늘 · 앞으로 7일 · 날짜 미정 일정을 골라 나와의 DM에 올립니다.
  - 매일 열리는 라이브나 신청 기간처럼 **여러 날에 걸친 일정은 하나로 적습니다.** 반복 일정은 열리는 날마다 '오늘'에 나오고, 신청 기간은 시작일과 마감일에 나옵니다.
- **소속:** setup에서 입력한 소속(예: 서울 15반)을 기준으로 고릅니다. 소속마다 날짜가 다른 일정은 내 날짜로 적고, 다른 소속만 대상인 일정은 뺍니다.
- **이미지:** Mattermost 축소본을 긴 변 1280px JPEG로 줄여 10장씩 읽습니다. 읽은 결과는 `~/.mm-brief/images.json` 에 저장해 다시 읽지 않습니다. PDF 첨부는 읽지 않습니다.
- **근거:** 모든 일정에 근거 공지 링크가 붙습니다. 근거 글이 없는 일정은 코드가 버립니다.
- **놓친 예약:** 예약 시각에 PC가 꺼져 있거나 잠자기 중이었으면, 켜진 뒤에 한 번 보냅니다 (하루 한 번).

## 안전
- **비밀번호:** 저장하지 않습니다. 로그인할 때 받은 세션 토큰만 `~/.mm-brief/token` 에 저장합니다.
  - 토큰은 설정한 서버 주소 외에는 보내지 않고, 리다이렉트도 따라가지 않습니다.
  - 서버 주소를 바꾸면 토큰을 지웁니다.
- **보내는 데이터:** 공지 글은 **내 Claude 계정**으로 Anthropic에 보내져 일정으로 정리됩니다. 작성자 이름은 보내지 않습니다.
- **명령 실행:** Claude는 도구를 모두 끈 상태(`--tools ""`)에서 글을 일정 JSON으로 바꾸기만 합니다. 공지 글에 이상한 지시가 있어도 내 PC에서 아무것도 실행되지 않습니다.
- **멘션:** 브리핑의 `@`는 `＠`로 바꿔서 다른 사람에게 알림이 가지 않습니다.
- **공식 도구 아님:** 이 플러그인은 Mattermost나 어떤 기관의 공식 도구가 아닙니다. 자동으로 글을 읽어도 되는지 조직의 규칙을 먼저 확인하세요.

아래 명령의 `~`는 내 홈 폴더입니다. Windows PowerShell에서는 `$HOME`, 명령 프롬프트에서는 `%USERPROFILE%`로 바꿔 쓰세요.

## 내 조직용으로 고쳐 쓰기 (템플릿)
이 저장소를 fork하거나 템플릿으로 복사한 뒤 아래만 바꾸면 됩니다. 코드는 `scripts/mmbrief.py` 한 파일입니다.
- 일정 뽑는 규칙: `PROMPT`(어떤 글을 일정으로 볼지)와 `WHO`(소속으로 고르는 규칙)
- 숫자: `DAYS`(읽을 기간), `AHEAD`(브리핑에 보여 줄 날 수), `MODEL`(쓸 Claude 모델)
- 이름: `.claude-plugin/marketplace.json` 의 `name`과 README의 설치 명령을 내 저장소 이름으로
- 바꾼 뒤 `python scripts/test_mmbrief.py` 로 확인합니다 (네트워크와 Claude 없이 돕니다).

## 끄기와 삭제
```
python ~/.mm-brief/mmbrief.py schedule --remove     # 매일 아침 예약 끄기 (mac은 python3)
```
그다음 `~/.mm-brief` 폴더를 지우고, Claude Code에서 `/plugin uninstall mm-brief@mm-brief` 를 실행하면 모두 지워집니다.

## 직접 실행 (Claude Code 없이 명령만)
```
python ~/.mm-brief/mmbrief.py install --server https://chat.example.com --who "서울 15반"
python ~/.mm-brief/mmbrief.py login                       # 로그인
python ~/.mm-brief/mmbrief.py channels                    # 채널 목록
python ~/.mm-brief/mmbrief.py install --channels team/notice team/events
python ~/.mm-brief/mmbrief.py brief --dry-run             # 미리보기 (--rebuild: 일정표 다시 만들기)
python ~/.mm-brief/mmbrief.py brief                       # 나와의 DM에 보내기
python ~/.mm-brief/mmbrief.py schedule --time 07:30
```
처음 `install`은 플러그인 폴더의 `scripts/mmbrief.py`로 실행하세요. 그때 `~/.mm-brief`에 복사됩니다.

## 라이선스
MIT

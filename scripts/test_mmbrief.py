"""python test_mmbrief.py : 네트워크와 Claude 없이 일정표 고치기와 브리핑 글만 확인한다."""
import datetime as dt
import io
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mmbrief as m  # noqa: E402

tmp = Path(tempfile.mkdtemp())
m.KB, m.IMAGES = tmp / "events.json", tmp / "images.json"


def ms(month, day):
    return int(dt.datetime(2026, month, day, 9, tzinfo=m.KST).timestamp() * 1000)


def post(pid, day, ch="t/notice", text="...", edit=0):
    return {"id": pid, "ch": ch, "channel": "공지", "at": ms(11, day), "edit": edit, "text": text, "images": [],
            "link": f"https://chat.example.com/t/pl/{pid}"}


def ev(**kw):
    base = {"id": "", "cancelled": False, "date": "", "end": "", "repeat": "", "time": "", "title": "", "note": "",
            "certainty": "확정", "source": "p1"}
    return {**base, **kw}


# 일정표 고치기: 근거 없음·날짜 이상·중복은 버리고, id로 고치거나 취소한다
kb = {"seen": {}, "events": [], "next": 1}
p1, p2 = post("p1", 3), post("p2", 5)
m.apply(kb, [ev(date="2026-11-24", time="14:00", title="월말평가", note="노트북 지참"),
             ev(date="2026-11-26 10:00", title="특강 @all", certainty="추정"),
             ev(date="2026-11-25", title="근거 없는 일정", source="nope"),
             ev(date="11월 말", title="날짜가 이상한 일정"),
             ev(date="2026-11-24", time="14:00", title="월말평가", note="중복"),
             ev(date="2026-11-02", end="2026-11-30", repeat="평일", time="12:00", title="점심 라이브"),
             ev(date="2026-11-03", end="2026-11-12", time="15:00", title="역량테스트 신청"),
             ev(date="2026-11-20", end="2026-11-20", repeat="매일", title="하루짜리"),
             ev(date="2026-12-01", title="최종발표", certainty="미정")], [p1])
titles = {e["title"]: e for e in kb["events"]}
assert set(titles) == {"월말평가", "특강 ＠all", "점심 라이브", "역량테스트 신청", "하루짜리", "최종발표"}, titles
assert titles["하루짜리"]["end"] == "" and titles["하루짜리"]["repeat"] == ""  # 끝 날짜가 같으면 하루짜리
assert titles["월말평가"]["link"].endswith("/pl/p1")
exam = titles["월말평가"]["id"]
m.apply(kb, [ev(id=exam, date="2026-11-25", time="10:00", title="월말평가", note="하루 미뤄짐", source="p2"),
             ev(id=titles["최종발표"]["id"], cancelled=True, source="p2"),
             ev(id=titles["특강 ＠all"]["id"], cancelled=True, source="p1")], [p2])  # 이번에 보내지 않은 글이 근거면 무시
titles = {e["title"]: e for e in kb["events"]}
assert titles["월말평가"]["date"] == "2026-11-25" and titles["월말평가"]["id"] == exam and titles["월말평가"]["posted"] == "11/05"
assert "최종발표" not in titles and "특강 ＠all" in titles

# 반복·기간 일정: 평일 반복은 평일마다, 신청 기간은 첫날과 마감일에만 보인다
live, apply_ = titles["점심 라이브"], titles["역량테스트 신청"]
assert m.occurs(live, dt.date(2026, 11, 10)) and not m.occurs(live, dt.date(2026, 11, 8))  # 화요일 / 일요일
assert m.occurs(apply_, dt.date(2026, 11, 12)) and not m.occurs(apply_, dt.date(2026, 11, 10))
assert m.occurs({**live, "repeat": "매주"}, dt.date(2026, 11, 9)) and not m.occurs({**live, "repeat": "매주"}, dt.date(2026, 11, 10))

today = dt.date(2026, 11, 10)
text = m.render_brief(kb["events"], today, 2, "서울 15반")
assert text.splitlines()[0] == "#### 아침 브리핑 · 11월 10일 (화) · 서울 15반", text
today_part = text.split("**오늘**")[1].split("**앞으로")[0]
assert "- 12:00 **점심 라이브** (11/2~11/30 평일)" in today_part and "역량테스트" not in today_part, text
assert "- 11/12 (목) 15:00 **역량테스트 신청** (11/3~11/12)" in text, text  # 진행 중인 기간의 마감
assert "점심 라이브" not in text.split("**앞으로")[1]  # 이미 시작한 반복 일정은 앞으로 목록에 또 넣지 않는다
assert "@all" not in text
night = {**live, "date": "2026-10-26", "time": "19:30", "title": "저녁 보충수업"}  # 더 일찍 시작했지만 더 늦은 시각
order = m.render_brief([night, live], today, 1)
assert order.index("점심 라이브") < order.index("저녁 보충수업"), order  # 오늘 칸은 시각 순서
weekly = {**live,"date": "2026-11-07", "end": "2026-12-26", "repeat": "매주", "title": "토요 특강"}  # 11/7은 토요일
assert m.soon_day(weekly, today) == dt.date(2026, 11, 14)  # 이미 시작한 매주 일정은 다음 회차를 앞으로 목록에
assert m.soon_day(live, today) is None
assert "| 11/2~11/30 평일 | 12:00 | 점심 라이브 |" in m.render_table(kb["events"], today)
assert "공지된 일정이 없어요" in m.render_brief([], today, 0)
assert "서울 15반" in m.prompt(today, {"who": "서울 15반"}) and "모른다" in m.prompt(today, {})

# 새 글만, 시간 순서로 나눠 보내고, 다음 묶음은 앞에서 만든 일정표를 본다
calls = []


def fake_claude(blocks, schema):
    calls.append(blocks)
    first = blocks[2]["text"].split("[id=")[1].split(" ")[0]
    return {"events": [ev(date="2026-11-20", title=f"{first} 일정", source=first)]}


m.claude = fake_claude
m.CHUNK_CHARS = 1000
cfg = {"channels": ["t/notice"]}
posts = [post(f"q{i}", 1 + i, text="가" * 400) for i in range(4)]  # 묶음당 2개씩 → 2번
events, n = m.update_kb(posts, today, cfg)
assert n == 4 and len(calls) == 2 and len(events) == 2
assert "q0 일정" in calls[1][1]["text"]  # 두 번째 묶음에 첫 묶음의 일정이 보인다
assert m.update_kb(posts, today, cfg)[1] == 0 and len(calls) == 2  # 이미 읽은 글은 다시 보내지 않는다
posts[3]["edit"] = 1
assert m.update_kb(posts, today, cfg)[1] == 1 and len(calls) == 3  # 고쳐진 글은 다시 읽는다
kb_now = json.loads(m.KB.read_text(encoding="utf-8"))
kb_now["events"] += [{**kb_now["events"][0], "id": "old", "date": "2026-11-09", "title": "어제 끝남"},
                     {**kb_now["events"][0], "id": "tbd", "date": "2026-11-01", "certainty": "미정", "title": "11월 중"}]
m.KB.write_text(json.dumps(kb_now, ensure_ascii=False), encoding="utf-8")
left = [e["title"] for e in m.update_kb(posts, today, cfg)[0]]
assert "어제 끝남" not in left and "11월 중" in left  # 끝난 일정은 버리고, 이번 달 날짜 미정 일정은 남긴다
assert m.update_kb(posts, today, {"channels": ["t/other"]})[0] == []  # 뺀 채널의 일정은 지운다
assert len(m.update_kb(posts, today, cfg, rebuild=True)[0]) == 2 and len(calls) == 5

# 이미지: 이미 읽은 것은 다시 보내지 않고, 읽은 글자는 그 글 내용에 붙고, 10장씩 나눠 보낸다
from PIL import Image  # noqa: E402
buf = io.BytesIO()
Image.new("RGBA", (3000, 1000), (0, 0, 0, 0)).save(buf, "PNG")  # 크고 투명한 PNG
big = buf.getvalue()
small = Image.open(io.BytesIO(m.shrink(big)))
assert small.format == "JPEG" and small.size == (m.IMG_EDGE, round(m.IMG_EDGE / 3)) and small.getpixel((0, 0)) == (255, 255, 255)
assert Image.open(io.BytesIO(m.shrink(m.shrink(big)))).size == small.size  # 작은 건 키우지 않는다

calls = []
m.api = lambda method, path, tok=None, body=None, query=None, raw=False: (b"broken" if path.endswith("bad") else big, "image/png")
m.claude = lambda blocks, schema: calls.append(blocks) or {"images": [{"file": "f2", "text": "11/20 14시 대강의장"}]}
m.IMAGES.write_text(json.dumps({"f1": "이미 읽음"}), encoding="utf-8")
ps = [{"id": "p1", "text": "공지", "images": [{"id": "f1", "preview": True}, {"id": "f2", "preview": True}]}]
assert m.read_images(ps, "tok") == 1 and len(calls) == 1
assert "(첨부 이미지 내용) 이미 읽음" in ps[0]["text"] and "(첨부 이미지 내용) 11/20 14시 대강의장" in ps[0]["text"]
assert m.read_images([{"id": "p1", "text": "", "images": [{"id": "f2", "preview": True}]}], "tok") == 0 and len(calls) == 1
m.read_images([{"id": "q", "text": "", "images": [{"id": f"n{i}", "preview": False} for i in range(12)]}], "tok")
assert len(calls) == 3  # 12장 = 10장 + 2장
assert all(b["source"]["media_type"] == "image/jpeg" for b in calls[-1] if b["type"] == "image")
m.read_images([{"id": "r", "text": "", "images": [{"id": "bad", "preview": False}]}], "tok")
assert len(calls) == 3  # 깨진 이미지만 있으면 Claude를 부르지 않는다
print("ok")

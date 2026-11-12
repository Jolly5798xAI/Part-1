"""EP11: verified phrase text over the measured phrase bounds (speech chunks from timeline/transcript_raw.json, i.e. the VO's own
pauses). ASR slips fixed by ear against the approved plot (e.g. «к вири» -> «к двери», «Алик» -> «Алекс», «Паницейский» ->
«Полицейский», truncated last syllables at chunk edges). Writes timeline/transcript_words.json and docs/EP11_transcript.txt."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = json.load(open(os.path.join(ROOT, "timeline", "transcript_raw.json")))
# (index of first raw chunk, index of last raw chunk, verified text)
P = [(0, 1, "«Следующий игрок: Елена»."), (2, 3, "И сразу её крик."), (4, 4, "Я бросился к двери комнаты двести четыре,"),
     (5, 5, "но полицейский схватил меня."), (6, 6, "«Не входи."), (7, 7, "Там начинается нулевой уровень»."),
     (8, 8, "Я вырвался и открыл дверь."), (9, 9, "За ней стояла моя сестра,"), (10, 11, "прикованная к креслу."),
     (12, 12, "Перед ней горел экран."), (13, 13, "«Выберите, кого сохранить»."), (14, 15, "«Создателя или игрока»."),
     (16, 16, "Елена посмотрела на меня."), (17, 17, "«Алекс."), (18, 18, "Я не создавала эту игру»."),
     (19, 20, "«Но на экране было твоё имя»."), (21, 21, "«Я создала только копии,"), (22, 22, "чтобы спасти тебя»."),
     (23, 23, "Она указала на монитор."), (24, 24, "На записи я лежал в больничной палате"), (25, 25, "без сознания."),
     (26, 26, "«Ты попал в аварию три года назад."), (27, 27, "Я пыталась вернуть твою память."),
     (28, 30, "Но программа начала создавать новые версии тебя»."), (31, 31, "Я посмотрел на свою исчезающую руку."),
     (32, 33, "«Значит, настоящий Алекс всё ещё жив?»"), (34, 34, "Елена кивнула."), (35, 35, "Вдруг экран загорелся красным."),
     (36, 37, "«Нулевой уровень активирован»."), (38, 39, "«Удаление всех копий»."), (40, 40, "Полицейский за моей спиной начал рассыпаться."),
     (41, 41, "Из коридора донёсся крик."), (42, 43, "Алекс-сорок девять тоже исчезал."), (44, 44, "Я бросился к компьютеру,"),
     (45, 45, "но Елена закричала:"), (46, 46, "«Не трогай его!»"), (47, 47, "«Почему?»"), (48, 50, "«Потому что это не компьютер»."),
     (51, 51, "Экран медленно повернулся."), (52, 52, "На нём появилось моё лицо,"), (53, 53, "только с закрытыми глазами."),
     (54, 54, "А потом глаза открылись."), (55, 56, "Я услышал собственный голос:"), (57, 58, "«Елена, отойди от него."),
     (59, 60, "Эта копия уже знает слишком много»."), (61, 61, "На экране появилось сообщение:"),
     (62, 63, "«Подключение к оригиналу установлено»."), (64, 64, "«Оригинал проснулся».")]
assert P[-1][1] == len(raw) - 1 and all(P[i][1] + 1 == P[i + 1][0] for i in range(len(P) - 1)), "phrases must cover every chunk once"
out, txt = [], []
for a, b, text in P:
    s, e = raw[a]["start"], raw[b]["end"]
    # word times: inside each raw chunk by letter count; the verified words are spread over the phrase by letters
    ws = text.split(); n = sum(len(w) for w in ws); c = s; words = []
    for w in ws:
        d = (e - s) * len(w) / n; words.append({"w": w, "s": round(c, 3), "e": round(c + d, 3)}); c += d
    out.append({"start": s, "end": e, "text": text, "words": words}); txt.append(f"{s:7.2f}  {text}")
json.dump(out, open(os.path.join(ROOT, "timeline", "transcript_words.json"), "w"), ensure_ascii=False, indent=1)
head = ["ЦЕНА ВЫБОРА — EP11 «НУЛЕВОЙ УРОВЕНЬ» — verified transcript of the approved voiceover",
        "File: audio/ElevenLabs_2026-11-12T12_15_57_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3 (108.12 s, md5 5974a54f41fada113993a12605b97d1a)",
        "ASR: Whisper small (sherpa-onnx int8 export), phrases cut at the VO's own pauses (silencedetect -36 dB, >= 0.09 s); text checked by ear",
        "against the approved EP11 plot; numbers written as spoken. Times: phrase start, seconds on the VO clock.",
        "Notes: the VO says «За ней стояла моя сестра, прикованная к креслу» (she is shown seated, chained to the chair, as the plot says);",
        "the speech runs to the very end of the file (last word ends at 108.12 s, no silent tail).", ""]
open(os.path.join(ROOT, "docs", "EP11_transcript.txt"), "w").write("\n".join(head + txt) + "\n")
print("\n".join(txt))

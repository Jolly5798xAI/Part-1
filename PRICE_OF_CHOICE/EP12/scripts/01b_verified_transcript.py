"""EP12: verified phrase text over the measured phrase bounds (speech chunks from timeline/transcript_raw.json, i.e. the VO's own
pauses). ASR slips fixed by ear against the approved plot (e.g. «троснул» -> «проснулся», «Душ» -> «Дождь», «спасет на собой» ->
«спасёт нас обоих», truncated last syllables at chunk edges). Writes timeline/transcript_words.json and docs/EP12_transcript.txt."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = json.load(open(os.path.join(ROOT, "timeline", "transcript_raw.json")))
# (index of first raw chunk, index of last raw chunk, verified text)
P = [(0, 0, '«Оригинал проснулся».'), (1, 1, 'На экране открыл глаза настоящий Алекс.'), (2, 2, 'Он посмотрел на меня.'), (3, 3, '«Сорок восемь.'), (4, 4, 'Ты должен исчезнуть».'), (5, 5, 'Я отступил.'), (6, 6, '«Почему?»'), (7, 7, '«Потому что'), (8, 8, 'ты вспомнил аварию».'), (9, 9, 'Елена закричала:'), (10, 10, '«Не слушай его!»'), (11, 11, 'Экран вспыхнул.'), (12, 12, 'Передо мной появилась дорога.'), (13, 13, 'Ночь.'), (14, 14, 'Дождь.'), (15, 15, 'За рулём сидел я,'), (16, 16, 'на пассажирском сиденье —'), (17, 17, 'Елена.'), (18, 18, 'Телефон завибрировал.'), (19, 19, '«Первое задание».'), (20, 20, '«Не тормози».'), (21, 21, '«Награда —'), (22, 22, 'пятьсот долларов».'), (23, 23, 'Впереди появился человек.'), (24, 24, 'Я нажал на тормоз.'), (25, 25, 'Но машина не остановилась.'), (26, 26, 'Запись оборвалась.'), (27, 27, 'Я посмотрел на Елену.'), (28, 28, '«Кто отправил сообщение?»'), (29, 29, 'Она молчала.'), (30, 30, 'Оригинальный Алекс усмехнулся.'), (31, 31, '«А теперь покажи ему остальное».'), (32, 32, 'На экране появилась новая запись.'), (33, 33, 'Елена сидела за компьютером.'), (34, 34, 'Она вводила команду:'), (35, 35, '«Повторить'), (36, 36, 'испытание».'), (37, 37, '«Ты запускала его снова?»'), (38, 38, 'Елена заплакала.'), (39, 39, '«Я пыталась найти версию, которая спасёт нас обоих».'), (40, 40, 'Оригинальный Алекс произнёс:'), (41, 41, '«Сорок семь копий выбрали деньги.'), (42, 42, 'А ты нажал на тормоз».'), (43, 43, 'Я посмотрел на исчезающую руку.'), (44, 44, '«Значит,'), (45, 45, 'я прошёл испытание?»'), (46, 46, '«Да».'), (47, 47, 'Впервые оригинал выглядел испуганным.'), (48, 48, '«И поэтому'), (49, 49, 'система выбрала тебя».'), (50, 50, 'Вдруг кресло Елены раскрылось.'), (51, 51, 'Крепления упали на пол.'), (52, 52, 'На мониторе появилось:'), (53, 53, '«Передача управления».'), (54, 54, '«Новый администратор:'), (55, 55, 'сорок восемь».'), (56, 56, 'Я поднял руку.'), (57, 57, 'Она перестала исчезать.'), (58, 58, 'Но затем загорелся второй экран.'), (59, 59, 'На нём был прямой эфир.'), (60, 60, 'Моя квартира.'), (61, 61, 'За столом сидела Елена.'), (62, 62, 'Я обернулся.'), (63, 63, 'Елена всё ещё стояла рядом со мной.'), (64, 64, 'На экране появилась надпись:'), (65, 65, '«Обнаружены две Елены».'), (66, 66, 'А затем'), (67, 67, 'обе одновременно сказали:'), (68, 68, '«Не верь мне».')]
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
head = ["ЦЕНА ВЫБОРА — EP12 «ПЕРВОЕ ИСПЫТАНИЕ» — verified transcript of the approved voiceover",
        "File: audio/ElevenLabs_2026-11-12T22_43_31_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3 (110.92 s, md5 097cedfe5c6498c64ff763cd0faf69a2)",
        "ASR: Whisper small (sherpa-onnx int8 export), phrases cut at the VO's own pauses (silencedetect -36 dB, >= 0.09 s); text checked by ear",
        "against the approved EP12 plot; numbers written as spoken. Times: phrase start, seconds on the VO clock.",
        "Notes: the VO opens on «Оригинал проснулся» (EP11's last screen line, read again as the hook); «Не верь мне» is read by the narrator",
        "(«обе одновременно сказали») - both Elenas mouth it on screen, no second voice; the speech runs to the end of the file (110.92 s).", ""]
open(os.path.join(ROOT, "docs", "EP12_transcript.txt"), "w").write("\n".join(head + txt) + "\n")
print("\n".join(txt))

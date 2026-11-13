"""EP13: verified phrase text over the measured phrase bounds (speech chunks from timeline/transcript_raw.json, i.e. the VO's own
pauses). ASR slips fixed by ear and by a second ASR pass with padded windows, against the approved EP13 plot:
«обе лены» -> «Обе Елены», «тонны сестру, тонны м» -> «то на сестру, то на монитор», «Ну записьте!» -> «На запястье»,
«а то, что рядом» -> «а та, что рядом,», «изопись ав» -> «запись аварии», «пануя админи» -> «панель администратора»,
«обнаружено последние копии» -> «Обнаружена последняя копия», «пожертвуют» -> «пожертвует», «создатели» -> «создателя»,
truncated last syllables at chunk edges. Writes timeline/transcript_words.json and docs/EP13_transcript.txt."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = json.load(open(os.path.join(ROOT, "timeline", "transcript_raw.json")))
T = ['Обе Елены', 'одновременно сказали:', '«Не верь мне».', 'Я смотрел то на сестру, то на монитор.', '«Которая из вас настоящая?»',
     'Елена рядом со мной подняла руку.', 'На запястье', 'светился номер один.', 'На экране', 'у второй Елены', 'появился ноль.',
     '«Я настоящая», —', 'сказала она, —', '«а та, что рядом,', 'создана системой».', 'Я отступил.', 'Но Елена с номером один схватила меня.',
     '«Она врёт.', 'Проверь запись аварии».', 'Я открыл панель администратора.', 'На экране появилась скрытая запись.', 'Ночная дорога.',
     'Телефон с заданием.', 'И ещё один человек', 'на заднем сиденье.', 'Это был…', 'настоящий', 'Алекс.', 'Он держал второй телефон.',
     'На нём светилась команда:', '«Отключить', 'тормоза».', 'Я замер.', '«Ты сам устроил аварию?»', 'Оригинал на мониторе улыбнулся.',
     '«Мне нужен был идеальный выбор».', 'Елена с номером один прошептала:', '«Он проверял, кто', 'пожертвует собой».',
     'Вдруг система выдала предупреждение:', '«Обнаружена последняя копия.', 'Номер сорок восемь».', 'Я посмотрел на сестру.', '«А ты кто?»',
     'Она опустила глаза.', '«Та, которая пыталась тебя остановить».', 'На экране появился новый выбор:', '«Удалить все копии».',
     '«Сохранить последнюю».', 'Под вторым вариантом загорелась надпись:', '«Цена —', 'жизнь Елены».', 'Я дёрнул руку.', '«Нет.',
     'Я не буду выбирать».', 'Тогда система заговорила голосом оригинала:', '«Выбор уже сделан».', 'На мониторе начался отсчёт.',
     '«Десять».', '«Девять».', '«Восемь».', 'Елена с номером один посмотрела на меня.', '«Алекс.', 'Есть третий вариант».', '«Какой?»',
     'Она указала на моё запястье.', 'Номер сорок восемь исчез.', 'Вместо него появилось слово:', '«Создатель».', 'И система произнесла:',
     '«Для остановки игры', 'удалите её создателя».', 'Все экраны', 'одновременно показали моё лицо.']
assert len(T) == len(raw), (len(T), len(raw))
out, txt = [], []
for c, text in zip(raw, T):
    s, e = c["start"], c["end"]
    ws = text.split(); n = sum(len(w) for w in ws); cc = s; words = []
    for w in ws:
        d = (e - s) * len(w) / n; words.append({"w": w, "s": round(cc, 3), "e": round(cc + d, 3)}); cc += d
    out.append({"start": s, "end": e, "text": text, "words": words}); txt.append(f"{s:7.2f} {e:7.2f}  {text}")
json.dump(out, open(os.path.join(ROOT, "timeline", "transcript_words.json"), "w"), ensure_ascii=False, indent=1)
head = ["ЦЕНА ВЫБОРА — EP13 «ПОСЛЕДНЯЯ КОПИЯ» — verified transcript of the approved voiceover",
        "File: audio/ElevenLabs_2026-11-13T01_03_09_Artem_Lebedev_-_Captivating_and_Engaging_eleven_v3.mp3 (116.61 s, md5 1b88f317c35291d93b1e933f0c30e1de)",
        "ASR: Whisper small (sherpa-onnx int8 export), phrases cut at the VO's own pauses (silencedetect -36 dB, >= 0.09 s), unclear chunks",
        "re-decoded with padded windows; text checked against the approved EP13 plot; numbers written as spoken. Times: phrase start / end (s).",
        "Notes: every line is read by the narrator (ALEX_48), including both Elenas, the original and the system — no second voice.", ""]
open(os.path.join(ROOT, "docs", "EP13_transcript.txt"), "w").write("\n".join(head + txt) + "\n")
print("\n".join(txt))

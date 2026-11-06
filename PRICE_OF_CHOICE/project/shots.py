"""EP01 «СТАКАН ВОДЫ» — single source of truth for the edit.

Every time here is in SOURCE voiceover seconds (the untouched MP3, see timeline/EP01_words.json).
02_timeline.py maps them to OUTPUT seconds (after the atmospheric pauses below) and writes
timeline/EP01_timeline.json, which the sound designer (03_sound.py), the UI renderer (04_ui.py)
and the editor (05_build.py) all read.
"""

FPS = 24
W, H = 1080, 1920

# Atmospheric pauses inserted into silences of the voiceover (allowed by the brief).
# (source_time_inside_a_silence, pause_seconds). Speech itself is never cut, stretched or pitched.
PAUSES = [
    (24.94, 0.70),  # after «Не открывай дверь три минуты» -> room for the first knocks
    (51.93, 0.35),  # after «Он замолчал» -> real silence behind the door
    (54.98, 0.45),  # after «...повернул голову» -> music drops out before the face reveal
]
CUT_TO_BLACK = 75.55   # source time of the hard cut (mid lock-turn, after the last word ends at 74.78)
END_CARD = 1.40        # seconds of silent black + series title after the cut

# ---------------------------------------------------------------- references (see characters/, locations/)
REF = {
    "ALEX": "characters/ALEX_character_bible.md#reference-sheet",
    "DOUBLE": "characters/DOUBLE_character_bible.md",
    "COP": "characters/POLICEMAN_character_bible.md",
    "HALL": "locations/APARTMENT_HALLWAY.md",
    "DOOR": "locations/ENTRANCE_DOOR.md",
    "CORRIDOR": "locations/STAIRWELL_CORRIDOR.md",
    "GLASS": "locations/PROPS.md#glass",
    "PHONE": "locations/PROPS.md#phone",
}

STYLE = ("photorealistic cinematic psychological thriller still, shot on ARRI Alexa 35 with Cooke S4 lenses, "
         "vertical 9:16 composition, night, very low practical light, cold blue-grey grade, neutral natural skin tones, "
         "deep shadows that are not crushed to pure black, subtle 35mm film grain, realistic textures, physically correct "
         "shadows and reflections, restrained and grounded, no stylisation")
NEGATIVE = ("cartoon, anime, illustration, 3d render, CGI look, plastic skin, waxy face, beauty filter, deformed hands, "
            "extra fingers, fused fingers, distorted face, asymmetric eyes, warped door, melting objects, floating objects, "
            "text, letters, captions, watermark, logo, brand names, readable insignia, oversaturated, neon, glitch, "
            "chromatic aberration overload, cheap horror filter, gore, exaggerated blood, jump-scare face, demon, monster, "
            "fog machine, lens flare overload, shaky cam, dutch angle")

# Fixed continuity facts, repeated into every relevant prompt.
CONT = {
    "HALL": "narrow entrance hall of an ordinary Moscow panel-building flat: grey ceramic floor tiles, beige textured wallpaper, "
            "low oak-veneer shoe cabinet on the LEFT wall with a round frameless mirror above it, kitchen doorway at the far end "
            "letting in faint cold-blue streetlight, ceiling light OFF",
    "DOOR": "dark-brown powder-coated steel entrance door, brushed-chrome lever handle on the LEFT side, round lock cylinder "
            "below the handle, small chrome thumb-turn latch above the handle, single peephole at eye level in the centre, "
            "hinges on the right, thin cold fluorescent light leaking through the gap under the door",
    "CORRIDOR": "stairwell landing of a Soviet panel building seen from inside the flat: walls painted pale green to shoulder "
                "height and whitewashed above, one flat fluorescent tube on the ceiling (steady, no flicker), beige-brown square "
                "floor tiles, a brown neighbour door straight across, a closed elevator door on the RIGHT, bare wall on the LEFT",
    "GLASS": "classic faceted Soviet glass tumbler (granyonyi stakan) filled to the brim with clear water",
    "PHONE": "black unbranded smartphone with thin bezels, dark-mode screen",
    "ALEX_HAND": "a young man's right hand, lean, short clean nails, thin black braided cord bracelet on the right wrist, "
                 "sleeve of a charcoal-grey cotton hoodie",
}

# ---------------------------------------------------------------- shot list
# kind: "live"  -> AI-generated photoreal shot (video preferred; still + camera move acceptable)
#       "ui"    -> phone interface insert rendered by 04_ui.py (final asset, exact Cyrillic)
# sfx : (source_time, effect, gain_db)  — effects are synthesised by 03_sound.py
SHOTS = [
    # ===================== SCENE 1 — HOOK
    dict(id="S01_A", scene=1, start=0.00, kind="live", anchor="Мне заплатили",
         visual_ru="Экстремально крупно: полный гранёный стакан воды на кафеле у входной двери. По поверхности воды проходит едва заметная дрожь.",
         prompt="extreme close-up, low angle at floor level: a {GLASS} standing on grey ceramic tiles right at the threshold of a closed {DOOR}; "
                "the thin cold light from under the door glints in the water and the glass facets; the water surface trembles very slightly",
         camera="slow push-in 4%, locked tripod", light="only the cold strip of light under the door, faint blue fill from behind",
         refs=["GLASS", "DOOR", "HALL"], transition="hard open (no fade)",
         sfx=[(0.00, "roomtone_start", 0), (0.05, "water_shiver", -8)]),
    dict(id="S01_B", scene=1, start=0.92, kind="ui", anchor="500 долларов", ui="bank_500",
         visual_ru="Вставка интерфейса: на тёмном экране всплывает уведомление банка «+500 $».",
         camera="UI pop-in, slight 2% zoom", transition="hard cut on «500»", on_screen="Зачисление +500,00 $",
         sfx=[(0.96, "money_chime", -6)]),
    dict(id="S01_C", scene=1, start=1.76, kind="live", anchor="за стакан воды",
         visual_ru="Низкий ракурс: стакан на переднем плане в фокусе, дверь позади размыта; полоска света под дверью.",
         prompt="low angle from the floor: the {GLASS} sharp in the foreground, the closed {DOOR} soft-focus behind it, "
                "cold light strip under the door, the rest of the {HALL} falling into darkness",
         camera="very slow lateral slide left 3%", light="cold under-door light, deep shadows",
         refs=["GLASS", "DOOR", "HALL"], transition="hard cut", sfx=[]),
    dict(id="S01_D", scene=1, start=2.95, kind="live", anchor="А через минуту… выломать мою дверь",
         visual_ru="Крупно: дверная ручка. На «выломать» ручку резко дёргают снаружи вниз, дверь вздрагивает в раме.",
         prompt="close-up of the brushed-chrome lever handle and thumb-turn of the {DOOR} from inside the dark hall; "
                "the handle is violently yanked down from outside and snaps back, the whole door shudders in its frame, "
                "a little dust falls from the frame",
         camera="locked, micro handheld only on the impacts", light="cold under-door light, faint blue fill",
         refs=["DOOR", "HALL"], transition="hard cut", on_screen=None,
         sfx=[(4.50, "handle_rattle", -4), (4.58, "door_blow", -3), (5.00, "door_blow", -6), (5.30, "handle_rattle", -10)]),

    # ===================== SCENE 2 — UNKNOWN MESSAGE
    dict(id="S02_A", scene=2, start=5.80, kind="live", anchor="Всё началось с сообщения без номера",
         visual_ru="От первого лица: телефон в руке Алекса в тёмной прихожей. В чёрном экране на миг отражается его лицо, затем экран загорается.",
         prompt="first-person POV: {ALEX_HAND} holding a {PHONE} at chest height in the dark {HALL}; for a moment the black screen reflects "
                "the face of ALEX (see reference) dimly, then the screen lights up and the reflection disappears in the glow; "
                "screen content left plain for compositing",
         camera="POV handheld, natural breathing micro-motion", light="phone screen glow on the hand, cold blue ambience",
         refs=["ALEX", "PHONE", "HALL"], transition="hard cut", screen="assets/ui/screens/screen_incoming.png",
         sfx=[(5.95, "phone_vibrate", -6), (6.10, "notify_ding", -8), (5.85, "cloth_rustle", -16)]),
    dict(id="S02_B", scene=2, start=7.90, kind="ui", anchor="«Поставь полный стакан у входа. Время — 60 секунд»", ui="task1",
         visual_ru="Экран сообщения: отправитель «Без номера». Текст задания появляется синхронно с голосом; запускается таймер 60 секунд.",
         camera="UI, slow 3% zoom", transition="hard cut", on_screen="Поставь полный стакан у входа. / Время: 60 секунд / 00:60",
         sfx=[(10.40, "timer_start", -8)]),
    dict(id="S02_C", scene=2, start=11.80, kind="live", anchor="Я решил, что это мошенники",
         visual_ru="Через плечо: Алекс в полутьме держит телефон, большой палец замер над кнопкой «Заблокировать». Лицо не в кадре.",
         prompt="over-the-shoulder shot from behind ALEX (only shoulder, ear and messy short dark-brown hair visible, face not shown) "
                "holding the {PHONE} in the dark {HALL}; his thumb hovers over the screen, hesitating; the {DOOR} is a dark shape beyond",
         camera="slow push-in 3%", light="phone glow rim light, cold ambience", refs=["ALEX", "PHONE", "HALL", "DOOR"],
         transition="hard cut", screen="assets/ui/screens/screen_task1.png", sfx=[(11.85, "breath", -18)]),
    dict(id="S02_D", scene=2, start=13.40, kind="ui", anchor="…были моё имя и адрес", ui="name_address",
         visual_ru="Экран: верх сообщения — «Алекс.» и полный адрес. Таймер продолжает отсчёт.",
         camera="UI scroll-up + slow zoom", transition="hard cut", on_screen="Алекс. / ул. Лесная, 14, кв. 37 / 00:54",
         sfx=[(14.67, "ui_tick_soft", -12)]),

    # ===================== SCENE 3 — GLASS AND THE MONEY
    dict(id="S03_A", scene=3, start=15.95, kind="live", anchor="Я поставил стакан",
         visual_ru="Крупно, низкий ракурс: рука Алекса ставит полный стакан на кафель у порога. Вода чуть переливается через край.",
         prompt="close-up at floor level: {ALEX_HAND} carefully sets the {GLASS} down on the grey tiles at the threshold of the {DOOR}; "
                "a single drop runs down the outside of the glass; the cold under-door light catches the water",
         camera="locked, slight tilt-down following the glass", light="cold under-door light, phone glow from above out of frame",
         refs=["ALEX", "GLASS", "DOOR"], transition="hard cut",
         sfx=[(16.20, "cloth_rustle", -14), (16.62, "glass_set", -4), (16.70, "water_shiver", -12)]),
    dict(id="S03_B", scene=3, start=17.35, kind="live", anchor="Телефон завибрировал",
         visual_ru="Крупно: телефон экраном вверх на тумбе для обуви вибрирует и медленно поворачивается; экран загорается.",
         prompt="close-up: the {PHONE} lying face-up on the oak-veneer shoe cabinet of the {HALL}, vibrating and slowly creeping "
                "across the wood; its screen lights up and throws cold light on the round mirror above; screen left plain for compositing",
         camera="locked, shallow depth of field", light="phone screen glow only", refs=["PHONE", "HALL"],
         transition="hard cut", screen="assets/ui/screens/screen_bank.png",
         sfx=[(17.45, "phone_vibrate_wood", -3)]),
    dict(id="S03_C", scene=3, start=18.65, kind="ui", anchor="На счёт пришли 500 долларов", ui="bank_500_full",
         visual_ru="Экран банка: «Зачисление +500,00 $», отправитель скрыт.",
         camera="UI, slow 2% zoom", transition="hard cut", on_screen="Зачисление / +500,00 $ / Отправитель: скрыт",
         sfx=[(19.55, "money_chime", -5)]),

    # ===================== SCENE 4 — SECOND TASK
    dict(id="S04_A", scene=4, start=20.50, kind="ui", anchor="Следующее задание стоило уже две тысячи", ui="task2_reward",
         visual_ru="Новое сообщение «Без номера»: «Задание 2 · Награда 2 000 $».",
         camera="UI, message slides in", transition="hard cut", on_screen="Задание 2 / Награда: 2 000 $",
         sfx=[(20.60, "notify_ding", -6)]),
    dict(id="S04_B", scene=4, start=23.05, kind="ui", anchor="«Не открывай дверь три минуты»", ui="task2",
         visual_ru="Текст задания: «Не открывай дверь 3 минуты.» Запускается таймер 03:00.",
         camera="UI, push-in on the timer", transition="hard cut on the first knock", on_screen="Не открывай дверь 3 минуты. / 03:00",
         sfx=[(24.20, "timer_start", -8)]),

    # ===================== SCENE 5 — THE POLICEMAN
    dict(id="S05_A", scene=5, start=24.94, kind="live", anchor="(пауза) стук — «В ту же секунду раздался стук»",
         visual_ru="Средний план прихожей от лица Алекса: дверь, стакан у порога. Три тяжёлых удара — дверь вздрагивает, вода в стакане дрожит. В полосе света под дверью тени ног.",
         prompt="first-person medium shot down the dark {HALL} toward the closed {DOOR}; the {GLASS} stands at its foot; the door "
                "shudders under heavy knocks, rings ripple across the water in the glass; two shadows of feet move in the light strip under the door",
         camera="POV, locked with tiny breathing motion", light="cold under-door strip, blue streetlight spill from the kitchen behind",
         refs=["HALL", "DOOR", "GLASS"], transition="hard cut on the first knock",
         sfx=[(24.96, "knock", -2), (25.22, "knock", -3), (25.46, "knock", -3), (26.50, "knock", -7), (26.72, "knock", -8)]),
    dict(id="S05_B", scene=5, start=26.90, kind="live", anchor="Мужчина за дверью представился полицейским…",
         visual_ru="Крупно: дверь изнутри — замок и глазок со светящейся точкой. Глухие удары кулаком продолжаются.",
         prompt="close-up of the inside of the {DOOR}: lock cylinder, thumb-turn and the peephole glowing as a tiny cold point of light; "
                "the door vibrates slightly with muffled fist knocks from outside",
         camera="slow tilt up from the lock to the peephole", light="peephole point light, under-door strip",
         refs=["DOOR"], transition="hard cut",
         sfx=[(28.10, "knock", -10), (28.36, "knock", -11), (30.90, "knock", -11), (31.14, "knock", -12)]),
    dict(id="S05_C", scene=5, start=29.25, kind="live", anchor="…утечка газа и нужно срочно выходить",
         visual_ru="От первого лица: Алекс медленно идёт к двери, левая рука скользит по обоям. Дверь приближается.",
         prompt="first-person POV slowly walking toward the {DOOR} through the {HALL}, his left hand (lean, no jewellery) sliding along the "
                "beige wallpaper; the peephole point of light grows closer",
         camera="slow POV dolly forward, natural steps", light="under-door strip and peephole point only",
         refs=["HALL", "DOOR"], transition="hard cut",
         sfx=[(29.40, "footstep_sock", -16), (30.05, "footstep_sock", -16), (30.70, "footstep_sock", -16), (29.5, "cloth_rustle", -18), (31.8, "breath", -16)]),
    dict(id="S05_D", scene=5, start=32.70, kind="live", anchor="Я посмотрел в глазок",
         visual_ru="Экстремально крупно: глазок. Камера приближается вплотную, кадр уходит в линзу — монтажный переход во взгляд через глазок.",
         prompt="extreme close-up of the chrome peephole of the {DOOR} at eye level, camera moving right up to the lens until the cold light "
                "inside the lens fills the frame",
         camera="push-in into the lens, ends on bright lens (match-cut to fisheye)", light="cold light through the peephole",
         refs=["DOOR"], transition="match cut into the lens", sfx=[(32.80, "cloth_rustle", -16), (33.50, "peephole_cover", -10)]),
    dict(id="S05_E", scene=5, start=34.10, kind="live", anchor="Полицейский действительно был в форме",
         visual_ru="Вид через глазок (рыбий глаз, круглая виньетка): полицейский в форме в коридоре, смотрит прямо в глазок.",
         prompt="view through a door peephole, strong fisheye distortion, circular dark vignette: the POLICEMAN (see reference) in a plain "
                "dark-blue police-style uniform and cap, no readable insignia, standing close to the door in the {CORRIDOR}, looking straight into "
                "the peephole with a calm, flat, unblinking expression, mouth slightly open as if he just finished speaking",
         camera="static fisheye, very slight lens breathing", light="single steady fluorescent tube overhead, cold green-white",
         refs=["COP", "CORRIDOR"], transition="hard cut", sfx=[(34.10, "corridor_hum", -14)]),

    # ===================== SCENE 6 — THE MAN AT THE WALL
    dict(id="S06_A", scene=6, start=36.15, kind="live", anchor="Но рядом с ним стоял ещё один человек, лицом к стене",
         visual_ru="Тот же вид через глазок, медленный дрейф: слева, у стены, неподвижно стоит человек лицом к стене. Заметен не сразу.",
         prompt="same peephole fisheye view of the {CORRIDOR}: the POLICEMAN on the right half of the frame, and at the LEFT edge, partly lost in the "
                "vignette, a second man in a charcoal-grey hoodie stands completely still with his face to the green-painted wall, back to camera, "
                "arms hanging, head slightly bowed; nobody else",
         camera="very slow drift left 4% so the second man is discovered late", light="same steady fluorescent tube",
         refs=["COP", "DOUBLE", "CORRIDOR"], transition="hard cut", sfx=[(36.20, "music_dip_small", 0)]),

    # ===================== SCENE 7 — THE WARNING
    dict(id="S07_A", scene=7, start=39.50, kind="live", anchor="Я потянулся к замку",
         visual_ru="Крупно: рука Алекса медленно тянется к вертушке замка, пальцы касаются металла.",
         prompt="close-up: {ALEX_HAND} slowly reaching toward the chrome thumb-turn latch of the {DOOR}; fingertips touch the cold metal",
         camera="locked, rack focus from latch to fingertips", light="cold under-door and peephole light, skin neutral",
         refs=["ALEX", "DOOR"], transition="hard cut", sfx=[(39.60, "cloth_rustle", -12), (40.90, "lock_touch", -8)]),
    dict(id="S07_B", scene=7, start=41.20, kind="live", anchor="Телефон загорелся",
         visual_ru="Рука на замке на переднем плане, позади на тумбе вспыхивает экран телефона; перевод фокуса на телефон.",
         prompt="the hand on the thumb-turn latch in the soft foreground, behind it on the shoe cabinet the {PHONE} screen flares up bright; "
                "focus racks from the hand to the glowing phone",
         camera="rack focus hand -> phone", light="sudden cold phone glow", refs=["ALEX", "DOOR", "PHONE", "HALL"],
         transition="hard cut", screen="assets/ui/screens/screen_warning.png", sfx=[(41.30, "phone_vibrate_wood", -12)]),
    dict(id="S07_C", scene=7, start=42.90, kind="ui", anchor="«Откроешь — погибнешь»", ui="warning",
         visual_ru="Экран: красное предупреждение «ОТКРОЕШЬ — ПОГИБНЕШЬ.» Короткое замедление, гул.",
         camera="UI, slow-motion feel: 4% creeping zoom", transition="hard cut", on_screen="ОТКРОЕШЬ — ПОГИБНЕШЬ. / 02:41",
         sfx=[(43.05, "low_boom", -10), (43.00, "tinnitus", -26)]),
    dict(id="S07_D", scene=7, start=44.85, kind="live", anchor="Я отдёрнул руку",
         visual_ru="Рука резко отдёргивается от замка и уходит из кадра.",
         prompt="close-up: {ALEX_HAND} jerks back sharply from the thumb-turn latch of the {DOOR} and leaves the frame, slight motion blur",
         camera="locked, natural motion blur", light="cold", refs=["ALEX", "DOOR"], transition="hard cut",
         sfx=[(45.10, "whoosh_short", -8), (45.15, "cloth_rustle", -10)]),
    dict(id="S07_E", scene=7, start=46.15, kind="live", anchor="Снаружи начали бить в дверь",
         visual_ru="Широко: дверь содрогается от тяжёлых ударов, стакан у порога дрожит, вода выплёскивается.",
         prompt="wide shot from inside the dark {HALL}: the {DOOR} shakes violently in its frame under heavy blows from outside, dust drifts from "
                "the frame, the {GLASS} at its foot shivers and a little water spills on the tiles",
         camera="locked, the image itself shakes only on impacts", light="under-door light flickers with the shadows outside",
         refs=["HALL", "DOOR", "GLASS"], transition="hard cut",
         sfx=[(46.30, "door_blow", -2), (46.95, "door_blow", -2), (47.55, "door_blow", -1), (48.05, "door_blow", -3), (47.6, "glass_rattle", -12)]),

    # ===================== SCENE 8 — THE NEIGHBOUR QUESTION
    dict(id="S08_A", scene=8, start=48.05, kind="live", anchor="Я спросил полицейского, как зовут моего соседа",
         visual_ru="Крупно, профиль снизу: ладонь Алекса прижата к двери, рядом с глазком; лицо остаётся в тени.",
         prompt="close-up from a low side angle: the palm of ALEX pressed flat against the inside of the {DOOR} next to the peephole, his face "
                "turned away in shadow, only the line of his jaw and stubble visible",
         camera="very slow push-in", light="peephole point light, under-door strip",
         refs=["ALEX", "DOOR"], transition="hard cut", sfx=[(48.50, "door_blow", -9), (49.40, "breath", -16)]),
    dict(id="S08_B", scene=8, start=50.95, kind="live", anchor="Он замолчал (пауза)",
         visual_ru="Глазок: полицейский замер и молча смотрит прямо в глазок. Полная тишина.",
         prompt="peephole fisheye view: the POLICEMAN stands motionless right in front of the door, staring into the peephole, silent, expressionless; "
                "the man at the wall still faces the wall at the left edge",
         camera="static", light="steady fluorescent", refs=["COP", "DOUBLE", "CORRIDOR"], transition="hard cut",
         sfx=[(50.95, "silence_cut", 0)]),

    # ===================== SCENE 9 — THE DOUBLE TURNS
    dict(id="S09_A", scene=9, start=51.93, kind="live", anchor="А человек у стены медленно повернул голову (пауза)",
         visual_ru="Глазок, медленный наезд на человека у стены: он медленно поворачивает голову через плечо; лицо пока в тени, виден лишь профиль.",
         prompt="peephole fisheye view slowly pushing toward the man at the green wall in the {CORRIDOR}: he very slowly turns his head over his "
                "shoulder toward the door; his face is still in shadow under the fluorescent light, only the profile, short dark-brown hair and "
                "stubble are visible; identical build and hoodie to ALEX",
         camera="slow push-in 6% toward the man", light="fluorescent top light, face half in shadow",
         refs=["DOUBLE", "ALEX", "CORRIDOR"], transition="hard cut",
         note="If the generator cannot keep the face identical during the head turn: end this shot BEFORE the face is visible and reveal it in S09_B as a separate still/clip made from the ALEX face reference.",
         sfx=[]),
    dict(id="S09_B", scene=9, start=54.98, kind="live", anchor="У него было моё лицо",
         visual_ru="Глазок, крупнее: двойник смотрит прямо в глазок. Это лицо Алекса — те же черты, шрам на левой брови.",
         prompt="peephole fisheye close view: the DOUBLE — exactly the face of ALEX (same face reference, same scar through the left eyebrow, same "
                "grey-green eyes, stubble and short dark-brown hair), now facing the door and staring straight into the peephole, completely calm, "
                "skin slightly pale and damp",
         camera="static, imperceptible push-in", light="fluorescent top light, eyes catching a highlight",
         refs=["DOUBLE", "ALEX", "CORRIDOR"], transition="hard cut after silence", sfx=[(55.28, "reveal_sting", -8)]),
    dict(id="S09_C", scene=9, start=56.55, kind="live", anchor="…моё лицо (реакция)",
         visual_ru="Крупно: настоящий Алекс у двери, в холодном свете из глазка. То же лицо — зритель видит совпадение.",
         prompt="close-up portrait of ALEX inside the dark {HALL}, face lit only by the thin cold light from the peephole, frozen in shock, "
                "breath held; exact same face as the reference sheet (scar through the left eyebrow)",
         camera="static", light="single cold point light on the face, deep soft shadows",
         refs=["ALEX", "HALL"], transition="hard cut", sfx=[(56.70, "breath_in_sharp", -12)]),

    # ===================== SCENE 10 — THE BLOODY PALM
    dict(id="S10_A", scene=10, start=57.60, kind="live", anchor="Я отступил от двери",
         visual_ru="От первого лица: Алекс пятится назад, дверь удаляется в темноту.",
         prompt="first-person POV stepping backwards away from the {DOOR} down the dark {HALL}; the peephole point of light recedes",
         camera="POV pull-back, two unsteady steps", light="peephole point and under-door strip",
         refs=["HALL", "DOOR"], transition="hard cut", sfx=[(57.75, "footstep_sock", -14), (58.30, "footstep_sock", -14)]),
    dict(id="S10_B", scene=10, start=59.00, kind="live", anchor="Двойник приложил к глазку…",
         visual_ru="Глазок: двойник подходит вплотную, лицо заполняет линзу.",
         prompt="peephole fisheye view: the DOUBLE (face of ALEX) walks up to the door until his face fills most of the lens, eyes on the peephole",
         camera="static fisheye", light="fluorescent", refs=["DOUBLE", "ALEX", "CORRIDOR"], transition="hard cut",
         sfx=[(59.10, "footstep_corridor", -14), (59.60, "footstep_corridor", -14)]),
    dict(id="S10_C", scene=10, start=60.60, kind="live", anchor="…окровавленную ладонь",
         visual_ru="Ладонь в крови ложится на глазок снаружи: изображение становится тёмно-красным, видны линии ладони.",
         prompt="peephole fisheye view: a man's right palm smeared with dark blood presses flat onto the outer lens of the peephole; the view turns "
                "dark red, palm lines and smeared blood visible, the fluorescent light glowing faintly through; realistic, not gory",
         camera="static", light="fluorescent light filtered through blood", refs=["DOUBLE", "CORRIDOR"], transition="hard cut on contact",
         sfx=[(60.66, "palm_slap_wet", -5), (61.10, "music_pulse_hit", -13)]),
    dict(id="S10_D", scene=10, start=62.70, kind="live", anchor="…а затем беззвучно произнёс",
         visual_ru="Ладонь медленно сползает, оставляя мазок; за ним — лицо двойника очень близко.",
         prompt="peephole fisheye: the bloody palm slowly slides down off the lens leaving a red smear across the view; behind the smear, very close, "
                "the face of the DOUBLE (face of ALEX) looking into the peephole",
         camera="static", light="fluorescent", refs=["DOUBLE", "ALEX", "CORRIDOR"], transition="hard cut", sfx=[(62.80, "smear", -12)]),
    dict(id="S10_E", scene=10, start=64.65, kind="live", anchor="«Не верь телефону»",
         visual_ru="Экстремально крупно сквозь мазок крови: губы двойника беззвучно произносят «Не верь телефону».",
         prompt="extreme close-up through the blood-smeared peephole lens: the lips and lower face of the DOUBLE (face of ALEX, stubble) silently and "
                "clearly mouthing the Russian words 'Ne ver telefonu' (four distinct mouth shapes: n-e, v-e-r, te-le, fo-nu); no sound",
         camera="static", light="fluorescent", refs=["DOUBLE", "ALEX", "CORRIDOR"], transition="hard cut",
         note="Lip-sync: mouth shapes must land on 64.75 «Не», 64.99 «верь», 65.35 «телефону». Second voice is NOT added.",
         sfx=[]),

    # ===================== SCENE 11 — THE LAST MESSAGE
    dict(id="S11_A", scene=11, start=66.30, kind="live", anchor="В этот момент пришло новое сообщение",
         visual_ru="Телефон на тумбе снова вспыхивает и вибрирует; свет отражается в круглом зеркале.",
         prompt="the {PHONE} on the shoe cabinet lights up again and vibrates; its cold glow reflects in the round mirror above; the {DOOR} is a dark "
                "mass at the frame edge; screen left plain for compositing",
         camera="slow push toward the phone", light="phone glow", refs=["PHONE", "HALL", "DOOR"], transition="hard cut",
         screen="assets/ui/screens/screen_open.png", sfx=[(66.45, "phone_vibrate_wood", -10), (66.50, "notify_ding", -8)]),
    dict(id="S11_B", scene=11, start=67.80, kind="ui", anchor="«Открой дверь. Осталось 10 секунд»", ui="open_door",
         visual_ru="Экран: «Открой дверь.» и таймер «Осталось 10 секунд», который начинает тикать.",
         camera="UI, accelerating push-in", transition="hard cut", on_screen="Открой дверь. / Осталось: 00:10",
         sfx=[(70.13, "tick", -8), (71.13, "tick", -8)]),

    # ===================== SCENE 12 — CLIFFHANGER
    dict(id="S12_A", scene=12, start=71.40, kind="live", anchor="И тут я услышал…",
         visual_ru="Крупно: замок изнутри — цилиндр и вертушка. Полная неподвижность.",
         prompt="close-up of the lock cylinder and the chrome thumb-turn latch of the {DOOR} from inside, absolutely still, cold light from the gap",
         camera="imperceptible push-in", light="cold under-door light", refs=["DOOR"], transition="hard cut",
         sfx=[(72.13, "tick", -9), (73.13, "tick", -10)]),
    dict(id="S12_B", scene=12, start=73.40, kind="live", anchor="…кто-то начал открывать замок снаружи",
         visual_ru="Экстремально крупно: снаружи вставляют ключ, вертушка сама начинает поворачиваться… Резкий обрыв на середине поворота.",
         prompt="extreme close-up: the chrome thumb-turn latch of the {DOOR} begins to rotate on its own as a key turns the cylinder from outside; "
                "nobody is visible; the turn is only half complete",
         camera="locked", light="cold under-door light", refs=["DOOR"], transition="HARD CUT TO BLACK mid-turn at 75.55 (source)",
         sfx=[(73.45, "key_insert", -4), (74.05, "lock_pins", -4), (74.75, "lock_turn", -3)]),
]

# End card (rendered by 05_build.py, silent)
END_CARD_TEXT = ("ЦЕНА ВЫБОРА", "серия 1")

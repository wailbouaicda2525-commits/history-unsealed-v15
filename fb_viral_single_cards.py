#!/usr/bin/env python3
"""
VIRAL SINGLE-IMAGE 4:5 (1080x1350) FACEBOOK MONETIZATION ENGINE
Replaces low-reach multi-photo carousels with THREE high-engagement single-photo formats:
  1) `versus_ab`    : Dedicated Split Showdown Card (OPTION A vs OPTION B — comment war magnet!)
  2) `before_after` : Dedicated BEFORE -> AFTER / THEN vs NOW Impact Card (shares magnet!)
  3) `what_if`      : Dedicated WHAT IF...? 3-Stage Chain-Reaction Card (curiosity magnet!)
  4) `before_after_whatif`: Auto-alternates ODD days = BEFORE vs AFTER, EVEN days = WHAT IF...!
"""
import datetime as dt
import hashlib
import json
import os
import random
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1080, 1350

BRAND_THEMES = {
    "behind_the_curtain": {
        "name": "BEHIND THE CURTAIN",
        "bg": (12, 15, 22),
        "card_a": (36, 16, 22),
        "card_b": (18, 28, 44),
        "panel": (20, 24, 34),
        "accent": (214, 38, 46),     # Soviet Crimson
        "gold": (232, 188, 86),      # Archival Brass
        "cyan": (86, 174, 232),
        "text": (246, 243, 236),
        "muted": (196, 198, 208),
        "hashtags": "#BehindTheCurtain #ColdWar #SecretHistory #Declassified #HistoryFacts",
        "vs_bank": [
            ("COLD WAR SURVIVAL DILEMMA", "WHICH BUNKER WOULD YOU TRUST?",
             "CHEYENNE MOUNTAIN", "2,000 feet of solid granite under Colorado. 25-ton nuclear blast doors. Built to survive a direct hit.",
             "GREENBRIER SECRET BUNKER", "Hidden beneath a luxury 5-star resort for U.S. Congress. Stocked for 1,100 people in total secrecy.",
             "Only one door seals before impact. Type A or B and explain WHY!"),
            ("1983 NUCLEAR STANDOFF", "WHAT WOULD YOU DO IN 5 MINUTES?",
             "OBEY SOVIET PROTOCOL", "Radar screams 5 incoming U.S. missiles. Orders are absolute: launch full nuclear retaliation immediately.",
             "DEFY MOSCOW LIKE PETROV", "Trust your gut that the satellite glitched. Risk court-martial—or save 5 billion human lives.",
             "Stanislav Petrov chose B. Be honest: would you have the nerve? Type A or B!"),
            ("BERLIN 1961 ESCAPE", "WHICH ESCAPE PLAN DO YOU PICK?",
             "DIG A 450-FOOT TUNNEL", "Weeks crawling under East Berlin streets while Stasi patrols walk ten feet above your head.",
             "HOMEMADE HOT-AIR BALLOON", "Sew bedsheets in secret and fly 8,000 feet above searchlights and guard towers at midnight.",
             "Both actually happened in real Cold War history! Which takes more guts—A or B?"),
            ("SPY MISSION BRIEFING", "WHO HAD THE CRAZIER OPERATION?",
             "PROJECT AZORIAN (CIA)", "Build a fake $4B Howard Hughes mining ship to steal a sunken Soviet nuclear sub 3 miles underwater.",
             "THE GREAT SEAL BUG (KGB)", "Hide a battery-free microphone inside a carved wooden eagle hanging in the U.S. Ambassador's office for 7 years.",
             "Which intelligence heist was more genius? Drop A or B below!"),
        ],
        "ba_bank": [
            ("BERLIN — AUGUST 1961", "ONE NIGHT THAT SPLIT A CITY",
             "BEFORE (AUG 12, 1961)", "Families crossed freely across Berlin for work, dinner, and Sunday visits. 60,000 East Berliners commuted west daily.",
             "AFTER (AUG 13, 1961 — 2:00 AM)", "Barbed wire and concrete sealed 155 km overnight. Neighbors woke up trapped on opposite sides for 28 years.",
             "28 YEARS OF SEPARATION CREATED IN A SINGLE NIGHT."),
            ("PRIPYAT — APRIL 1986", "THE CITY FROZEN IN 36 HOURS",
             "BEFORE (APRIL 25, 1986)", "A brand-new Soviet model city of 49,000 young families preparing to open its brand-new May Day amusement park.",
             "AFTER (APRIL 27, 1986 — 2:00 PM)", "1,200 buses evacuated every soul in 3 hours. Dinner plates, toys, and Ferris wheels stood untouched forever.",
             "THE AMUSEMENT PARK NEVER OPENED FOR A SINGLE DAY."),
            ("CUBAN MISSILE CRISIS — OCT 1962", "THE 13 DAYS THAT CHANGED WAR",
             "BEFORE (OCT 1962)", "Zero direct phone line between Washington and Moscow. Urgent diplomatic warnings took hours by coded telegraph.",
             "AFTER (AUG 1963)", "The Moscow–Washington Hotline went live after Vasili Arkhipov stopped a nuclear torpedo launch by a single vote.",
             "ONE OFFICER'S 'NO' SAVED MODERN CIVILIZATION."),
        ],
        "wi_bank": [
            ("WHAT IF STANISLAV PETROV HAD PUSHED THE BUTTON?",
             "SEPTEMBER 26, 1983 • SERPUKHOV-15",
             "MINUTE 01 — FALSE LAUNCH", "Soviet early-warning computers misread sunlight on clouds as 5 U.S. ICBMs. Retaliation launches 1,000+ warheads.",
             "MINUTE 28 — NORAD RESPONSE", "Automated U.S. defense launches full counter-strike before a single missile lands. Every major city in the Northern Hemisphere is targeted.",
             "THE AFTERMATH — NUCLEAR WINTER", "Smoke blocks 70% of sunlight for years. Global agriculture collapses. Over 4 billion people never see 1985.",
             "One man broke orders and saved Earth. Should he be taught in every school?"),
            ("WHAT IF PROJECT AZORIAN HAD RAISED THE ENTIRE SUBMARINE?",
             "JULY 1974 • PACIFIC OCEAN",
             "STAGE 01 — INTACT CODE ROOM", "Instead of snapping at 9,000 ft, the whole Soviet K-129 hull enters the Hughes Glomar Explorer with every cipher machine intact.",
             "STAGE 02 — TOTAL SOVIET BLINDNESS", "The CIA reads every Soviet Pacific submarine patrol and ballistic launch code for the next decade.",
             "STAGE 03 — SECRET ESCALATION", "If Moscow discovers the breach, the Cold War explodes into open naval confrontation across the Pacific.",
             "Would total intelligence have ended the Cold War earlier—or triggered WWIII?"),
        ],
    },
    "history_unsealed": {
        "name": "HISTORY UNSEALED",
        "bg": (10, 20, 38),
        "card_a": (18, 36, 66),
        "card_b": (46, 22, 26),
        "panel": (15, 29, 52),
        "accent": (218, 178, 84),    # Royal Archival Gold
        "gold": (240, 202, 108),
        "cyan": (186, 42, 48),       # Wax Seal Crimson
        "text": (248, 244, 234),
        "muted": (194, 202, 218),
        "hashtags": "#HistoryUnsealed #USHistory #WorldHistory #UntoldHistory #OnThisDay",
        "vs_bank": [
            ("HISTORICAL CROSSROADS", "WHICH EXPEDITION WOULD YOU JOIN?",
             "APOLLO 11 MOON LANDING (1969)", "25 seconds of landing fuel left. Alarm 1202 screaming. One wrong bounce strands you on the Moon forever.",
             "LINDBERGH SOLO ATLANTIC (1927)", "33.5 hours alone over pitch-black freezing ocean with zero radio, no windshield, and fighting sleep every minute.",
             "Which historic leap took more fearless nerve? Type A or B!"),
            ("GREATEST DEALS IN HISTORY", "WHICH GAMBLE WAS MORE INSANE?",
             "LOUISIANA PURCHASE (1803)", "Buy 828,000 square miles from Napoleon for $15 million—literally 3 cents an acre—doubling the U.S. overnight.",
             "ALASKA PURCHASE (1867)", "Mocked as 'Seward's Folly' at $7.2 million—until gold, oil, and Arctic strategy turned it into trillions.",
             "Which signature rewrote world power more? Drop A or B below!"),
            ("UNSOLVED MYSTERIES", "WHICH CASE DO YOU WANT SOLVED?",
             "ROANOKE COLONY (1590)", "115 settlers vanished without a single body—leaving only one word carved into a tree: CROATOAN.",
             "BOSTON $500M ART HEIST (1990)", "Two fake cops walked out with 13 priceless Rembrandt & Vermeer masterpieces in 81 minutes. Still empty frames today.",
             "If you could open ONE sealed truth file forever—A or B?"),
        ],
        "ba_bank": [
            ("CHICAGO — OCTOBER 1871", "HOW FIRE INVENTED THE SKYLINE",
             "BEFORE (OCT 7, 1871)", "A booming wooden frontier city of 300,000 where sidewalks, bridges, and roofs were built almost entirely of dry pine.",
             "AFTER (OCT 10, 1871)", "3.3 square miles reduced to ash. Architects rebuilt in fireproof steel—giving birth to the world's first skyscraper.",
             "OUT OF 30 HOURS OF ASH ROSE MODERN ARCHITECTURE."),
            ("PANAMA ISTHMUS — 1904 TO 1914", "CARVING TWO OCEANS TOGETHER",
             "BEFORE (1904)", "Ships sailing New York to San Francisco had to brave 13,000 miles of deadly storms around South America's Cape Horn.",
             "AFTER (AUG 15, 1914)", "50 miles of giant locks sliced 8,000 miles off global shipping—permanently reshaping world trade and naval power.",
             "ONE SHORTCUT REWROTE EVERY TRADE MAP ON EARTH."),
            ("CALIFORNIA — JANUARY 1848", "ONE FLAKE THAT BUILT THE WEST",
             "BEFORE (JAN 23, 1848)", "San Francisco was a quiet coastal settlement of barely 800 residents far from East Coast power.",
             "AFTER (1849–1855)", "300,000 prospectors surged across land and sea. California jumped straight to U.S. statehood in just two years.",
             "A SINGLE GOLD FLAKE TRIGGERED A CONTINENTAL BOOM."),
        ],
        "wi_bank": [
            ("WHAT IF APOLLO 11 HAD ABORTED THE MOON LANDING?",
             "JULY 20, 1969 • 25 SECONDS OF FUEL",
             "STAGE 01 — ALARM 1202 ABORT", "Flight guidance fails to recognize the computer overload. Houston calls ABORT just 500 feet above the Sea of Tranquility.",
             "STAGE 02 — SOVIET WINDOW OPENS", "NASA delays until late 1969 as budget pressure surges. Moscow pours emergency funding into its N1 lunar rocket.",
             "STAGE 03 — SPACE RACE REWRITTEN", "Instead of Armstrong's immortal words in July 1969, humanity's first lunar footprint becomes an unpredictable 1970s race.",
             "Did a 26-year-old engineer calling 'GO' save the greatest moment of the 20th century?"),
            ("WHAT IF D-DAY HAD LAUNCHED ON JUNE 5, 1944?",
             "ENGLISH CHANNEL • OPERATION OVERLORD",
             "STAGE 01 — STORM CATASTROPHE", "Gale-force winds and 10-foot waves capsize hundreds of flat-bottomed landing craft miles off Normandy beaches.",
             "STAGE 02 — AIR COVER GROUNDED", "Zero Allied bombers can see coastal bunkers through thick cloud decks. Paratroopers scatter into the sea.",
             "STAGE 03 — EUROPE'S FATE DELAYED", "Eisenhower's resignation letter gets published—and the liberation of Western Europe is pushed back a full year.",
             "One Scottish meteorologist's forecast saved D-Day. Did you know that story?"),
        ],
    },
    "last_map_standing": {
        "name": "LAST MAP STANDING",
        "bg": (10, 16, 26),
        "card_a": (16, 44, 58),
        "card_b": (48, 22, 24),
        "panel": (16, 24, 38),
        "accent": (56, 189, 248),    # Tactical Satellite Cyan
        "gold": (250, 204, 21),      # Alert Amber
        "cyan": (239, 68, 68),       # Elimination Red
        "text": (245, 248, 255),
        "muted": (182, 196, 216),
        "hashtags": "#LastMapStanding #Geography #Maps #Geopolitics #Survival #WhatIf",
        "vs_bank": [
            ("GLOBAL BLACKOUT SHOWDOWN", "WHICH NATION SURVIVES LAST?",
             "SWITZERLAND", "Nuclear bunkers for 114% of its population, Alpine hydro-dams, neutral fortress valleys, and months of stored grain.",
             "ICELAND", "100% geothermal & hydro energy independence, isolated North Atlantic moat, abundant fish, and tiny demand.",
             "Global grid dies for 1 full year. Who is the Last Map Standing—A or B?"),
            ("U.S. STATE SURVIVAL BATTLE", "WHO OUTLASTS A SUPPLY COLLAPSE?",
             "TEXAS", "Independent power grid, massive oil & gas reserves, huge cattle & farmland output, and Gulf port access.",
             "MONTANA", "Low population density, massive freshwater headwaters, vast grain/ranch land, and natural Rocky Mountain defense.",
             "Every interstate highway closes for 180 days. Pick your survival state—A or B!"),
            ("SUPERPOWER GEOGRAPHY TEST", "WHICH BORDER IS HARDER TO INVADE?",
             "UNITED STATES", "Protected by two massive oceans, friendly northern/southern buffers, and the world's largest navigable river network.",
             "RUSSIA", "11 time zones of strategic depth, brutal winter logistics, vast forests, and self-sufficient raw resources.",
             "Pure geography—no politics. Which fortress is more unbeatable—A or B?"),
        ],
        "ba_bank": [
            ("EARTH WITHOUT OIL — 72 HOURS", "HOW FAST THE MODERN MAP STOPS",
             "BEFORE (HOUR 0)", "100 million barrels burn daily powering 95% of cargo ships, food trucks, tractors, and global aviation.",
             "AFTER (HOUR 72)", "Supermarket shelves empty in 48 hours. Megacities run out of fresh food first while hydro/rail nations hold longest.",
             "WOULD YOUR COUNTRY MAKE IT PAST WEEK TWO?"),
            ("IF OCEANS DROPPED 100 METERS", "THE HIDDEN CONTINENTS APPEAR",
             "BEFORE (TODAY'S COASTLINE)", "Britain is an island, Alaska and Siberia are split by sea, and Southeast Asia is thousands of separate islands.",
             "AFTER (-100M SEA LEVEL)", "Doggerland reconnects Europe to the UK, the Bering Land Bridge returns, and Sundaland forms a massive Asian continent.",
             "MILLIONS OF SQUARE MILES OF NEW LAND EMERGE."),
        ],
        "wi_bank": [
            ("WHAT IF EVERY BORDER ON EARTH VANISHED OVERNIGHT?",
             "GLOBAL SIMULATION • DAY 1 TO DAY 365",
             "DAY 01 — MASS MIGRATION", "Visas, tariffs, and customs walls disappear instantly. Coastal climate hubs and mega-economies see historic population surges.",
             "DAY 90 — RESOURCE SHIFT", "Global trade explodes without bottlenecks—while housing, freshwater, and power grids face extreme overload.",
             "DAY 365 — NEW NATURAL REGIONS", "Humanity reorganizes not by flags, but by river basins, climates, and energy grids.",
             "Would Earth become richer—or collapse into chaos? Drop your country & vote!"),
            ("WHAT IF EVERY U.S. STATE BECAME ITS OWN COUNTRY?",
             "NORTH AMERICA SIMULATION • 50 NATIONS",
             "DAY 01 — ECONOMIC GIANTS", "California (#5 global economy), Texas (energy superpower), and New York (finance hub) instantly rival Europe.",
             "DAY 60 — WATER & FOOD LEVERAGE", "Midwest breadbasket states control food exports while Colorado River states negotiate high-stakes water treaties.",
             "DAY 365 — REGIONAL ALLIANCES", "Landlocked states form trade blocs—and only 6–8 states remain 100% self-sufficient alone.",
             "Does YOUR state survive solo—or join an alliance? Comment below!"),
        ],
    },
    "watch_block_ville": {
        "name": "WATCH BLOCK VILLE",
        "bg": (14, 18, 36),
        "card_a": (24, 48, 92),
        "card_b": (96, 20, 34),
        "panel": (22, 28, 52),
        "accent": (255, 220, 30),    # Pixar Electric Yellow
        "gold": (255, 220, 30),
        "cyan": (239, 35, 50),       # Comic Crimson
        "text": (255, 255, 255),
        "muted": (212, 222, 242),
        "hashtags": "#WatchBlockVille #3DAnimation #AnimatedStory #Comedy #Cartoon #WhatIf",
        "vs_bank": [
            ("BLOCKVILLE CRAZY LAW #02", "WHICH CHOICE SAVES YOU?",
             "PAY $299/MO GRAVITY TAX", "Keep your house bolted to the sidewalk—but go completely broke paying Mayor Snodgrass every month!",
             "REFUSE & FLOAT TO SPACE", "Save your cash—and wake up with your bedroom, couch, and snacks drifting 10,000 feet above the clouds!",
             "Be 100% honest: are you paying the Gravity Tax or floating away? Type A or B!"),
            ("BLOCKVILLE CRAZY LAW #01", "WOULD YOU SURVIVE THIS TOWN?",
             "CREDIT SCORE ABOVE YOUR HEAD", "Everyone sees your exact number glowing in neon—one late bill turns your coffee from $3 to $300!",
             "EVERY LIE MAKES YOU SHRINK", "Tell one tiny excuse to your boss and suddenly you're 4 inches tall dodging neighborhood squirrels!",
             "Which insane Blockville rule would ruin your life faster? Type A or B!"),
            ("BLOCKVILLE SURVIVAL PICK", "WHO DO YOU TEAM UP WITH?",
             "MILO (THE CHAOTIC GENIUS)", "Always breaks the town's dumbest law in 30 seconds—somehow survives every disaster by pure luck.",
             "GRANDMA BETTY (NO MERCY)", "Has 47 loopholes memorized and once made the Mayor cry using a coupon from 1984.",
             "Pick your Blockville partner! Drop A or B below!"),
        ],
        "ba_bank": [
            ("BLOCKVILLE — GRAVITY TAX DAY", "BEFORE vs AFTER THE MAYOR'S LAW",
             "BEFORE (8:59 AM)", "Milo is peacefully eating cereal in his kitchen. Rent is paid. Everything is sitting nicely on the floor.",
             "AFTER (9:01 AM)", "The Gravity Tax hits $299/month. Milo refuses to pay—and his entire house blasts off like a rocket past the clouds!",
             "FULL 3D MOVIE DROPS TONIGHT ON WATCH BLOCK VILLE!"),
            ("BLOCKVILLE — CREDIT SCORE LAW", "BEFORE vs AFTER ONE MISSED BILL",
             "BEFORE (SCORE: 820)", "VIP red carpet at the bakery, free upgrades, and Mayor Snodgrass waves hello like your best friend.",
             "AFTER (SCORE: 410)", "The automatic doors lock in your face, pigeons judge you, and a single donut costs $49.99!",
             "WHAT WOULD YOUR GLOWING SCORE BE TODAY? COMMENT!"),
        ],
        "wi_bank": [
            ("WHAT IF YOUR CREDIT SCORE FLOATED OVER YOUR HEAD?",
             "BLOCKVILLE REALITY CHECK • 24 HOURS",
             "HOUR 01 — INSTANT CHAOS", "Walking into work, the café, or a first date—everybody sees a giant glowing number hovering 6 inches above your hair.",
             "HOUR 08 — DYNAMIC PRICING", "Stores scan your head at the door. 800+ gets 50% off; under 550 gets handed a plastic chair outside.",
             "HOUR 24 — TOTAL REBELLION", "Everyone starts wearing 4-foot-tall hats until the Mayor bans hats too!",
             "How long before your town completely riots? Comment below!"),
            ("WHAT IF GRAVITY COST $299 A MONTH IN REAL LIFE?",
             "BLOCKVILLE SIMULATION • DAY 1",
             "STAGE 01 — BILLING DAY", "Half the neighborhood cancels their subscription thinking it's a bluff—until cars start drifting off driveways.",
             "STAGE 02 — SKY TRAFFIC", "Commuting turns into swimming through clouds with leaf blowers taped to backpacks.",
             "STAGE 03 — MAYOR'S PROBLEM", "Nobody comes down to pay taxes anymore—so the entire economy moves 500 feet into the sky!",
             "Would you pay the subscription or embrace zero-gravity life? Comment!"),
        ],
    },
}

def _find_font(bold=True):
    here = Path(__file__).resolve().parent
    cands = [
        str(here / "fonts" / ("Montserrat-Black.ttf" if bold else "Montserrat-Bold.ttf")),
        str(here / "fonts" / ("Montserrat-ExtraBold.ttf" if bold else "Montserrat-SemiBold.ttf")),
        str(here / "fonts" / "Montserrat-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in cands:
        if os.path.exists(p):
            return p
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def _f(size, bold=True):
    return ImageFont.truetype(_find_font(bold), size)

def _wrap(dr, text, font, max_w, max_lines=4):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if dr.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
            if len(lines) >= max_lines - 1:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    return lines

def _fit_text_lines(dr, text, max_w, start_sz, min_sz, max_lines=2, bold=True):
    for sz in range(start_sz, min_sz - 1, -2):
        fn = _f(sz, bold=bold)
        lns = _wrap(dr, text, fn, max_w, max_lines=max_lines + 1)
        if len(lns) <= max_lines and all(dr.textbbox((0, 0), l, font=fn)[2] <= max_w for l in lns):
            return fn, lns
    fn = _f(min_sz, bold=bold)
    return fn, _wrap(dr, text, fn, max_w, max_lines=max_lines)

def _base_canvas(theme):
    im = Image.new("RGB", (W, H), theme["bg"])
    dr = ImageDraw.Draw(im)
    # Subtle atmospheric vertical studio sheen
    br, bg_, bb = theme["bg"]
    for y in range(H):
        bump = int(14 * (1.0 - abs(y - H * 0.45) / (H * 0.65)))
        bump = max(0, bump)
        dr.line([(0, y), (W, y)], fill=(min(255, br + bump), min(255, bg_ + bump), min(255, bb + bump + 4)))
    # Crisp outer double frame
    dr.rectangle([28, 28, W - 28, H - 28], outline=theme["accent"], width=4)
    dr.rectangle([42, 42, W - 42, H - 42], outline=(theme["gold"][0]//2, theme["gold"][1]//2, theme["gold"][2]//2), width=2)
    return im, dr

def render_versus_ab_card(brand_key, data, out_path):
    """Single 1080x1350 Split-Showdown Photo Card: OPTION A vs OPTION B."""
    kicker, headline, a_title, a_desc, b_title, b_desc, cta = data
    th = BRAND_THEMES[brand_key]
    im, dr = _base_canvas(th)

    # Top Pill Badge
    f_pill = _f(26, True)
    pill_txt = f"{th['name']}  •  {kicker}"
    pw = min(920, dr.textbbox((0, 0), pill_txt, font=f_pill)[2] + 64)
    dr.rounded_rectangle([W//2 - pw//2, 68, W//2 + pw//2, 124], radius=28, fill=th["accent"])
    p_col = (12, 16, 26) if sum(th["accent"]) > 420 else (255, 255, 255)
    tw = dr.textbbox((0, 0), pill_txt, font=f_pill)[2]
    dr.text((W//2 - tw//2, 81), pill_txt, font=f_pill, fill=p_col)

    # Bold Main Headline
    f_hl, hl_lines = _fit_text_lines(dr, headline.upper(), 940, 62, 42, max_lines=2, bold=True)
    y = 148
    for ln in hl_lines:
        lw = dr.textbbox((0, 0), ln, font=f_hl)[2]
        dr.text((W//2 - lw//2, y), ln, font=f_hl, fill=th["text"])
        y += int(f_hl.size * 1.15)

    # OPTION A CARD (y = 312 .. 710)
    card_x0, card_x1 = 70, W - 70
    a_y0, a_y1 = 312, 718
    dr.rounded_rectangle([card_x0, a_y0, card_x1, a_y1], radius=26, fill=th["card_a"], outline=th["accent"], width=5)
    # Big glowing A badge on left
    dr.rounded_rectangle([card_x0 + 28, a_y0 + 30, card_x0 + 162, a_y0 + 164], radius=22, fill=th["accent"])
    fa_big = _f(92, True)
    aw = dr.textbbox((0, 0), "A", font=fa_big)[2]
    dr.text((card_x0 + 95 - aw//2, a_y0 + 44), "A", font=fa_big, fill=p_col)
    dr.text((card_x0 + 190, a_y0 + 34), "OPTION A", font=_f(26, True), fill=th["gold"])
    fa_t, a_tl = _fit_text_lines(dr, a_title.upper(), 710, 44, 30, max_lines=2, bold=True)
    ty = a_y0 + 72
    for ln in a_tl:
        dr.text((card_x0 + 190, ty), ln, font=fa_t, fill=th["text"])
        ty += int(fa_t.size * 1.15)
    fa_d = _f(31, False)
    dy = max(ty + 18, a_y0 + 188)
    for ln in _wrap(dr, a_desc, fa_d, card_x1 - card_x0 - 68, max_lines=4):
        dr.text((card_x0 + 34, dy), ln, font=fa_d, fill=th["muted"])
        dy += 42

    # OPTION B CARD (y = 782 .. 1188)
    b_y0, b_y1 = 782, 1188
    dr.rounded_rectangle([card_x0, b_y0, card_x1, b_y1], radius=26, fill=th["card_b"], outline=th["gold"], width=5)
    dr.rounded_rectangle([card_x0 + 28, b_y0 + 30, card_x0 + 162, b_y0 + 164], radius=22, fill=th["gold"])
    bw = dr.textbbox((0, 0), "B", font=fa_big)[2]
    dr.text((card_x0 + 95 - bw//2, b_y0 + 44), "B", font=fa_big, fill=(12, 16, 26))
    dr.text((card_x0 + 190, b_y0 + 34), "OPTION B", font=_f(26, True), fill=th["gold"])
    fb_t, b_tl = _fit_text_lines(dr, b_title.upper(), 710, 44, 30, max_lines=2, bold=True)
    ty = b_y0 + 72
    for ln in b_tl:
        dr.text((card_x0 + 190, ty), ln, font=fb_t, fill=th["text"])
        ty += int(fb_t.size * 1.15)
    dy = max(ty + 18, b_y0 + 188)
    for ln in _wrap(dr, b_desc, fa_d, card_x1 - card_x0 - 68, max_lines=4):
        dr.text((card_x0 + 34, dy), ln, font=fa_d, fill=th["muted"])
        dy += 42

    # GIANT CENTER VS MEDALLION (bridges Card A & Card B!)
    vcx, vcy, vr = W // 2, (a_y1 + b_y0) // 2, 66
    dr.ellipse([vcx - vr - 8, vcy - vr - 8, vcx + vr + 8, vcy + vr + 8], fill=th["bg"])
    dr.ellipse([vcx - vr, vcy - vr, vcx + vr, vcy + vr], fill=th["cyan"] if brand_key != "history_unsealed" else th["cyan"], outline=th["gold"], width=6)
    f_vs = _f(54, True)
    vw = dr.textbbox((0, 0), "VS", font=f_vs)[2]
    dr.text((vcx - vw//2, vcy - 32), "VS", font=f_vs, fill=(255, 255, 255))

    # Bottom Comment CTA Pill
    dr.rounded_rectangle([70, 1218, W - 70, 1296], radius=20, fill=th["accent"])
    cta_s = 'TYPE "A" OR "B" IN THE COMMENTS!'
    f_cta, _ = _fit_text_lines(dr, cta_s, 900, 34, 24, max_lines=1, bold=True)
    cw = dr.textbbox((0, 0), cta_s, font=f_cta)[2]
    dr.text((W//2 - cw//2, 1238), cta_s, font=f_cta, fill=p_col)

    im.save(out_path, quality=93)
    return out_path

def render_before_after_card(brand_key, data, out_path):
    """Single 1080x1350 BEFORE vs AFTER Comparison Card."""
    kicker, headline, b_lbl, b_txt, a_lbl, a_txt, bottom_punch = data
    th = BRAND_THEMES[brand_key]
    im, dr = _base_canvas(th)

    # Top Badge
    f_pill = _f(26, True)
    pill_txt = f"BEFORE vs AFTER  •  {kicker}"
    pw = min(940, dr.textbbox((0, 0), pill_txt, font=f_pill)[2] + 64)
    dr.rounded_rectangle([W//2 - pw//2, 68, W//2 + pw//2, 124], radius=28, fill=th["gold"])
    tw = dr.textbbox((0, 0), pill_txt, font=f_pill)[2]
    dr.text((W//2 - tw//2, 81), pill_txt, font=f_pill, fill=(12, 16, 26))

    # Main Headline
    f_hl, hl_lines = _fit_text_lines(dr, headline.upper(), 940, 62, 42, max_lines=2, bold=True)
    y = 148
    for ln in hl_lines:
        lw = dr.textbbox((0, 0), ln, font=f_hl)[2]
        dr.text((W//2 - lw//2, y), ln, font=f_hl, fill=th["text"])
        y += int(f_hl.size * 1.15)

    # BEFORE PANEL (y = 314 .. 674)
    x0, x1 = 70, W - 70
    dr.rounded_rectangle([x0, 314, x1, 676], radius=24, fill=(24, 32, 46), outline=(120, 140, 168), width=4)
    dr.rounded_rectangle([x0 + 28, 342, x0 + 540, 398], radius=12, fill=(70, 92, 122))
    dr.text((x0 + 48, 354), b_lbl.upper()[:34], font=_f(26, True), fill=(255, 255, 255))
    f_b = _f(35, False)
    by = 426
    for ln in _wrap(dr, b_txt, f_b, x1 - x0 - 76, max_lines=5):
        dr.text((x0 + 38, by), ln, font=f_b, fill=th["text"])
        by += 48

    # DRAMATIC DIVIDER ARROW BAR (y = 696 .. 768)
    dr.rounded_rectangle([W//2 - 280, 696, W//2 + 280, 764], radius=34, fill=th["accent"])
    p_col = (12, 16, 26) if sum(th["accent"]) > 420 else (255, 255, 255)
    mid_t = "▼   THE TURNING POINT   ▼"
    mw = dr.textbbox((0, 0), mid_t, font=_f(28, True))[2]
    dr.text((W//2 - mw//2, 714), mid_t, font=_f(28, True), fill=p_col)

    # AFTER PANEL (y = 786 .. 1152)
    dr.rounded_rectangle([x0, 786, x1, 1152], radius=24, fill=th["card_a"], outline=th["accent"], width=5)
    dr.rounded_rectangle([x0 + 28, 814, x0 + 620, 870], radius=12, fill=th["accent"])
    dr.text((x0 + 48, 826), a_lbl.upper()[:38], font=_f(26, True), fill=p_col)
    ay = 898
    for ln in _wrap(dr, a_txt, f_b, x1 - x0 - 76, max_lines=5):
        dr.text((x0 + 38, ay), ln, font=f_b, fill=(255, 252, 245))
        ay += 48

    # Bottom Punch Stat + Brand Bar
    dr.rounded_rectangle([x0, 1184, x1, 1296], radius=20, fill=th["panel"], outline=th["gold"], width=3)
    f_p, pl = _fit_text_lines(dr, bottom_punch.upper(), x1 - x0 - 60, 30, 22, max_lines=2, bold=True)
    py = 1200 if len(pl) == 2 else 1222
    for ln in pl:
        lw = dr.textbbox((0, 0), ln, font=f_p)[2]
        dr.text((W//2 - lw//2, py), ln, font=f_p, fill=th["gold"])
        py += 38

    im.save(out_path, quality=93)
    return out_path

def render_what_if_card(brand_key, data, out_path):
    """Single 1080x1350 WHAT IF...? 3-Stage Chain Reaction Poster."""
    headline, sub_tag, s1_t, s1_d, s2_t, s2_d, s3_t, s3_d, cta = data
    th = BRAND_THEMES[brand_key]
    im, dr = _base_canvas(th)

    # Top Mystery Badge
    f_pill = _f(26, True)
    pill_txt = f"WHAT IF...?  •  {sub_tag}"
    pw = min(940, dr.textbbox((0, 0), pill_txt, font=f_pill)[2] + 64)
    dr.rounded_rectangle([W//2 - pw//2, 68, W//2 + pw//2, 124], radius=28, fill=th["accent"])
    p_col = (12, 16, 26) if sum(th["accent"]) > 420 else (255, 255, 255)
    tw = dr.textbbox((0, 0), pill_txt, font=f_pill)[2]
    dr.text((W//2 - tw//2, 81), pill_txt, font=f_pill, fill=p_col)

    # Giant WHAT IF Headline
    f_hl, hl_lines = _fit_text_lines(dr, headline.upper(), 940, 58, 38, max_lines=3, bold=True)
    y = 148
    for idx_l, ln in enumerate(hl_lines):
        lw = dr.textbbox((0, 0), ln, font=f_hl)[2]
        dr.text((W//2 - lw//2, y), ln, font=f_hl, fill=th["gold"] if idx_l == 0 else th["text"])
        y += int(f_hl.size * 1.15)

    # 3 Chain-Reaction Stage Cards
    stages = [("01", s1_t, s1_d), ("02", s2_t, s2_d), ("03", s3_t, s3_d)]
    x0, x1 = 70, W - 70
    sy = min(max(y + 18, 344), 392)
    card_h = 246
    gap = 20
    for idx_s, (num, st, sd) in enumerate(stages):
        cy0, cy1 = sy + idx_s * (card_h + gap), sy + idx_s * (card_h + gap) + card_h
        is_last = (idx_s == 2)
        bg_c = th["card_a"] if is_last else th["panel"]
        out_c = th["accent"] if is_last else th["gold"]
        dr.rounded_rectangle([x0, cy0, x1, cy1], radius=22, fill=bg_c, outline=out_c, width=4)
        # Number Square
        dr.rounded_rectangle([x0 + 24, cy0 + 24, x0 + 124, cy0 + 124], radius=18, fill=out_c)
        nc = (12, 16, 26) if sum(out_c) > 420 else (255, 255, 255)
        f_num = _f(52, True)
        nw = dr.textbbox((0, 0), num, font=f_num)[2]
        dr.text((x0 + 74 - nw//2, cy0 + 42), num, font=f_num, fill=nc)
        # Stage title & body
        ft, _ = _fit_text_lines(dr, st.upper(), 740, 34, 24, max_lines=1, bold=True)
        dr.text((x0 + 150, cy0 + 30), st.upper(), font=ft, fill=th["gold"] if not is_last else th["text"])
        fb = _f(29, False)
        by = cy0 + 82
        for ln in _wrap(dr, sd, fb, 750, max_lines=4):
            dr.text((x0 + 150, by), ln, font=fb, fill=th["muted"] if not is_last else (250, 246, 238))
            by += 39

    # Bottom Debate CTA
    dr.rounded_rectangle([x0, 1218, x1, 1296], radius=20, fill=th["gold"])
    cta_s = f"{th['name']}  •  WHAT DO YOU THINK? COMMENT BELOW!"
    f_cta, _ = _fit_text_lines(dr, cta_s, 900, 28, 20, max_lines=1, bold=True)
    cw = dr.textbbox((0, 0), cta_s, font=f_cta)[2]
    dr.text((W//2 - cw//2, 1242), cta_s, font=f_cta, fill=(12, 16, 26))

    im.save(out_path, quality=93)
    return out_path


def _groq_json(prompt: str) -> dict | None:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return None
    for model in ("openai/gpt-oss-120b", "llama-3.1-8b-instant"):
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "UnsealedFBEngine/2.0"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "Return ONLY a valid compact JSON object. No markdown fences. Punchy English viral Facebook copy."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.92,
                    "max_tokens": 520,
                    "response_format": {"type": "json_object"},
                },
                timeout=25,
            )
            if r.status_code == 200:
                txt = r.json()["choices"][0]["message"]["content"].strip()
                return json.loads(txt)
        except Exception as exc:
            print(f"[GROQ VIRAL CARD] {model} warning: {exc}", flush=True)
    return None


def _pick_or_generate(brand_key: str, card_kind: str) -> tuple:
    """Generates a fresh unique viral topic via Groq (seeded by today's date + random salt), falling back to curated bank."""
    th = BRAND_THEMES[brand_key]
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    day_idx = dt.datetime.now(dt.timezone.utc).timetuple().tm_yday

    niche_desc = {
        "behind_the_curtain": "Cold War espionage, declassified CIA/KGB operations, Iron Curtain bunkers, nuclear near-misses, Soviet life (1945-1991)",
        "history_unsealed": "Dramatic true U.S. & World History turning points, historical expeditions, disasters, mysteries, inventions (79 AD - 1990)",
        "last_map_standing": "Geopolitics, world & U.S. state map survival scenarios, geography fortresses, resource collapses, borders",
        "watch_block_ville": "Funny chaotic 3D animated city where Mayor Snodgrass passes absurd rules (Credit Score over head, Gravity Tax, No Lying, Sleep Tax) starring Milo & Grandma Betty",
    }[brand_key]

    if card_kind == "versus_ab":
        prompt = (
            f"Brand: {th['name']} ({niche_desc}). Date: {today}.\n"
            f"Create ONE fresh viral Facebook 'A vs B' showdown dilemma that sparks massive comment debates.\n"
            f"JSON keys: kicker (<=28 chars), headline (<=34 chars, question), a_title (<=28 chars), a_desc (<=125 chars), "
            f"b_title (<=28 chars), b_desc (<=125 chars), cta (<=115 chars engaging question asking readers to comment A or B)."
        )
        g = _groq_json(prompt)
        if g and all(g.get(k) for k in ("kicker", "headline", "a_title", "a_desc", "b_title", "b_desc", "cta")):
            return (str(g["kicker"])[:30], str(g["headline"])[:42], str(g["a_title"])[:32], str(g["a_desc"])[:140],
                    str(g["b_title"])[:32], str(g["b_desc"])[:140], str(g["cta"])[:140])
        bank = th["vs_bank"]
        return bank[day_idx % len(bank)]

    elif card_kind == "before_after":
        prompt = (
            f"Brand: {th['name']} ({niche_desc}). Date: {today}.\n"
            f"Create ONE jaw-dropping viral Facebook 'BEFORE vs AFTER' transformation card.\n"
            f"JSON keys: kicker (<=28 chars), headline (<=36 chars), before_label (<=28 chars), before_desc (<=145 chars), "
            f"after_label (<=30 chars), after_desc (<=145 chars), punchline (<=65 chars bold takeaway)."
        )
        g = _groq_json(prompt)
        if g and all(g.get(k) for k in ("kicker", "headline", "before_label", "before_desc", "after_label", "after_desc", "punchline")):
            return (str(g["kicker"])[:30], str(g["headline"])[:42], str(g["before_label"])[:32], str(g["before_desc"])[:155],
                    str(g["after_label"])[:34], str(g["after_desc"])[:155], str(g["punchline"])[:72])
        bank = th["ba_bank"]
        return bank[day_idx % len(bank)]

    else:  # what_if
        prompt = (
            f"Brand: {th['name']} ({niche_desc}). Date: {today}.\n"
            f"Create ONE viral Facebook 'WHAT IF...?' 3-stage chain reaction card.\n"
            f"JSON keys: headline (starts with WHAT IF, <=48 chars), sub_tag (<=28 chars), "
            f"s1_title (<=30 chars), s1_desc (<=125 chars), s2_title (<=30 chars), s2_desc (<=125 chars), "
            f"s3_title (<=30 chars), s3_desc (<=125 chars), cta (<=120 chars debate question)."
        )
        g = _groq_json(prompt)
        if g and all(g.get(k) for k in ("headline", "sub_tag", "s1_title", "s1_desc", "s2_title", "s2_desc", "s3_title", "s3_desc", "cta")):
            return (str(g["headline"])[:54], str(g["sub_tag"])[:30], str(g["s1_title"])[:32], str(g["s1_desc"])[:135],
                    str(g["s2_title"])[:32], str(g["s2_desc"])[:135], str(g["s3_title"])[:32], str(g["s3_desc"])[:135],
                    str(g["cta"])[:140])
        bank = th["wi_bank"]
        return bank[day_idx % len(bank)]


def publish_single_photo_fb(image_path: str | Path, caption: str) -> str | None:
    """Publishes a single full-screen 4:5 (1080x1350) photo directly to Facebook Page via Graph API v24.0."""
    pid = os.environ.get("FB_PAGE_ID", "").strip()
    tok = os.environ.get("FB_PAGE_ACCESS_TOKEN", "").strip()
    if not (pid and tok):
        print("[FB SINGLE PHOTO] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN not configured)", flush=True)
        return None
    with open(image_path, "rb") as fh:
        r = requests.post(
            f"https://graph.facebook.com/v24.0/{pid}/photos",
            data={"access_token": tok, "message": caption, "published": "true"},
            files={"source": (Path(image_path).name, fh, "image/jpeg")},
            timeout=90,
        )
    data = r.json() if r.text.strip() else {}
    if r.status_code >= 400 or "error" in data:
        raise RuntimeError(f"[FB SINGLE PHOTO ERROR {r.status_code}] {data}")
    post_id = data.get("post_id") or data.get("id")
    print(f"[FB SINGLE PHOTO LIVE!] post_id={post_id} ({Path(image_path).name})", flush=True)
    return str(post_id)


def run_viral_single_card(brand_key: str, mode: str, out_dir: str | Path = "/tmp", dry_run: bool = False) -> str | None:
    """
    Main entrypoint for ALL 4 Facebook Pages:
      - mode='versus_ab'           -> Split A vs B Showdown Single Photo
      - mode='before_after'        -> BEFORE vs AFTER Single Photo
      - mode='what_if'             -> WHAT IF...? 3-Stage Single Photo
      - mode='before_after_whatif' -> Auto-alternates: ODD day = BEFORE vs AFTER, EVEN day = WHAT IF...!
    """
    th = BRAND_THEMES[brand_key]
    if mode == "before_after_whatif":
        day_num = dt.datetime.now(dt.timezone.utc).day
        actual = "before_after" if (day_num % 2 == 1) else "what_if"
    else:
        actual = mode

    data = _pick_or_generate(brand_key, actual)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_jpg = out_dir / f"fb_{brand_key}_{actual}.jpg"

    if actual == "versus_ab":
        render_versus_ab_card(brand_key, data, out_jpg)
        kicker, headline, a_t, a_d, b_t, b_d, cta = data
        caption = (
            f"⚔️ {headline}\n\n"
            f"🅰️ {a_t}: {a_d}\n\n"
            f"🅱️ {b_t}: {b_d}\n\n"
            f"👇 {cta}\n"
            f"🔔 Follow {th['name'].title()} for daily Reels, full movies & interactive challenges!\n\n"
            f"{th['hashtags']} #PickOne #Debate"
        )
    elif actual == "before_after":
        render_before_after_card(brand_key, data, out_jpg)
        kicker, headline, b_l, b_t, a_l, a_t, punch = data
        caption = (
            f"⏳ BEFORE vs AFTER — {headline}\n\n"
            f"⏪ {b_l}: {b_t}\n\n"
            f"⏩ {a_l}: {a_t}\n\n"
            f"💥 {punch}\n"
            f"👇 Did you know how fast everything changed? Drop your thoughts & share this!\n\n"
            f"{th['hashtags']} #BeforeAndAfter #ThenAndNow"
        )
    else:
        render_what_if_card(brand_key, data, out_jpg)
        headline, sub_tag, s1_t, s1_d, s2_t, s2_d, s3_t, s3_d, cta = data
        caption = (
            f"🤯 {headline}\n\n"
            f"1️⃣ {s1_t}: {s1_d}\n"
            f"2️⃣ {s2_t}: {s2_d}\n"
            f"3️⃣ {s3_t}: {s3_d}\n\n"
            f"👇 {cta}\n"
            f"🔔 Follow {th['name'].title()} for daily deep dives & full documentaries!\n\n"
            f"{th['hashtags']} #WhatIf #AlternateHistory"
        )

    print(f"[VIRAL CARD READY] brand={brand_key} mode={actual} -> {out_jpg}", flush=True)
    if dry_run:
        print(f"[DRY-RUN CAPTION]\n{caption}", flush=True)
        return "dry_run_ok"
    return publish_single_photo_fb(out_jpg, caption)

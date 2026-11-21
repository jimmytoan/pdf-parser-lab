"""Generate the synthetic test corpus with exact ground truth and question set.

Everything here is fictional: the company, people, vessels, places and numbers are invented
by a seeded generator. No customer, company or personal data is used.

Outputs (under corpus/):
  pdf/<doc>.pdf            the test PDFs
  truth/<doc>.json         per-page ground truth (body blocks in reading order, tables, forms)
  questions.jsonl          questions with known answers, linked to doc + page
  manifest.json            documents, page counts, categories, pilot page selection
"""
from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout import Composer, register_fonts, wrap  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "corpus")
PDF = os.path.join(OUT, "pdf")
TRUTH = os.path.join(OUT, "truth")
SEED = 20261121

QUESTIONS: list[dict] = []


class Unique:
    """Hands out values never used before anywhere in the corpus, so an answer string
    found in a retrieved chunk can only come from the right fact."""

    def __init__(self, rng):
        self.rng, self.used = rng, set()

    def num(self, lo, hi, fmt="{:,}"):
        while True:
            v = self.rng.randint(lo, hi)
            s = fmt.format(v)
            if s not in self.used and str(v) not in self.used:
                self.used.add(s)
                self.used.add(str(v))
                return s

    def pick(self, pool):
        free = [p for p in pool if p not in self.used]
        v = self.rng.choice(free)
        self.used.add(v)
        return v


def q(doc, page, kind, question, answers, lang="en", evidence=None):
    QUESTIONS.append({"qid": f"q{len(QUESTIONS)+1:04d}", "doc": doc, "page": page, "kind": kind,
                      "question": question, "answers": answers if isinstance(answers, list) else [answers],
                      "evidence": evidence or (answers[0] if isinstance(answers, list) else answers), "lang": lang})


def save_truth(doc, pages, category, extra=None):
    os.makedirs(TRUTH, exist_ok=True)
    data = {"doc": doc, "category": category, "pages": pages}
    if extra:
        data.update(extra)
    with open(os.path.join(TRUTH, f"{doc}.json"), "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


# --------------------------------------------------------------------------------------
# Vocabulary for the fictional Corvane Maritime Group
# --------------------------------------------------------------------------------------
PLACES = ["Marrow Point", "Esker Bay", "Hollin Quay", "Tavish Reach", "Brenlow", "Ostrava Sound", "Kelmscar",
          "Durrant Flats", "Saltmere", "Ivel Harbour", "Calder Spit", "Fennick Island", "Port Aldane", "Wyre Basin",
          "Larchmont Cove", "Quill Head", "Ravensgarth", "Sorrel Point", "Tamsin Bay", "Vantor Strand",
          "Windle Haven", "Yarrow Mouth", "Ashby Shoal", "Coldharbour East", "Dunmere"]
PLACES += [f"{a} {b}" for a in ["Garrow", "Helmsby", "Kinlet", "Morvane", "Pellow", "Strand", "Thorne", "Ullock"]
           for b in ["Quay", "Reach", "Haven", "Point", "Sound", "Bay"]]
PROGRAMS = ["Project Lantern", "Bluewater 30", "Harbour Grid", "Clearwake", "Tidewatch", "Northstar Retrofit",
            "Keel Forward", "Brightdeck", "Seaward Skills", "Anchorline", "Driftless", "Lowsulphur Path"]
SURNAMES = ["Okafor", "Lindqvist", "Ferreira", "Nakamura", "Abernathy", "Castellanos", "Duvall", "Haugen",
            "Iyer", "Kowalczyk", "Moreau", "Oyelaran", "Petrov", "Quintero", "Rasmussen", "Szabo", "Tanaka",
            "Vanterpool", "Whitcombe", "Zielinski", "Brannock", "Edevane", "Galloway", "Huxtable",
            "Achterberg", "Bellamy", "Cruickshank", "Delacroix", "Esterhazy", "Fairweather", "Grimaldi", "Holloway",
            "Ingersoll", "Jablonski", "Kerrigan", "Lachance", "Montague", "Nordqvist", "Ostrowski", "Pemberton"]
GIVEN = ["Amara", "Bastian", "Celeste", "Dorian", "Elif", "Farrah", "Gideon", "Helena", "Ines", "Jonah", "Keira",
         "Lucan", "Mireille", "Niall", "Odile", "Pavel", "Rhea", "Soren", "Talia", "Viktor", "Wren", "Yusuf"]
VESSEL_A = ["Northern", "Silver", "Coral", "Granite", "Amber", "Cobalt", "Ivory", "Juniper", "Linden", "Maple",
            "Onyx", "Pearl", "Quartz", "Russet", "Sable", "Topaz", "Umber", "Vesper", "Willow", "Zephyr"]
VESSEL_B = ["Tern", "Heron", "Gannet", "Petrel", "Plover", "Osprey", "Curlew", "Kittiwake", "Fulmar", "Shearwater",
            "Puffin", "Skua", "Avocet", "Dunlin", "Grebe"]
REGIONS = ["North Atlantic", "Baltic", "Mediterranean", "West Africa", "Gulf", "South Asia", "East Asia", "Oceania"]
QUARTERS = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"]

FILLER = [
    "Management continued to focus on reliability, cost discipline and the safety of crews across the network.",
    "The {region} market remained competitive, with freight rates moving within a narrow band for most of the year.",
    "Investment decisions were reviewed by the capital committee against a hurdle rate set at the start of the period.",
    "Customer feedback collected through quarterly reviews pointed to schedule reliability as the main purchasing factor.",
    "The group kept its dividend policy unchanged and maintained headroom under all banking covenants.",
    "Port congestion eased in the second half, although berth waiting times at peak weeks were still above target.",
    "Digital tools introduced under {program} reduced manual data entry in the operations centres.",
    "Fuel efficiency gains came mainly from hull cleaning, trim optimisation and slower steaming on long routes.",
    "The board monitored progress on these measures at each scheduled meeting and requested further detail where needed.",
    "Contract renewals with the largest shippers were completed on terms broadly similar to the prior year.",
    "Training hours per seafarer increased, supported by new simulator capacity at the regional academy.",
    "Insurance costs rose modestly in line with the wider market and reflected a higher assessed value of the fleet.",
    "Maintenance windows were scheduled to avoid the busiest trading months wherever operationally possible.",
    "Working capital was managed closely, with receivable days kept within the range agreed with lenders.",
    "Regulatory changes on emissions reporting required new procedures for collecting voyage data from every vessel.",
    "Shore power connections were tested at two terminals, and results will inform a wider roll-out decision.",
    "The procurement team consolidated suppliers for spare parts, which shortened average lead times.",
    "Health and wellbeing support for crews was extended to cover families ashore through a confidential helpline.",
    "Several older vessels were placed on longer-term charters rather than sold, preserving optionality on capacity.",
    "Risk assessments were refreshed for routes affected by weather volatility and shifting security conditions.",
    "Terminal productivity, measured in moves per crane hour, improved at most sites compared with the prior period.",
    "Cybersecurity exercises were run with external specialists and covered both shipboard and shore systems.",
    "Planning assumptions for the next period include stable demand in the {region} trades and moderate cost inflation.",
    "Lessons from incidents were shared across the fleet through monthly safety bulletins and toolbox talks.",
]


def filler(rng, n):
    out = []
    for _ in range(n):
        out.append(rng.choice(FILLER).format(region=rng.choice(REGIONS), program=rng.choice(PROGRAMS)))
    return " ".join(out)


# --------------------------------------------------------------------------------------
# 1. Long annual report (~112 pages): narrative facts, footnotes, tables, spanning register
# --------------------------------------------------------------------------------------
def build_report(rng, U):
    doc = "report"
    cz = Composer(os.path.join(PDF, f"{doc}.pdf"), header="Corvane Maritime Group — Annual Report 2025",
                  footer="Corvane Maritime Group", font="Serif", size=10)
    cz.heading("Corvane Maritime Group Annual Report 2025", 0)
    cz.para("This report describes the operations, fleet, people and financial results of Corvane Maritime Group "
            "for the year ended 31 December 2025. All companies, people and figures in it are fictional.")
    chapters = ["Chair's statement", "Chief executive's review", "Our network", "Terminals", "Fleet",
                "Safety and crew welfare", "Sustainability", "People", "Regional review", "Financial review",
                "Risk management", "Governance"]
    pages_per = 10
    fact_budget = {"text": 32, "footnote": 9}
    made = {"text": 0, "footnote": 0}
    used_places = []

    def text_fact():
        kind = rng.randint(0, 5)
        place = U.pick(PLACES)
        used_places.append(place)
        if kind == 0:
            n = U.num(18000, 990000)
            yr = rng.randint(2009, 2022)
            s = (f"The terminal at {place}, which opened in {yr}, handled {n} TEU during 2025 after the "
                 f"completion of its second berth.")
            return s, (f"How many TEU did the terminal at {place} handle in 2025?", [n])
        if kind == 1:
            person = f"{rng.choice(GIVEN)} {U.pick(SURNAMES)}"
            s = (f"Operations at {place} were led during the year by {person}, who joined the group from a "
                 f"regional ferry operator and now chairs the local safety council.")
            return s, (f"Who led operations at {place} during 2025?", [person, person.split()[-1]])
        if kind == 2:
            prog = U.pick(PROGRAMS)
            n = U.num(120, 9800)
            s = (f"Under {prog}, the group installed {n} low-energy LED fittings across its warehouses at "
                 f"{place} and neighbouring sites, cutting lighting demand noticeably.")
            return s, (f"How many LED fittings were installed under {prog}?", [n])
        if kind == 3:
            n = U.num(1100, 8900)
            s = (f"The dredging campaign at {place} removed {n} cubic metres of silt from the approach channel, "
                 f"restoring the permitted draught for larger container ships.")
            return s, (f"How many cubic metres of silt did the dredging campaign at {place} remove?", [n])
        if kind == 4:
            pct = f"{rng.randint(11, 89)}.{rng.randint(1, 9)}%"
            while pct in U.used:
                pct = f"{rng.randint(11, 89)}.{rng.randint(1, 9)}%"
            U.used.add(pct)
            s = (f"Crew retention at the {place} manning office reached {pct} for the year, the strongest "
                 f"result recorded by any office in the network.")
            return s, (f"What was crew retention at the {place} manning office in 2025?", [pct])
        n = U.num(21, 640)
        s = (f"A total of {n} apprentices completed the marine engineering course run at the {place} academy, "
             f"most of whom joined the fleet within three months.")
        return s, (f"How many apprentices completed the marine engineering course at the {place} academy?", [n])

    for ci, ch in enumerate(chapters):
        if ci > 0:
            cz.new_page()
        cz.heading(f"{ci+1}. {ch}", 1)
        target = 1 + pages_per * (ci + 1) + (1 if ci >= 4 else 0)
        sub = 0
        tables_done = False
        while cz.page_no < target:
            if rng.random() < 0.22:
                sub += 1
                cz.heading(f"{ci+1}.{sub} {rng.choice(['Overview', 'Performance', 'Outlook', 'Priorities', 'Progress', 'Highlights', 'Challenges', 'Approach'])}", 2)
            if ch == "Fleet" and not tables_done and cz.page_no >= target - 6:
                tables_done = True
                fleet_register(cz, rng, U)
                continue
            if ch == "Financial review" and not tables_done and cz.page_no >= target - 7:
                tables_done = True
                finance_tables(cz, rng, U, doc)
                continue
            if ch == "Regional review" and not tables_done and cz.page_no >= target - 6:
                tables_done = True
                regional_table(cz, rng, U, doc)
                continue
            if ch in STAT_TABLES and not tables_done and cz.page_no >= target - 5:
                tables_done = True
                stat_table(cz, rng, U, doc, ch)
                continue
            r = rng.random()
            if made["text"] < fact_budget["text"] and r < 0.33:
                s, (qq, ans) = text_fact()
                body = filler(rng, rng.randint(1, 3)) + " " + s + " " + filler(rng, rng.randint(1, 3))
                p_before = cz.page_no
                cz.para(body)
                # the fact sentence may straddle a page; record the page where its answer landed
                page = _find_page(cz, ans[0], p_before)
                q(doc, page, "text", qq, ans)
                made["text"] += 1
            elif made["footnote"] < fact_budget["footnote"] and r < 0.42:
                place = U.pick(PLACES)
                n = U.num(2001, 9899)
                fn = (f"Figure for {place} restated to include {n} tonnes of transhipped cargo previously "
                      f"reported under bulk handling.")
                cz.para(filler(rng, rng.randint(3, 5)), footnote=fn)
                q(doc, cz.page_no, "footnote",
                  f"According to the footnote, how many tonnes of transhipped cargo were added in the restated figure for {place}?", [n])
                made["footnote"] += 1
            else:
                cz.para(filler(rng, rng.randint(3, 7)))
    pages = cz.save()
    save_truth(doc, pages, "report")
    return doc, len(pages)


def _find_page(cz, needle, start):
    for i in range(start - 1, len(cz.pages)):
        for b in cz.pages[i].blocks:
            if needle in b.get("text", ""):
                return i + 1
    return cz.page_no


def fleet_register(cz, rng, U):
    cz.para("The table below lists every vessel in the operated fleet at 31 December 2025, with its year of "
            "build and nominal capacity. The register continues over several pages.")
    rows = []
    names = []
    for a in VESSEL_A:
        for b in rng.sample(VESSEL_B, 3):
            names.append(f"{a} {b}")
    rng.shuffle(names)
    names = names[:58]
    for nm in names:
        imo = U.num(9100000, 9899999, "{}")
        built = rng.randint(2001, 2024)
        teu = U.num(1200, 15900)
        flag = rng.choice(["Liberia", "Malta", "Singapore", "Norway", "Panama", "Marshall Is."])
        rows.append([nm, imo, str(built), teu, flag])
    start = cz.page_no
    cz.table(["Vessel", "IMO number", "Built", "Capacity (TEU)", "Flag"], rows, [3, 2, 1.2, 2, 2],
             table_id="fleet_register", caption="Table 5.1 Operated fleet register", align_right_from=1)
    # questions on rows from every part, including the later pages
    for p in range(start - 1, len(cz.pages)):
        parts = [b for b in cz.pages[p].blocks if b.get("table_id") == "fleet_register"]
        for b in parts:
            for r in rng.sample(b["rows"], min(6, len(b["rows"]))):
                if rng.random() < 0.5:
                    q("report", p + 1, "table_span", f"What is the nominal capacity in TEU of the vessel {r[0]} in the fleet register?", [r[3]])
                else:
                    q("report", p + 1, "table_span", f"What is the IMO number of the vessel {r[0]}?", [r[1]])


STAT_TABLES = {
    "Our network": ("Table 3.1 Services by trade lane", ["Trade lane", "Weekly sailings", "Vessels deployed", "Average transit (days)"],
                    ["Asia–Europe", "Transpacific", "Intra-Asia", "Transatlantic", "Mediterranean feeder", "West Africa loop", "Gulf shuttle"]),
    "Terminals": ("Table 4.1 Terminal performance", ["Terminal", "Berths", "Crane moves per hour", "Yard capacity (TEU)"],
                  None),
    "Safety and crew welfare": ("Table 6.1 Safety statistics by fleet segment", ["Fleet segment", "Lost-time injuries", "Near-miss reports", "Drills held"],
                                ["Container", "Feeder", "Ferry", "Offshore support", "Tug and harbour", "Bulk"]),
    "Sustainability": ("Table 7.1 Emissions by fleet segment", ["Fleet segment", "CO2 (tonnes)", "SOx (tonnes)", "Fuel used (tonnes)"],
                       ["Container", "Feeder", "Ferry", "Offshore support", "Tug and harbour", "Bulk"]),
    "People": ("Table 8.1 Headcount by function", ["Function", "Sea staff", "Shore staff", "New hires"],
               ["Deck", "Engine", "Catering", "Terminal operations", "Commercial", "Technical", "Support functions"]),
}


def stat_table(cz, rng, U, doc, ch):
    caption, header, labels = STAT_TABLES[ch]
    if labels is None:
        labels = [f"{U.pick(PLACES)}" for _ in range(7)]
    cz.para(filler(rng, 3))
    rows = [[lb] + [U.num(30, 98000) for _ in header[1:]] for lb in labels]
    cz.table(header, rows, [3] + [1.7] * (len(header) - 1), table_id=caption.split()[1], caption=caption)
    p = cz.page_no
    for r in rng.sample(rows, 5):
        col = rng.randint(1, len(header) - 1)
        q(doc, p, "table", f"In {caption.split(' ', 2)[0]} {caption.split()[1]}, what is the value of '{header[col]}' for {r[0]}?", [r[col]])
    cz.para(filler(rng, 4))


def finance_tables(cz, rng, U, doc):
    cz.para(filler(rng, 3))
    lines = ["Container shipping", "Terminal services", "Logistics and warehousing", "Ship management",
             "Ferry operations", "Other revenue"]
    rows = []
    for ln in lines:
        rows.append([ln] + [U.num(1200, 98000) for _ in QUARTERS])
    cz.table(["Revenue (USD thousand)"] + QUARTERS, rows, [3.2, 1.4, 1.4, 1.4, 1.4], table_id="rev_by_line",
             caption="Table 10.1 Revenue by business line and quarter")
    p = cz.page_no
    for r in rng.sample(rows, 4):
        qi = rng.randint(1, 4)
        q(doc, p, "table", f"What was revenue from {r[0].lower()} in {QUARTERS[qi-1]}, in USD thousand?", [r[qi]])
    cz.para(filler(rng, 4))
    items = ["Fuel", "Crew costs", "Port charges", "Repairs and maintenance", "Charter hire", "Insurance",
             "Depreciation", "Administration"]
    rows = []
    for it in items:
        a, b = U.num(800, 76000), U.num(800, 76000)
        rows.append([it, a, b])
    cz.table(["Operating costs (USD thousand)", "2025", "2024"], rows, [3.5, 1.5, 1.5], table_id="opex",
             caption="Table 10.2 Operating costs")
    p = cz.page_no
    for r in rng.sample(rows, 4):
        col = rng.choice([1, 2])
        q(doc, p, "table", f"What were {r[0].lower()} operating costs in {['', '2025', '2024'][col]}, in USD thousand?", [r[col]])
    cz.para(filler(rng, 5))


def regional_table(cz, rng, U, doc):
    cz.para(filler(rng, 3))
    rows = []
    for rg in REGIONS:
        rows.append([rg, U.num(40, 990), U.num(1000, 49000), f"{rng.randint(55, 97)}.{rng.randint(0,9)}%"])
    cz.table(["Region", "Port calls", "Volume (kTEU)", "On-time rate"], rows, [3, 1.5, 1.8, 1.6],
             table_id="regions", caption="Table 9.1 Regional operating statistics")
    p = cz.page_no
    for r in rng.sample(rows, 5):
        col = rng.choice([1, 2])
        label = ["", "number of port calls", "volume in kTEU"][col]
        q(doc, p, "table", f"What was the {label} for the {r[0]} region in Table 9.1?", [r[col]])
    cz.para(filler(rng, 4))


# --------------------------------------------------------------------------------------
# 2. Multi-column technical bulletin (8 pages)
# --------------------------------------------------------------------------------------
def build_multicol(rng, U):
    doc = "bulletin"
    cz = Composer(os.path.join(PDF, f"{doc}.pdf"), header="Corvane Technical Bulletin No. 47", columns=2,
                  font="Body", size=9)
    topics = ["Ballast water treatment", "Scrubber maintenance", "Propeller polishing", "Mooring line wear",
              "Lube oil analysis", "Hull coating trials", "Boiler water chemistry", "Cargo crane inspection",
              "Shaft generator tuning", "Battery hybrid trials", "Antifouling review", "Weather routing"]
    k = 0
    while cz.page_no <= 8:
        t = topics[k % len(topics)]
        k += 1
        cz.heading(t, 2)
        for _ in range(rng.randint(2, 3)):
            if rng.random() < 0.45 and len([x for x in QUESTIONS if x["doc"] == doc]) < 10:
                vessel = f"{rng.choice(VESSEL_A)} {rng.choice(VESSEL_B)}"
                n = U.num(110, 4900)
                s = (f"During the {t.lower()} trial on {vessel}, engineers recorded {n} operating hours "
                     f"before the first scheduled inspection.")
                p0 = cz.page_no
                cz.para(filler(rng, 1) + " " + s + " " + filler(rng, 1))
                if cz.page_no <= 8:
                    q(doc, _find_page(cz, n, p0), "multicol", f"How many operating hours were recorded in the {t.lower()} trial on {vessel}?", [n])
            else:
                cz.para(filler(rng, rng.randint(2, 4)))
            if cz.page_no > 8:
                break
    pages = cz.save()
    # trim any overflow page beyond 8 (keeps truth consistent: we stop drawing after page 8)
    save_truth(doc, pages, "multicolumn")
    return doc, len(pages)


# --------------------------------------------------------------------------------------
# 3. Maths engineering note (5 pages)
# --------------------------------------------------------------------------------------
def build_maths(rng, U):
    doc = "maths"
    cz = Composer(os.path.join(PDF, f"{doc}.pdf"), header="Engineering Note EN-12: Resistance and Power", font="Serif", size=10)
    cz.heading("Engineering Note EN-12: Hull resistance, power and fuel", 1)
    eqs = [
        ("Frictional resistance", "R_F = ½ · ρ · V² · S · C_F", "C_F = 0.075 / (log₁₀ Re − 2)²"),
        ("Effective power", "P_E = R_T · V", "P_B = P_E / (η_H · η_O · η_R · η_S)"),
        ("Admiralty coefficient", "C_adm = Δ^(2/3) · V³ / P", "P₂ = P₁ · (V₂ / V₁)³"),
        ("Fuel consumption", "FC = SFOC · P_B · t / 10⁶", "CO₂ = 3.114 · FC"),
        ("Froude number", "Fn = V / √(g · L)", "Re = V · L / ν"),
    ]
    for i, (title, e1, e2) in enumerate(eqs):
        if i:
            cz.new_page()
        cz.heading(f"{i+1}. {title}", 2)
        cz.para(filler(rng, 2))
        cz.para(e1, font="Mono", size=11, indent=40)
        cz.para(filler(rng, 1))
        cz.para(e2, font="Mono", size=11, indent=40)
        n = U.num(1100, 98000)
        vessel = f"{rng.choice(VESSEL_A)} {rng.choice(VESSEL_B)}"
        cz.para(f"Worked example {i+1}: applying the relation above to {vessel} at service speed gives a result of "
                f"{n} units, which is used as the reference value for the sea trial comparison.")
        q(doc, cz.page_no, "maths", f"What result was obtained in worked example {i+1} for {vessel}?", [n])
        cz.para(filler(rng, rng.randint(6, 10)))
    pages = cz.save()
    save_truth(doc, pages, "maths")
    return doc, len(pages)


# --------------------------------------------------------------------------------------
# 4. Chinese and Vietnamese regional reports (5 pages each)
# --------------------------------------------------------------------------------------
ZH_CITIES = ["上海", "宁波", "青岛", "厦门", "天津", "大连", "广州", "深圳", "福州", "连云港"]
ZH_FILL = [
    "本年度区域团队继续专注于安全、效率和客户服务。",
    "港口拥堵情况在下半年有所缓解，但高峰周的等泊时间仍高于目标。",
    "公司对船舶维修计划进行了优化，尽量避开运输旺季。",
    "数字化工具减少了操作中心的人工录入工作量。",
    "燃油效率的提升主要来自船体清洁和航速优化。",
    "管理层定期审查各项措施的进展，并在需要时要求提供更多细节。",
    "培训时长有所增加，新增的模拟器设备为船员提供了更多实践机会。",
    "保险费用随市场温和上涨，反映了船队资产价值的提高。",
    "排放报告的新规要求每艘船舶建立新的航次数据收集流程。",
    "与主要客户的合同续签条款与上一年度大致相同。",
    "网络安全演练覆盖了船舶和岸基系统。",
    "区域办公室加强了与当地港务部门的沟通与合作。",
]
VI_CITIES = ["Hải Phòng", "Đà Nẵng", "Quy Nhơn", "Vũng Tàu", "Cần Thơ", "Nha Trang", "Cái Mép", "Hạ Long", "Huế", "Thị Vải"]
VI_FILL = [
    "Trong năm qua, đội ngũ khu vực tiếp tục tập trung vào an toàn, hiệu quả và chất lượng dịch vụ khách hàng.",
    "Tình trạng ùn tắc tại cảng đã giảm trong nửa cuối năm, nhưng thời gian chờ cầu bến vào tuần cao điểm vẫn cao hơn mục tiêu.",
    "Kế hoạch bảo dưỡng tàu được sắp xếp để tránh các tháng vận chuyển cao điểm.",
    "Các công cụ số đã giúp giảm khối lượng nhập liệu thủ công tại trung tâm điều hành.",
    "Hiệu quả nhiên liệu được cải thiện chủ yếu nhờ vệ sinh thân tàu và tối ưu tốc độ hành trình.",
    "Ban lãnh đạo định kỳ xem xét tiến độ của các biện pháp này và yêu cầu bổ sung thông tin khi cần.",
    "Số giờ đào tạo cho thuyền viên tăng lên nhờ hệ thống mô phỏng mới tại học viện khu vực.",
    "Chi phí bảo hiểm tăng nhẹ theo xu hướng chung của thị trường.",
    "Quy định mới về báo cáo phát thải yêu cầu quy trình thu thập dữ liệu hành trình từ mỗi tàu.",
    "Các hợp đồng với khách hàng lớn được gia hạn với điều khoản tương tự năm trước.",
    "Các cuộc diễn tập an ninh mạng đã bao gồm cả hệ thống trên tàu và trên bờ.",
    "Văn phòng khu vực tăng cường phối hợp với chính quyền cảng địa phương.",
]


def build_zh(rng, U):
    doc = "zh_report"
    cz = Composer(os.path.join(PDF, f"{doc}.pdf"), header="科凡海运集团 华东区域年度报告 2025", font="CJK", size=10.5, cjk=True)
    cz.heading("科凡海运集团 华东区域年度报告（2025年）", 1)
    cities = rng.sample(ZH_CITIES, 8)
    for i, city in enumerate(cities):
        if i and i % 2 == 0:
            cz.new_page()
        cz.heading(f"{i+1}. {city}办事处", 2)
        cz.para("".join(rng.sample(ZH_FILL, 4)))
        n = U.num(120, 980, "{}")
        if i % 2 == 0:
            cz.para(f"截至2025年底，{city}办事处共有员工{n}人，比上一年有所增加。" + "".join(rng.sample(ZH_FILL, 3)))
            q(doc, cz.page_no, "cjk", f"截至2025年底，{city}办事处共有多少名员工？", [n], lang="zh")
        else:
            cz.para(f"2025年，{city}码头共完成船舶靠泊{n}艘次，创历史新高。" + "".join(rng.sample(ZH_FILL, 3)))
            q(doc, cz.page_no, "cjk", f"2025年{city}码头共完成多少艘次船舶靠泊？", [n], lang="zh")
        cz.para("".join(rng.sample(ZH_FILL, 5)))
    rows = [[c, U.num(1000, 9800, "{}"), f"{rng.randint(60, 99)}%"] for c in cities[:6]]
    cz.table(["城市", "集装箱量（千标箱）", "准班率"], rows, [2, 2, 1.5], table_id="zh_table", caption="表1 各港口运营数据")
    for r in rng.sample(rows, 2):
        q(doc, cz.page_no, "cjk_table", f"根据表1，{r[0]}的集装箱量是多少千标箱？", [r[1]], lang="zh")
    pages = cz.save()
    save_truth(doc, pages, "chinese")
    return doc, len(pages)


def build_vi(rng, U):
    doc = "vi_report"
    cz = Composer(os.path.join(PDF, f"{doc}.pdf"), header="Tập đoàn Hàng hải Corvane — Báo cáo khu vực Việt Nam 2025", font="Body", size=10)
    cz.heading("Báo cáo hoạt động khu vực Việt Nam năm 2025", 1)
    cities = rng.sample(VI_CITIES, 8)
    for i, city in enumerate(cities):
        if i and i % 2 == 0:
            cz.new_page()
        cz.heading(f"{i+1}. Văn phòng {city}", 2)
        cz.para(" ".join(rng.sample(VI_FILL, 3)))
        n = U.num(120, 980, "{}")
        if i % 2 == 0:
            cz.para(f"Tính đến cuối năm 2025, văn phòng {city} có tổng cộng {n} nhân viên. " + " ".join(rng.sample(VI_FILL, 2)))
            q(doc, cz.page_no, "vi", f"Tính đến cuối năm 2025, văn phòng {city} có bao nhiêu nhân viên?", [n], lang="vi")
        else:
            cz.para(f"Trong năm 2025, cảng {city} đã tiếp nhận {n} lượt tàu cập cảng, mức cao nhất từ trước đến nay. " + " ".join(rng.sample(VI_FILL, 2)))
            q(doc, cz.page_no, "vi", f"Trong năm 2025, cảng {city} đã tiếp nhận bao nhiêu lượt tàu?", [n], lang="vi")
        cz.para(" ".join(rng.sample(VI_FILL, 4)))
    rows = [[c, U.num(1000, 9800, "{}"), f"{rng.randint(60, 99)}%"] for c in cities[:6]]
    cz.table(["Cảng", "Sản lượng (nghìn TEU)", "Tỷ lệ đúng giờ"], rows, [2, 2, 1.6], table_id="vi_table", caption="Bảng 1. Số liệu khai thác theo cảng")
    for r in rng.sample(rows, 2):
        q(doc, cz.page_no, "vi_table", f"Theo Bảng 1, sản lượng của cảng {r[0]} là bao nhiêu nghìn TEU?", [r[1]], lang="vi")
    pages = cz.save()
    save_truth(doc, pages, "vietnamese")
    return doc, len(pages)


# --------------------------------------------------------------------------------------
# 5. Filled forms with checkboxes; some filled in simulated handwriting
# --------------------------------------------------------------------------------------
FORM_FIELDS = ["Claimant name", "Rank", "Vessel", "Date of incident", "Port of treatment", "Amount claimed (USD)",
               "Treating clinic", "Days off duty"]
FORM_BOXES = ["Hospitalisation", "Outpatient", "Dental", "Optical", "Physiotherapy", "Repatriation"]


def draw_form(c, rng, U, doc, page_no, ref, hand=None):
    from reportlab.lib.pagesizes import A4
    W, H = A4
    blocks, fields, boxes = [], [], []
    c.setFont("Body-Bold", 15)
    c.drawString(50, H - 60, "Corvane Crew Welfare Fund — Medical Claim Form")
    blocks.append({"type": "heading", "level": 1, "text": "Corvane Crew Welfare Fund — Medical Claim Form"})
    c.setFont("Body", 10)
    c.drawString(50, H - 82, f"Claim reference: {ref}")
    blocks.append({"type": "para", "text": f"Claim reference: {ref}"})
    c.setFont("Body", 8.5)
    intro = "Complete all sections. Tick every treatment type that applies. Attach receipts for amounts over USD 200."
    c.drawString(50, H - 100, intro)
    blocks.append({"type": "para", "text": intro})
    c.setFont("Body-Bold", 11)
    c.drawString(50, H - 130, "Section A — Claimant details")
    blocks.append({"type": "heading", "level": 2, "text": "Section A — Claimant details"})
    vals = {
        "Claimant name": f"{rng.choice(GIVEN)} {rng.choice(SURNAMES)}",
        "Rank": rng.choice(["Second Officer", "Chief Engineer", "Able Seaman", "Bosun", "Cook", "Third Engineer", "Electro-Technical Officer"]),
        "Vessel": f"{rng.choice(VESSEL_A)} {rng.choice(VESSEL_B)}",
        "Date of incident": f"{rng.randint(1, 28):02d}/{rng.randint(1, 12):02d}/2025",
        "Port of treatment": rng.choice(PLACES),
        "Amount claimed (USD)": U.num(210, 18900),
        "Treating clinic": f"{rng.choice(['St', 'Harbour', 'Seaview', 'Mariners', 'Bayside'])} {rng.choice(['Clinic', 'Medical Centre', 'Hospital'])}",
        "Days off duty": U.num(2, 89, "{}") if rng.random() < 0.5 else str(rng.randint(2, 30)),
    }
    y = H - 158
    for k in FORM_FIELDS:
        c.setFont("Body", 9.5)
        c.drawString(50, y, k + ":")
        c.setLineWidth(0.4)
        c.line(190, y - 3, 520, y - 3)
        v = vals[k]
        if hand:
            c.saveState()
            c.translate(196 + rng.uniform(-2, 6), y + rng.uniform(-1, 2))
            c.rotate(rng.uniform(-2.5, 2.5))
            c.setFont(hand, 14 if hand == "Hand2" else 12)
            c.setFillColorRGB(0.05, 0.1, 0.45)
            c.drawString(0, 0, v)
            c.restoreState()
        else:
            c.setFont("Mono", 10)
            c.drawString(196, y, v)
        fields.append({"label": k, "value": v})
        blocks.append({"type": "field", "label": k, "text": f"{k}: {v}"})
        y -= 30
    y -= 10
    c.setFont("Body-Bold", 11)
    c.drawString(50, y, "Section B — Treatment type")
    blocks.append({"type": "heading", "level": 2, "text": "Section B — Treatment type"})
    y -= 26
    ticked = set(rng.sample(FORM_BOXES, rng.randint(1, 3)))
    for i, b in enumerate(FORM_BOXES):
        x = 60 + (i % 3) * 165
        yy = y - (i // 3) * 26
        c.setLineWidth(0.8)
        c.rect(x, yy - 2, 11, 11)
        if b in ticked:
            c.setLineWidth(1.6)
            if hand:
                c.setStrokeColorRGB(0.05, 0.1, 0.45)
                c.line(x + 1, yy + 4, x + 4.5, yy - 1)
                c.line(x + 4.5, yy - 1, x + 13, yy + 11)
                c.setStrokeColorRGB(0, 0, 0)
            else:
                c.line(x + 2, yy, x + 9, yy + 7)
                c.line(x + 2, yy + 7, x + 9, yy)
        c.setFont("Body", 9.5)
        c.drawString(x + 17, yy, b)
        boxes.append({"label": b, "checked": b in ticked})
        blocks.append({"type": "checkbox", "label": b, "checked": b in ticked, "text": b})
    y -= 70
    c.setFont("Body-Bold", 11)
    c.drawString(50, y, "Section C — Declaration")
    blocks.append({"type": "heading", "level": 2, "text": "Section C — Declaration"})
    decl = ("I declare that the information given is true and complete, and I authorise the Fund to contact the "
            "treating clinic to verify this claim.")
    c.setFont("Body", 8.5)
    yy = y - 18
    for ln in wrap(decl, "Body", 8.5, 470):
        c.drawString(50, yy, ln)
        yy -= 12
    blocks.append({"type": "para", "text": decl})
    c.setFont("Body", 9.5)
    c.drawString(50, yy - 30, "Signature:")
    c.line(110, yy - 33, 300, yy - 33)
    c.drawString(320, yy - 30, "Date:")
    c.line(352, yy - 33, 450, yy - 33)
    if hand:
        c.saveState()
        c.setFont(hand, 16)
        c.setFillColorRGB(0.05, 0.1, 0.45)
        c.drawString(120, yy - 30, vals["Claimant name"].split()[-1])
        c.restoreState()
    foot = f"CWF-MC v3 · Page {page_no}"
    c.setFont("Body", 7)
    c.drawRightString(W - 50, 30, foot)
    # questions
    q(doc, page_no, "form", f"What amount in USD was claimed on claim {ref}?", [vals["Amount claimed (USD)"]])
    q(doc, page_no, "form", f"Which vessel is named on claim {ref}?", [vals["Vessel"]])
    if rng.random() < 0.6:
        q(doc, page_no, "form", f"Who is the claimant on claim {ref}?", [vals["Claimant name"], vals["Claimant name"].split()[-1]])
    b = rng.choice(FORM_BOXES)
    q(doc, page_no, "checkbox", f"On claim {ref}, is the '{b}' treatment type ticked? Answer yes or no.",
      ["yes" if b in ticked else "no"], evidence=b)
    c.showPage()
    return {"blocks": blocks, "furniture": [foot], "fields": fields, "checkboxes": boxes}


def build_forms(rng, U, doc="forms", n_typed=10, n_hand=6, refs=None):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    register_fonts()
    c = canvas.Canvas(os.path.join(PDF, f"{doc}.pdf"), pagesize=A4)
    pages = []
    for i in range(n_typed + n_hand):
        ref = f"CW-{U.num(10000, 99999, '{}')}"
        hand = None if i < n_typed else ("Hand1" if i % 2 else "Hand2")
        pages.append(draw_form(c, rng, U, doc, i + 1, ref, hand))
    c.save()
    save_truth(doc, pages, "forms", {"handwritten_pages": list(range(n_typed + 1, n_typed + n_hand + 1))})
    return doc, len(pages)


# --------------------------------------------------------------------------------------
# 6. Twin set: 15 pages made born-digital, then degraded into 4 scan variants
# --------------------------------------------------------------------------------------
def build_twins(rng, U):
    """Memo pages, price-list tables and forms. The same 15 pages are later rendered and degraded."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    doc = "twin_clean"
    path = os.path.join(PDF, f"{doc}.pdf")
    cz = Composer(path, header="Corvane Ship Supply — internal circular", font="Body", size=10.5)
    pages_meta = []
    # 5 memo pages
    for i in range(8):
        if i:
            cz.new_page()
        num = U.num(100, 999, "{}")
        cz.heading(f"Circular SS-{num}: {rng.choice(['Stores ordering', 'Bunker sampling', 'Port clearance', 'Crew change', 'Waste handling'])}", 1)
        place = U.pick(PLACES)
        n = U.num(1000, 9900)
        person = f"{rng.choice(GIVEN)} {U.pick(SURNAMES)}"
        cz.para(filler(rng, 3))
        cz.para(f"From 1 March 2026, all requests for the {place} depot must be approved by {person}. "
                f"The depot currently holds {n} stock lines, and orders above the monthly limit need a second signature.")
        q("twin", cz.page_no, "scan_text", f"Who must approve requests for the {place} depot from 1 March 2026?", [person, person.split()[-1]])
        q("twin", cz.page_no, "scan_text", f"How many stock lines does the {place} depot hold according to circular SS-{num}?", [n])
        cz.para(filler(rng, 6))
    # 5 price-list pages
    items = ["Mooring rope 64mm", "Hydraulic oil ISO 46", "Fire hose 25m", "Lifejacket SOLAS", "Paint, antifouling 20L",
             "Gasket set DN150", "Welding rods 3.2mm", "Filter element 10µm", "Chain shackle 32mm", "Bilge pump seal kit",
             "Hatch cover rubber", "Galley gas regulator", "Navigation lamp LED", "Oil spill kit", "Thermal suit",
             "Air compressor valve", "Rescue line 30m", "Pilot ladder 9m", "Fuel sampling bottle", "Grease cartridge"]
    for i in range(6):
        cz.new_page()
        pl = U.num(10, 99, "{}")
        cz.heading(f"Price list PL-{pl}", 1)
        cz.para("Prices are per unit, in US dollars, for delivery to any group vessel in port.")
        rows = []
        for it in rng.sample(items, 9):
            code = f"{rng.choice('ABCDEFGHJK')}{U.num(1000, 9999, '{}')}"
            rows.append([it, code, f"{U.num(12, 9800)}.{rng.randint(0, 99):02d}", str(rng.randint(1, 40))])
        cz.table(["Item", "Code", "Unit price (USD)", "Lead time (days)"], rows, [3.4, 1.4, 1.8, 1.6], table_id=f"pl{pl}", size=9.5)
        for r in rng.sample(rows, 3):
            q("twin", cz.page_no, "scan_table", f"What is the unit price in USD of item code {r[1]} on price list PL-{pl}?", [r[2]])
        cz.para(filler(rng, 3))
    pages = cz.save()
    # 5 form pages, appended as a second PDF then merged
    fdoc = "twin_forms_tmp"
    c = canvas.Canvas(os.path.join(PDF, f"{fdoc}.pdf"), pagesize=A4)
    fpages = []
    start_qs = len(QUESTIONS)
    for i in range(6):
        ref = f"CW-{U.num(10000, 99999, '{}')}"
        fpages.append(draw_form(c, rng, U, "twin", len(pages) + 1 + i, ref, hand=("Hand1" if i >= 4 else None)))
    c.save()
    import pymupdf
    a = pymupdf.open(path)
    b = pymupdf.open(os.path.join(PDF, f"{fdoc}.pdf"))
    a.insert_pdf(b)
    a.save(path + ".tmp")
    a.close()
    os.replace(path + ".tmp", path)
    os.remove(os.path.join(PDF, f"{fdoc}.pdf"))
    allp = pages + fpages
    save_truth(doc, allp, "twin_clean")
    return doc, len(allp)


def degrade_twins(rng):
    """Render twin pages to images and degrade them four ways; image-only PDFs (no text layer)."""
    import io

    import cv2
    import numpy as np
    import pymupdf
    from PIL import Image, ImageFilter

    src = pymupdf.open(os.path.join(PDF, "twin_clean.pdf"))
    truth = json.load(open(os.path.join(TRUTH, "twin_clean.json")))
    out = []
    for kind in ["skew", "blur", "jpeg", "photo"]:
        dst = pymupdf.open()
        r = random.Random(f"{SEED}-{kind}")
        for page in src:
            dpi = 200 if kind in ("skew", "blur") else 150
            pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY if kind != "photo" else pymupdf.csRGB)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            if kind == "skew":
                ang = r.choice([-1, 1]) * r.uniform(1.5, 3.5)
                img = img.rotate(ang, resample=Image.BICUBIC, expand=False, fillcolor=255)
                a = np.array(img).astype(np.int16)
                a = np.clip(a + np.random.default_rng(r.randint(0, 9999)).normal(0, 8, a.shape), 0, 255).astype(np.uint8)
                img = Image.fromarray(a)
                buf = io.BytesIO(); img.save(buf, "PNG")
            elif kind == "blur":
                img = img.filter(ImageFilter.GaussianBlur(radius=r.uniform(1.4, 1.9)))
                buf = io.BytesIO(); img.save(buf, "PNG")
            elif kind == "jpeg":
                img = img.resize((int(img.width * 0.75), int(img.height * 0.75)), Image.BILINEAR)
                buf = io.BytesIO(); img.save(buf, "JPEG", quality=r.randint(12, 18))
            else:  # photo: perspective warp, uneven light, warm tint, slight blur, jpeg
                a = np.array(img).astype(np.float32)
                h, w = a.shape[:2]
                d = lambda: r.uniform(0.02, 0.06)
                srcp = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
                dstp = np.float32([[w * d(), h * d()], [w * (1 - d()), h * d() * 0.5], [w * (1 - d() * 0.5), h * (1 - d())], [w * d() * 0.6, h * (1 - d() * 0.4)]])
                M = cv2.getPerspectiveTransform(srcp, dstp)
                a = cv2.warpPerspective(a, M, (w, h), borderValue=(70, 60, 50))
                yy, xx = np.mgrid[0:h, 0:w]
                light = 0.72 + 0.32 * (1 - ((xx - w * 0.3) ** 2 + (yy - h * 0.25) ** 2) / (w ** 2 + h ** 2) * 1.6)
                a = a * light[..., None] * np.array([1.0, 0.96, 0.86])
                a = cv2.GaussianBlur(np.clip(a, 0, 255), (3, 3), 0.9)
                img = Image.fromarray(a.astype(np.uint8))
                buf = io.BytesIO(); img.save(buf, "JPEG", quality=60)
            p = dst.new_page(width=page.rect.width, height=page.rect.height)
            p.insert_image(p.rect, stream=buf.getvalue())
        name = f"scan_{kind}"
        dst.save(os.path.join(PDF, f"{name}.pdf"), deflate=True)
        t = dict(truth)
        t["doc"], t["category"], t["degradation"] = name, "scan", kind
        json.dump(t, open(os.path.join(TRUTH, f"{name}.json"), "w"), ensure_ascii=False, indent=1)
        out.append((name, len(src)))
    return out


# --------------------------------------------------------------------------------------
def main():
    import pymupdf

    os.makedirs(PDF, exist_ok=True)
    rng = random.Random(SEED)
    U = Unique(rng)
    docs = []
    docs.append(build_report(rng, U))
    docs.append(build_multicol(rng, U))
    docs.append(build_maths(rng, U))
    docs.append(build_zh(rng, U))
    docs.append(build_vi(rng, U))
    docs.append(build_forms(rng, U))
    docs.append(build_twins(rng, U))
    docs.extend(degrade_twins(rng))

    # drop questions whose page landed beyond a trimmed document
    counts = {d: n for d, n in docs}
    for d, n in docs:
        real = pymupdf.open(os.path.join(PDF, f"{d}.pdf")).page_count
        assert real == n, (d, real, n)

    for qq in QUESTIONS:
        if qq["doc"] == "twin" and not qq["kind"].startswith("scan_"):
            qq["kind"] = "scan_" + qq["kind"]
    with open(os.path.join(OUT, "questions.jsonl"), "w") as f:
        for qq in QUESTIONS:
            f.write(json.dumps(qq, ensure_ascii=False) + "\n")

    # pilot: ~21 pages spread over every category
    rep = json.load(open(os.path.join(TRUTH, "report.json")))["pages"]
    def first(pred):
        return next(i + 1 for i, pg in enumerate(rep) if any(pred(b) for b in pg["blocks"]))
    fleet = first(lambda b: b.get("table_id") == "fleet_register")
    text_pg = next(x["page"] for x in QUESTIONS if x["doc"] == "report" and x["kind"] == "text")
    fn_pg = next(x["page"] for x in QUESTIONS if x["doc"] == "report" and x["kind"] == "footnote")
    fin_pg = first(lambda b: b.get("table_id") == "rev_by_line")
    twin_tab = next(x["page"] for x in QUESTIONS if x["kind"] == "scan_table")
    twin_form = next(x["page"] for x in QUESTIONS if x["kind"] == "scan_form")
    pilot = {
        "report": sorted({text_pg, fn_pg, fleet, fleet + 1, fin_pg}),
        "bulletin": [2],
        "maths": [2],
        "zh_report": [2],
        "vi_report": [2],
        "forms": [3, 14],
        "twin_clean": [twin_tab, twin_form],
        "scan_skew": [twin_tab, twin_form], "scan_blur": [twin_tab, twin_form],
        "scan_jpeg": [twin_tab, twin_form], "scan_photo": [twin_tab, twin_form],
    }
    manifest = {"seed": SEED, "documents": [{"doc": d, "pages": n, "pdf": f"pdf/{d}.pdf",
                                             "category": json.load(open(os.path.join(TRUTH, f"{d}.json")))["category"]}
                                            for d, n in docs],
                "total_pages": sum(n for _, n in docs), "questions": len(QUESTIONS), "pilot": pilot}
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    from collections import Counter
    print("pages", manifest["total_pages"], {d: n for d, n in docs})
    print("questions", len(QUESTIONS), Counter(x["kind"] for x in QUESTIONS))


if __name__ == "__main__":
    main()

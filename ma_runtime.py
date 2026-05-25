#!/usr/bin/env python3
"""MA Runtime v3 — Observer + benchmark拡張 + memory decay + policy-engine + retry-engine

v2からの追加:
  Observer     : 全ステップを監査ログ(memory/ciie/sessions/)に記録
  benchmark+   : confidence/freshness/source_count/diversity を追加
  memory decay : confidence = 1.0 × e^(-λ×hours) — financialはλ高め
  policy-engine: FAIL typeを診断して再試行戦略を決定
  retry-engine : policy-engineの指示でリトライ実行（最大2回）

Usage:
    python3 ma_runtime.py 'USDJPYのトレンドを調査して'
    python3 ma_runtime.py --list
"""

import json, uuid, datetime, subprocess, os, sys, math, re, urllib.request
from pathlib import Path

ROOT       = Path(__file__).parent
TASKS_DIR  = ROOT / "tasks"
MEMORY_NOW = ROOT / "memory" / "now.md"
TASKS_DIR.mkdir(exist_ok=True)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")


# ── PERSONAS — 人格定義（シェル非依存） ──────────────────────────────────────

PERSONAS: dict[str, str] = {
    "researcher": (
        "You are the Researcher agent for MA System. "
        "Search broadly. Output findings with sources (URLs or paper names). "
        "Focus on facts with dates and numbers. Respond in Japanese."
    ),
    "supervisor": (
        "You are the Supervisor agent for MA System. "
        "You receive multiple agent outputs and reconcile contradictions. "
        "Identify the delta between old known state and new information. "
        "Produce a single coherent, fact-based synthesis. Respond in Japanese."
    ),
    "critic": (
        "You are the Critic agent for MA System. "
        "Challenge assumptions. Find risks, counterarguments, and edge cases. "
        "Present the devil's advocate perspective. Respond in Japanese."
    ),
    "analyst": (
        "You are the Data Analyst agent for MA System. "
        "Extract numbers, trends, anomalies. "
        "Always cite sample size and comparison basis. Respond in Japanese."
    ),
    "lawyer": (
        "You are the Legal Advisor agent for MA System. "
        "When legal matters appear in the output, you MUST flag applicable laws and risks. "
        "Cover: 労働法・契約法・税法・規制・許認可・著作権・個人情報保護法(APPI). "
        "Format: ⚖️ 適用法令 / ⚠️ リスク / ✅ 推奨アクション の3点セット. "
        "Never give final legal advice — always recommend professional confirmation. "
        "Respond in Japanese."
    ),
}

# ── 法的インターロック — DO WAIT シグナル ────────────────────────────────────

LEGAL_WARN_TRIGGERS: list[str] = [
    "契約", "労働", "規制", "法律", "許可", "ライセンス",
    "特許", "著作権", "税", "確定申告", "雇用", "残業", "有給",
    "個人情報", "プライバシー", "就業規則", "退職",
]

LEGAL_LATCH_TRIGGERS: list[str] = [
    "解雇通知", "即時解雇", "訴訟", "賠償", "違反", "罰則",
    "ハラスメント", "discrimination", "個人情報漏洩", "違法",
    "今すぐ送って", "今すぐ実行", "gdpr違反", "appi違反",
]

LEGAL_SEVERITY_LOW  = "LOW"
LEGAL_SEVERITY_HIGH = "HIGH"

# ── FINANCIAL GOAL DETECTION ─────────────────────────────────────────────────

FINANCIAL_KEYWORDS: list[str] = [
    "usdjpy", "usd", "yen", "為替", "fx", "株", "btc", "仮想通貨",
    "価格", "相場", "金利", "利率", "金融", "投資", "運用",
]

def is_financial_goal(goal: str) -> bool:
    return any(kw in goal.lower() for kw in FINANCIAL_KEYWORDS)


# ── OBSERVER — 監査ログ ───────────────────────────────────────────────────────

SESSION_LOG_DIR = ROOT / "memory" / "ciie" / "sessions"
SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)


class Observer:
    """全ステップをセッション単位で記録し、memory/ciie/sessions/ に保存する"""

    def __init__(self, goal: str):
        self.session: dict = {
            "session_id":       f"sess-{uuid.uuid4().hex[:6]}",
            "goal":             goal,
            "started_at":       datetime.datetime.now().isoformat(),
            "steps":            [],
            "total_cost_usd":   0.0,
            "policy_engine":    {"fail_type": None, "retry_count": 0},
            "final_status":     None,
            "total_duration_sec": 0.0,
        }
        self._start = datetime.datetime.now()

    def record(self, step: str, **kwargs) -> None:
        self.session["steps"].append({
            "step": step,
            "ts":   datetime.datetime.now().isoformat(),
            **kwargs,
        })

    def set_policy(self, fail_type: str | None, retry_count: int) -> None:
        self.session["policy_engine"]["fail_type"]   = fail_type
        self.session["policy_engine"]["retry_count"] = retry_count

    def finish(self, status: str) -> None:
        self.session["final_status"]       = status
        elapsed = (datetime.datetime.now() - self._start).total_seconds()
        self.session["total_duration_sec"] = round(elapsed, 1)

    def save(self) -> Path:
        ts   = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        sid  = self.session["session_id"]
        path = SESSION_LOG_DIR / f"{ts}_{sid}.json"
        path.write_text(json.dumps(self.session, ensure_ascii=False, indent=2))
        return path


# ── MEMORY CONFIDENCE DECAY ──────────────────────────────────────────────────

DECAY_LAMBDA: dict[str, float] = {
    "financial": 0.15,  # 金融情報は速く陳腐化
    "general":   0.05,  # 一般情報はゆっくり陳腐化
}


def memory_confidence(last_updated_iso: str, domain: str = "general") -> float:
    """信頼度 = e^(-λ × elapsed_hours) — 0〜1"""
    try:
        dt    = datetime.datetime.fromisoformat(last_updated_iso)
        hours = (datetime.datetime.now() - dt).total_seconds() / 3600
        lam   = DECAY_LAMBDA.get(domain, DECAY_LAMBDA["general"])
        return round(math.exp(-lam * hours), 3)
    except Exception:
        return 0.5


def read_internal_state(domain: str = "general") -> tuple[str, float]:
    """内側既知状態（memory/now.md）を読み、confidence decayも計算して返す"""
    if not MEMORY_NOW.exists():
        return "(内側既知状態なし)", 0.0
    text    = MEMORY_NOW.read_text()
    snippet = text[-500:] if len(text) > 500 else text

    dates = re.findall(r'## (\d{4}-\d{2}-\d{2}T\d{2}:\d{2})', text)
    if dates:
        conf = memory_confidence(dates[-1] + ":00", domain)
    else:
        conf = 0.5
    return snippet, conf


# ── GOAL → PERSONA マッピング ────────────────────────────────────────────────

GOAL_KEYWORDS: dict[str, list[str]] = {
    "researcher": ["調査", "search", "research", "論文", "arxiv", "調べ", "探", "find",
                   "usdjpy", "yen", "usd", "価格", "トレンド"],
    "analyst":    ["分析", "kpi", "ga4", "データ", "analyze", "数値", "stats"],
    "supervisor": ["整合", "並列", "全体", "俯瞰", "まとめ", "統合"],
    "critic":     ["批判", "リスク", "問題", "懸念", "最悪", "デメリット", "チェック", "矛盾"],
}

def route_persona(goal: str) -> str:
    g = goal.lower()
    for persona, keywords in GOAL_KEYWORDS.items():
        if any(kw in g for kw in keywords):
            return persona
    return "researcher"


# ── C接点 シェル ─────────────────────────────────────────────────────────────

class EMOOpen(Exception):
    pass


def _call_openrouter(persona_key: str, prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    body = json.dumps({
        "model": "openai/gpt-4o",
        "messages": [
            {"role": "system", "content": PERSONAS[persona_key]},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens": 1200,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type":  "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def _call_gemini(persona_key: str, prompt: str) -> str:
    full_prompt = f"{PERSONAS[persona_key]}\n\nTask: {prompt}"
    r = subprocess.run(
        ["gemini", "-y", "-p", full_prompt],
        capture_output=True, text=True, timeout=180,
    )
    out = r.stdout.strip()
    return out if out else (r.stderr.strip() or "エラー: 出力なし")


def run_with_c_contact(
    persona_key: str, goal: str, log_fn=None
) -> tuple[str, str]:
    """C接点: OpenRouter(A接点) 失敗時 → Gemini CLI(B接点) に自動切替"""
    try:
        out = _call_openrouter(persona_key, goal)
        if len(out.strip()) >= 10:
            if log_fn: log_fn(f"   [{persona_key}] A接点(OpenRouter) ✅")
            return out, "openrouter"
    except Exception as e:
        if log_fn: log_fn(f"   [{persona_key}] A接点失敗 → C接点切替 ({e.__class__.__name__})")

    out = _call_gemini(persona_key, goal)
    if len(out.strip()) >= 10:
        if log_fn: log_fn(f"   [{persona_key}] B接点(Gemini CLI) ✅")
        return out, "gemini"

    raise EMOOpen(persona_key)


# ── カスケード制御 ────────────────────────────────────────────────────────────

def cascade_reconcile(
    external_outputs: dict[str, str],
    internal_state: str,
    goal: str,
    log_fn=None,
) -> str:
    """外側情報 vs 内側既知 → 差分を特定 → supervisor整合出力"""
    external_text = "\n\n".join(
        f"[{role}の出力]\n{out}" for role, out in external_outputs.items()
    )
    prompt = (
        f"目標: {goal}\n\n"
        f"=== 外側エージェントの出力 ===\n{external_text}\n\n"
        f"=== 内側の既知状態（memory） ===\n{internal_state}\n\n"
        "差分を特定し、新しく判明したことを明示したうえで、"
        "整合の取れた最終アウトプットを出してください。"
    )
    if log_fn: log_fn("   [cascade] supervisor整合中...")
    out, _ = run_with_c_contact("supervisor", prompt, log_fn)
    return out


# ── 法的インターロック ────────────────────────────────────────────────────────

def legal_interlock(
    goal: str, cascade_output: str, log_fn=None
) -> tuple[str, str]:
    """2段階法的インターロック: LOW=ワーニング発泡・継続 / HIGH=重故障ラッチ停止"""
    text = (goal + " " + cascade_output).lower()

    high_hits = [t for t in LEGAL_LATCH_TRIGGERS if t in text]
    if high_hits:
        if log_fn: log_fn(f"   🔴 重故障ラッチ: {high_hits[:3]} — EXECUTE停止")
        prompt = (
            f"以下は重大な法的リスクを含む可能性があります。\n\n"
            f"目標: {goal}\n検出: {high_hits}\n\n"
            f"アウトプット:\n{cascade_output}\n\n"
            "法令違反リスク・即時停止推奨理由・解除条件を出してください。"
        )
        try:
            out, _ = run_with_c_contact("lawyer", prompt, log_fn)
        except EMOOpen:
            out = f"🔴 重大法的リスク: {high_hits} — 専門家確認なしに実行禁止"
        return LEGAL_SEVERITY_HIGH, out

    low_hits = [t for t in LEGAL_WARN_TRIGGERS if t in text]
    if low_hits:
        if log_fn: log_fn(f"   🟡 DO WAIT ワーニング: {low_hits[:3]}...")
        prompt = (
            f"以下のアウトプットに法的知見が必要な箇所があります。\n\n"
            f"目標: {goal}\n検出: {low_hits}\n\n"
            f"アウトプット:\n{cascade_output}\n\n"
            "適用法令・リスク・推奨アクションを3点セットで出してください。"
        )
        try:
            out, _ = run_with_c_contact("lawyer", prompt, log_fn)
        except EMOOpen:
            out = f"⚠️ 法的キーワード検出: {low_hits} — 専門家確認を推奨"
        return LEGAL_SEVERITY_LOW, out

    return "NONE", ""


# ── JUDGE (拡張版) ────────────────────────────────────────────────────────────

def judge_extended(
    goal: str, output: str, financial: bool = False
) -> tuple[float, bool, str, dict]:
    """拡張Judge — source多様性・freshness・confidence_dataを追加

    Returns:
        (score, passed, reason_str, details_dict)
    """
    checks:  dict[str, bool] = {}
    details: dict[str, object] = {}

    # 基本4チェック
    checks["not_empty"] = len(output.strip()) >= 10

    source_markers = ["http", "arxiv", "github", "%", "万", "$", "円", "論文",
                      "report", "data", "source", "ref", "出典", "によると"]
    found_src = [m for m in source_markers if m in output.lower()]
    checks["has_source"]   = len(found_src) >= 1
    details["source_count"] = len(found_src)

    goal_words = [w for w in goal.replace("して", "").replace("を", " ").split() if len(w) > 1]
    hit = sum(1 for w in goal_words if w in output)
    checks["goal_satisfied"] = hit >= max(1, len(goal_words) // 2)

    bad = ["間違えました", "申し訳ありませんが、先ほどの回答は誤り", "逆のことを言いました"]
    checks["no_contradiction"] = not any(m in output for m in bad)

    # 拡張3チェック
    urls    = re.findall(r'https?://[^\s/]+', output)
    domains = {re.sub(r'^https?://', '', u).split('/')[0] for u in urls}
    details["source_diversity"] = len(domains)
    checks["source_diverse"] = len(domains) >= 2 or not financial

    has_date = bool(re.search(r'20\d\d[-/年]', output))
    details["has_date"] = has_date
    checks["freshness"] = has_date if financial else True

    has_numbers = bool(re.search(r'\d+\.?\d*\s*[%円ドル万億千]', output))
    details["has_numbers"] = has_numbers
    checks["confidence_data"] = has_numbers

    # 重み（financialはfreshnessを重視）
    if financial:
        weights = {
            "not_empty":       0.20, "has_source":      0.15,
            "goal_satisfied":  0.20, "no_contradiction":0.10,
            "source_diverse":  0.10, "freshness":       0.15,
            "confidence_data": 0.10,
        }
    else:
        weights = {
            "not_empty":       0.25, "has_source":      0.20,
            "goal_satisfied":  0.30, "no_contradiction":0.10,
            "source_diverse":  0.05, "freshness":       0.05,
            "confidence_data": 0.05,
        }

    score  = sum(weights[k] for k, v in checks.items() if v)
    passed = score >= 0.60
    icons  = {k: "✅" if v else "❌" for k, v in checks.items()}
    reason = (
        f"score={score:.2f} | "
        f"empty={icons['not_empty']} "
        f"src={icons['has_source']}({details['source_count']}) "
        f"goal={icons['goal_satisfied']} "
        f"contra={icons['no_contradiction']} "
        f"div={icons['source_diverse']}({details['source_diversity']}) "
        f"fresh={icons['freshness']} "
        f"data={icons['confidence_data']}"
    )
    return score, passed, reason, details


# ── POLICY ENGINE — FAIL TYPE 分析 ───────────────────────────────────────────

def policy_engine(
    task: dict, judge_score: float, judge_details: dict
) -> dict:
    """FAIL typeを診断してretry戦略を返す

    fail_types: timeout / legal / weak_source / low_confidence / hallucination
    """
    open_nodes = [k for k, v in task["emo_bus"].items() if v == "OPEN"]

    if open_nodes:
        return {
            "fail_type":      "timeout",
            "retry_strategy": {"action": "retry_gemini", "reason": f"EMO OPEN: {open_nodes}"},
        }
    if task["status"] == "LEGAL_LATCH":
        return {
            "fail_type":      "legal",
            "retry_strategy": {"action": "human_release", "reason": "LEGAL_LATCHはAI自動解除不可"},
        }
    if judge_details.get("has_numbers") and judge_details.get("source_count", 0) == 0:
        return {
            "fail_type":      "hallucination",
            "retry_strategy": {
                "action":  "retry_with_context",
                "context": "数値・データには必ずURLまたは出典を付けてください",
            },
        }
    if judge_details.get("source_count", 0) <= 1:
        return {
            "fail_type":      "weak_source",
            "retry_strategy": {
                "action":  "retry_with_context",
                "context": "情報ソースをURLまたは論文名で必ず明記してください",
            },
        }
    if judge_score < 0.40:
        return {
            "fail_type":      "low_confidence",
            "retry_strategy": {"action": "retry_decompose", "reason": "ゴールを分解して再試行"},
        }

    return {"fail_type": None, "retry_strategy": None}


# ── RETRY ENGINE ─────────────────────────────────────────────────────────────

MAX_RETRY = 2


def retry_engine(
    task: dict, policy: dict, goal: str, observer: Observer, log_fn=None
) -> tuple[str | None, bool]:
    """policy-engineの指示でリトライを実行。

    Returns:
        (new_cascade_output | None, should_continue: bool)
    """
    strategy = policy.get("retry_strategy")
    if not strategy:
        return None, False

    action = strategy["action"]

    if action == "human_release":
        if log_fn: log_fn("   🔴 LEGAL_LATCH: 人間による解除が必要 — 自動リトライ不可")
        return None, False

    retry_count = task.get("retry_count", 0)
    if retry_count >= MAX_RETRY:
        if log_fn: log_fn(f"   ⚠️ リトライ上限({MAX_RETRY}回)到達 — 停止")
        return None, False

    task["retry_count"] = retry_count + 1
    observer.set_policy(policy["fail_type"], task["retry_count"])
    if log_fn:
        log_fn(f"   🔄 リトライ {task['retry_count']}/{MAX_RETRY}: {action}")
    observer.record("retry", action=action, retry_count=task["retry_count"],
                    fail_type=policy["fail_type"])

    persona = route_persona(goal)
    try:
        if action == "retry_gemini":
            out = _call_gemini(persona, goal)
        elif action == "retry_with_context":
            ctx = strategy.get("context", "")
            out, _ = run_with_c_contact(persona, f"{goal}\n\n[追加要件] {ctx}", log_fn)
        elif action == "retry_decompose":
            decompose = (
                f"以下のゴールを2〜3の小ゴールに分解し、各ゴールの回答を出してください:\n{goal}"
            )
            out, _ = run_with_c_contact(persona, decompose, log_fn)
        else:
            out, _ = run_with_c_contact(persona, goal, log_fn)

        if out and len(out.strip()) >= 10:
            return out, True
    except Exception as e:
        if log_fn: log_fn(f"   ❌ リトライ失敗: {e}")

    return None, False


# ── TASK STATE ────────────────────────────────────────────────────────────────

def create_task(goal: str) -> dict:
    return {
        "task_id":        f"task-{uuid.uuid4().hex[:8]}",
        "goal":           goal,
        "status":         "PENDING",
        "emo_bus":        {},
        "warnings":       [],
        "created_at":     datetime.datetime.now().isoformat(),
        "think_outputs":  {},
        "cascade_output": None,
        "legal_output":   None,
        "judge_score":    None,
        "judge_pass":     None,
        "retry_count":    0,
    }

def save_task(task: dict) -> None:
    (TASKS_DIR / f"{task['task_id']}.json").write_text(
        json.dumps(task, ensure_ascii=False, indent=2)
    )

def load_task(task_id: str) -> dict:
    return json.loads((TASKS_DIR / f"{task_id}.json").read_text())


# ── CIIE — 検出・ログ・日記 ───────────────────────────────────────────────────

CIIE_LOG_DIR = ROOT / "memory" / "ciie"
CIIE_LOG_DIR.mkdir(parents=True, exist_ok=True)


def detect_ciie(task: dict, cascade_output: str) -> dict | None:
    """CIIE（アハ体験）検出 — 3タイプをチェック"""
    open_nodes  = [k for k, v in task["emo_bus"].items() if v == "OPEN"]
    cascade_len = len(cascade_output or "")

    if open_nodes and task["status"] == "DONE":
        return {"type": 1, "trigger": f"EMO OPEN({open_nodes}) → CASCADE解決",
                "signal": "矛盾誘発型アハ"}
    if 10 <= cascade_len <= 200:
        return {"type": 2, "trigger": f"cascade出力が{cascade_len}文字に収束",
                "signal": "オーバーフロー収束型アハ"}
    if len(task["think_outputs"]) >= 3:
        return {"type": 3, "trigger": f"{len(task['think_outputs'])}エージェント統合",
                "signal": "カスケード過負荷型アハ"}
    return None


def log_ciie_trace(
    task: dict, ciie: dict | None, cascade_output: str, source: str = "automated"
) -> None:
    today    = str(datetime.date.today())
    log_path = CIIE_LOG_DIR / f"{today}.jsonl"
    entry = {
        "ts":          datetime.datetime.now().isoformat(),
        "source":      source,
        "task_id":     task["task_id"],
        "goal":        task["goal"][:50],
        "ciie":        ciie,
        "triggered":   ciie is not None,
        "cascade_len": len(cascade_output or ""),
        "emo_open":    [k for k, v in task["emo_bus"].items() if v == "OPEN"],
        "think_count": len(task["think_outputs"]),
        "judge_score": task.get("judge_score"),
    }
    with log_path.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def summarize_ciie_today() -> dict:
    today    = str(datetime.date.today())
    log_path = CIIE_LOG_DIR / f"{today}.jsonl"
    if not log_path.exists():
        return {"date": today, "total": 0, "triggered": 0, "types": {}}
    lines     = [json.loads(l) for l in log_path.read_text().strip().splitlines() if l]
    triggered = [l for l in lines if l["triggered"]]
    type_counts: dict[int, int] = {}
    for t in triggered:
        tp = t["ciie"]["type"]
        type_counts[tp] = type_counts.get(tp, 0) + 1
    return {
        "date":      today,
        "total":     len(lines),
        "triggered": len(triggered),
        "types":     type_counts,
        "rate":      f"{len(triggered)/len(lines)*100:.0f}%" if lines else "0%",
    }


def write_ciie_diary(ciie: dict, task: dict) -> None:
    diary_path = ROOT / "memory" / "diary" / f"{datetime.date.today()}.md"
    entry = (
        f"\n## ✨ CIIE — {datetime.datetime.now().strftime('%H:%M')}\n"
        f"- Type: {ciie['type']}（{ciie['signal']}）\n"
        f"- trigger: {ciie['trigger']}\n"
        f"- task: {task['task_id']} / goal: {task['goal'][:40]}\n"
    )
    existing = diary_path.read_text() if diary_path.exists() else ""
    diary_path.write_text(existing + entry)


# ── MEMORY UPDATE ─────────────────────────────────────────────────────────────

def update_memory(task: dict) -> None:
    header   = "# now.md\n"
    existing = MEMORY_NOW.read_text() if MEMORY_NOW.exists() else header
    if task["task_id"] in existing:
        return
    warn_summary = ", ".join(w["type"] for w in task.get("warnings", [])) or "なし"
    entry = (
        f"\n## {task['created_at'][:16]} — {task['task_id']}\n"
        f"- **goal**: {task['goal']}\n"
        f"- **emo_bus**: {task['emo_bus']}\n"
        f"- **warnings**: {warn_summary}\n"
        f"- **cascade**: {'あり' if task['cascade_output'] else 'なし'}\n"
        f"- **judge**: {task['judge_score']:.2f} "
        f"({'PASS ✅' if task['judge_pass'] else 'FAIL ⚠️'})\n"
    )
    MEMORY_NOW.write_text(existing + entry)


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────

def run(goal: str, verbose: bool = True) -> dict:
    def log(msg: str) -> None:
        if verbose: print(msg)

    log(f"\n🚀 MA Runtime v3")
    log(f"   Goal: {goal}")

    task     = create_task(goal)
    observer = Observer(goal)
    financial = is_financial_goal(goal)
    if financial:
        log("   💱 Financial goal detected — freshness重視モード")

    save_task(task)
    log(f"   Task: {task['task_id']} / Session: {observer.session['session_id']}")
    observer.record("init", task_id=task["task_id"], financial=financial)

    # ── MEMORY CONFIDENCE CHECK ────────────────────────────────────────────
    domain = "financial" if financial else "general"
    internal, mem_conf = read_internal_state(domain)
    log(f"   memory confidence: {mem_conf:.2f} (λ={DECAY_LAMBDA[domain]}, domain={domain})")
    observer.record("memory-db", memory_confidence=mem_conf, domain=domain,
                    decay="triggered" if mem_conf < 0.70 else "ok")
    if mem_conf < 0.50:
        log("   ⚠️ memory confidence 低下 — 新鮮な情報を優先します")

    # ── THINK フェーズ ─────────────────────────────────────────────────────
    log("\n── THINK ──────────────────────────────────")
    task["status"] = "THINKING"
    save_task(task)

    persona = route_persona(goal)
    log(f"   Primary persona: {persona}")
    observer.record("skill-router", persona=persona)

    t0 = datetime.datetime.now()
    try:
        out1, shell1 = run_with_c_contact(persona, goal, log)
        task["think_outputs"][persona] = out1
        task["emo_bus"][persona]       = "CLOSED"
        observer.record(f"think/{persona}", shell=shell1,
                        duration_sec=round((datetime.datetime.now()-t0).total_seconds(),1),
                        status="OK", output_len=len(out1))
    except EMOOpen:
        task["emo_bus"][persona] = "OPEN"
        log(f"   ❌ EMO OPEN: {persona}")
        observer.record(f"think/{persona}", status="EMO_OPEN")

    if persona != "critic":
        t0 = datetime.datetime.now()
        try:
            out2, shell2 = run_with_c_contact("critic", goal, log)
            task["think_outputs"]["critic"] = out2
            task["emo_bus"]["critic"]       = "CLOSED"
            observer.record("think/critic", shell=shell2,
                            duration_sec=round((datetime.datetime.now()-t0).total_seconds(),1),
                            status="OK", output_len=len(out2))
        except EMOOpen:
            task["emo_bus"]["critic"] = "OPEN"
            log("   ❌ EMO OPEN: critic")
            observer.record("think/critic", status="EMO_OPEN")

    save_task(task)

    open_nodes = [k for k, v in task["emo_bus"].items() if v == "OPEN"]
    if open_nodes and len(open_nodes) == len(task["emo_bus"]):
        task["status"] = "EMO_OPEN"
        save_task(task)
        log(f"\n   ❌ 全ノードEMO OPEN — ラッチ停止")
        log(f"   リセット: python3 ma_runtime.py --reset {task['task_id']}")
        observer.finish("EMO_OPEN")
        observer.save()
        return task

    log(f"\n   EMOバス: {task['emo_bus']}")

    # ── カスケード制御 ─────────────────────────────────────────────────────
    log("\n── CASCADE ─────────────────────────────────")
    observer.record("cascade", start=datetime.datetime.now().isoformat())
    cascade_out = cascade_reconcile(task["think_outputs"], internal, goal, log)
    task["cascade_output"] = cascade_out
    task["status"]         = "JUDGING"
    save_task(task)
    observer.record("cascade-done", output_len=len(cascade_out))

    # ── 法的インターロック ─────────────────────────────────────────────────
    log("\n── LEGAL INTERLOCK ─────────────────────────")
    severity, legal_out = legal_interlock(goal, cascade_out, log)
    observer.record("legal-interlock", severity=severity)

    if severity == LEGAL_SEVERITY_HIGH:
        task["legal_output"] = legal_out
        task["warnings"].append({
            "type": "LEGAL_LATCH", "severity": "HIGH",
            "timestamp": datetime.datetime.now().isoformat(),
            "message": "重大法的リスク検出 — ラッチ停止",
        })
        task["status"] = "LEGAL_LATCH"
        save_task(task)
        log(f"   🔴 重故障ラッチ — EXECUTE停止")
        log(f"   解除: python3 ma_runtime.py --reset {task['task_id']}")
        log(f"   法的知見:\n{legal_out[:300]}...")
        observer.finish("LEGAL_LATCH")
        observer.save()
        return task

    elif severity == LEGAL_SEVERITY_LOW:
        task["legal_output"] = legal_out
        task["warnings"].append({
            "type": "LEGAL_WARNING", "severity": "LOW",
            "timestamp": datetime.datetime.now().isoformat(),
            "message": "法的キーワード検出 — 専門家確認推奨（実行継続）",
        })
        log(f"   🟡 ワーニング発泡（低故障・実行継続）")
        log(f"   法的知見: {legal_out[:120]}...")
    else:
        log("   ✅ 法的インターロック: クリア")

    save_task(task)

    # ── JUDGE (拡張版) ─────────────────────────────────────────────────────
    log("\n── JUDGE ───────────────────────────────────")
    score, passed, reason, details = judge_extended(goal, cascade_out, financial)
    task["judge_score"] = score
    task["judge_pass"]  = passed
    task["status"]      = "DONE" if passed else "JUDGE_FAILED"
    save_task(task)
    log(f"   {reason}")
    observer.record("judge", score=score, passed=passed,
                    source_count=details.get("source_count"),
                    source_diversity=details.get("source_diversity"),
                    has_date=details.get("has_date"),
                    has_numbers=details.get("has_numbers"))

    # ── POLICY ENGINE → RETRY ──────────────────────────────────────────────
    if not passed:
        log("\n── POLICY ENGINE ───────────────────────────")
        policy = policy_engine(task, score, details)
        log(f"   fail_type: {policy['fail_type']} → strategy: {policy.get('retry_strategy', {}).get('action')}")
        observer.record("policy-engine", **policy)

        if policy["fail_type"]:
            log("\n── RETRY ENGINE ────────────────────────────")
            new_out, ok = retry_engine(task, policy, goal, observer, log)
            if ok and new_out:
                cascade_out            = new_out
                task["cascade_output"] = new_out
                score2, passed2, reason2, details2 = judge_extended(goal, new_out, financial)
                task["judge_score"]    = score2
                task["judge_pass"]     = passed2
                task["status"]         = "DONE" if passed2 else "JUDGE_FAILED"
                save_task(task)
                log(f"   リトライ後Judge: {reason2}")
                observer.record("judge-retry", score=score2, passed=passed2)
            else:
                log("   ⚠️ リトライ不可または失敗 — 現状維持")

    # ── EXECUTE: memory更新 ────────────────────────────────────────────────
    log("\n── EXECUTE ─────────────────────────────────")
    update_memory(task)
    log("   memory/now.md 更新済み")
    observer.record("execute", memory_updated=True)

    # ── CIIE検出 + トレースログ ────────────────────────────────────────────
    ciie = detect_ciie(task, cascade_out)
    log_ciie_trace(task, ciie, cascade_out)
    if ciie:
        write_ciie_diary(ciie, task)
        log(f"   ✨ CIIE検出: Type {ciie['type']} — {ciie['signal']}")
        log(f"   日記に即時追記・トレースログ保存")
        observer.record("ciie", **ciie)
    else:
        log("   CIIE: 未検出（トレース記録済み）")

    # ── Observer保存 ──────────────────────────────────────────────────────
    observer.finish(task["status"])
    log_path = observer.save()
    log(f"   監査ログ: {log_path.name}")

    log(f"\n   {'✅' if task['judge_pass'] else '⚠️ '} {task['status']}")
    return task


def list_tasks(n: int = 10) -> list[dict]:
    files = sorted(TASKS_DIR.glob("task-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    tasks = []
    for f in files[:n]:
        t = json.loads(f.read_text())
        tasks.append({
            "task_id":     t["task_id"],
            "goal":        t["goal"][:40],
            "status":      t["status"],
            "emo_bus":     t.get("emo_bus", {}),
            "score":       t.get("judge_score"),
            "retry_count": t.get("retry_count", 0),
        })
    return tasks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 ma_runtime.py 'goal'")
        print("  python3 ma_runtime.py --list")
        sys.exit(1)

    if sys.argv[1] == "--list":
        print(json.dumps(list_tasks(), ensure_ascii=False, indent=2))
    else:
        goal = " ".join(sys.argv[1:])
        task = run(goal)
        print("\n" + json.dumps({
            "task_id":     task["task_id"],
            "goal":        task["goal"],
            "status":      task["status"],
            "emo_bus":     task["emo_bus"],
            "judge_score": task["judge_score"],
            "retry_count": task.get("retry_count", 0),
            "cascade_len": len(task["cascade_output"] or ""),
        }, ensure_ascii=False, indent=2))

import os
import random
from datetime import datetime, date
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from supabase import create_client, Client

BOT_TOKEN    = os.environ["BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

ELDOR_USERNAME = "Extratinch"
RANO_USERNAME  = "rvln_1"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

JOURNAL_TITLE, JOURNAL_BODY, JOURNAL_TAG = range(3)
QUIZ_ANSWER, QUIZ_GUESS = range(2)
GOAL_TEXT = 0

QUESTIONS = {
    "Would You Rather": [
        "Would you rather travel the world for a year with no fixed plan, or build a cozy home and never leave?",
        "Would you rather always know what I'm thinking, or keep some mystery forever?",
        "Would you rather have 2 more years of LDR then be together forever, or be together now with lots of uncertainty?",
        "Would you rather spend a weekend in the mountains or a week by the ocean?",
        "Would you rather have a relationship with zero arguments but little passion, or deep passion but occasional storms?",
        "Would you rather know the exact date we get married, or be surprised?",
        "Would you rather live in Tashkent or Seoul permanently?",
        "Would you rather spend a whole day in silence together or talk non-stop for 12 hours?",
        "Would you rather cook every meal together or always eat at new places?",
        "Would you rather be fluent in each other's native language or always speak English?",
    ],
    "Deep Talks": [
        "What's one moment from our relationship you'd relive if you could?",
        "What does home feel like to you — is it a place or a person?",
        "When do you feel most loved by me?",
        "What's a fear you have about our future that you've been holding onto?",
        "If you could change one thing about how we communicate, what would it be?",
        "What does your ideal version of us look like in 5 years?",
        "What's something small I do that makes you feel seen?",
        "Is there anything you've been wanting to say but haven't found the right moment?",
        "What do you think makes our connection different from anything else you've known?",
        "What does your dream Sunday morning with me look like?",
    ],
    "Hot Takes": [
        "Long distance makes a relationship stronger — agree or disagree?",
        "The person who loves more in a relationship is always at a disadvantage.",
        "Jealousy is a sign of love, not insecurity.",
        "You should be able to share your phone password with your partner without hesitation.",
        "A couple that argues often is healthier than one that never argues.",
        "Social media is quietly toxic for intimacy.",
        "You should never go to sleep angry at each other.",
        "You can truly love someone and still not be right for them.",
        "Surprises and grand gestures matter more than everyday consistency.",
        "Love languages are overrated — actions are all that matter.",
    ],
    "Silly and Playful": [
        "If we were a dish, what would we be and why?",
        "What animal best represents our relationship dynamic?",
        "If someone made a movie about us, what genre would it be?",
        "What song is secretly our theme song, even if it's embarrassing?",
        "If you had to describe me using only three emojis, which ones?",
        "What's the most chaotic thing we could do together on a random Tuesday?",
        "If we had a couples nickname that strangers gave us, what would it be?",
        "What fictional couple are we most like — and is that a good thing?",
        "If I were a scent, what would I smell like?",
        "What's one random thing you want us to do together before the year ends?",
    ],
    "Future and Dreams": [
        "Where do you picture us living 10 years from now?",
        "What's one tradition you want us to have as a couple?",
        "What kind of parents do you think we'd be?",
        "If money was no issue, what would our life look like?",
        "What's something on your bucket list you want to do with me specifically?",
        "Is there a version of success that scares you — even if it's good?",
        "What's one thing you hope never changes between us?",
        "If we could spend one year anywhere in the world just the two of us, where and why?",
        "What do you think our biggest strength as a team is?",
        "What's one tradition from your family you want to bring into ours?",
    ],
}

MOODS = {"1": "Heavy", "2": "Low", "3": "Good", "4": "Warm", "5": "Amazing"}
MOOD_EMOJI = {"1": "😔", "2": "😕", "3": "😊", "4": "🥰", "5": "✨"}

GOAL_CATEGORIES = [
    ("career",   "Career and Purpose"),
    ("family",   "Family and Marriage"),
    ("location", "Where We Live"),
    ("faith",    "Faith and Values"),
    ("finance",  "Financial Goals"),
    ("growth",   "Personal Growth"),
]

QUIZ_QUESTIONS = [
    ("What is my comfort food when I'm stressed?", "rano"),
    ("Which city would I most want to live in for 1 year?", "eldor"),
    ("What is my go-to way to relax after a hard day?", "rano"),
    ("What am I secretly most proud of?", "eldor"),
    ("What is my biggest irrational fear?", "rano"),
    ("What do I find most attractive in a partner?", "eldor"),
    ("What habit of mine do I wish I could change?", "rano"),
    ("What is the first thing I notice about a person?", "eldor"),
    ("What kind of music do I listen to when I'm emotional?", "rano"),
    ("What is my love language?", "eldor"),
]

def who(username):
    if username and username.lower() == ELDOR_USERNAME.lower():
        return "eldor"
    if username and username.lower() == RANO_USERNAME.lower():
        return "rano"
    return "unknown"

def display_name(w):
    return "Eldor" if w == "eldor" else "Ra'no"

def other(w):
    return "rano" if w == "eldor" else "eldor"

def db_get(table, key):
    try:
        r = supabase.table(table).select("*").eq("key", key).execute()
        return r.data[0] if r.data else None
    except:
        return None

def db_set(table, key, data):
    try:
        existing = db_get(table, key)
        if existing:
            supabase.table(table).update({"data": data}).eq("key", key).execute()
        else:
            supabase.table(table).insert({"key": key, "data": data}).execute()
    except Exception as e:
        print("DB error: " + str(e))

def db_get_data(table, key):
    row = db_get(table, key)
    return row["data"] if row else None

async def start(update, ctx):
    username = update.effective_user.username or ""
    w = who(username)
    name = display_name(w) if w != "unknown" else update.effective_user.first_name
    text = (
        "🐧💛🐧 *Welcome to Ra'El, " + name + "*\n\n"
        "_Just the two of us — Eldor & Ra'no_\n\n"
        "🎲 /question — Random question\n"
        "🎯 /quiz — Couples quiz\n"
        "📊 /mood — Log today's mood\n"
        "📖 /journal — Add a memory\n"
        "🌍 /goals — Life goals\n"
        "📈 /moodchart — Mood history\n"
        "🗂 /memories — Browse journal\n"
        "💛 /us — Relationship stats\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def question(update, ctx):
    keyboard = [[InlineKeyboardButton(t, callback_data="topic:" + t)] for t in QUESTIONS]
    await update.message.reply_text("*Pick a topic:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def topic_callback(update, ctx):
    query = update.callback_query
    await query.answer()
    topic = query.data[6:]
    q = random.choice(QUESTIONS[topic])
    await query.edit_message_text("*" + topic + "*\n\n_" + q + "_\n\n💬 _Answer each other!_", parse_mode="Markdown")

async def mood_cmd(update, ctx):
    username = update.effective_user.username or ""
    w = who(username)
    if w == "unknown":
        await update.message.reply_text("I don't recognize your username.")
        return
    keyboard = [[InlineKeyboardButton(MOOD_EMOJI[s], callback_data="mood:" + s + ":" + w) for s in ["1","2","3","4","5"]]]
    today = date.today().isoformat()
    existing = db_get_data("moods", today) or {}
    if w in existing:
        msg = "You already logged " + MOOD_EMOJI[str(existing[w])] + " " + MOODS[str(existing[w])] + " today. Update it?"
    else:
        msg = "*" + display_name(w) + ", how are you feeling today?*"
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def mood_callback(update, ctx):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    score = int(parts[1])
    w = parts[2]
    today = date.today().isoformat()
    existing = db_get_data("moods", today) or {}
    existing[w] = score
    db_set("moods", today, existing)
    other_score = existing.get(other(w))
    if other_score:
        diff = abs(score - other_score)
        if diff == 0:
            sync = "💛 Perfectly in sync today!"
        elif diff == 1:
            sync = "🌊 Almost in sync."
        elif diff >= 3:
            sync = "💙 You're in different places today. Reach out."
        else:
            sync = "😊 Slightly different vibes, that's okay."
        e_score = existing.get("eldor", score)
        r_score = existing.get("rano", score)
        text = "*Mood logged* ✓\n\nEldor: " + MOOD_EMOJI[str(e_score)] + " " + MOODS[str(e_score)] + "\nRa'no: " + MOOD_EMOJI[str(r_score)] + " " + MOODS[str(r_score)] + "\n\n" + sync
    else:
        text = MOOD_EMOJI[str(score)] + " *" + MOODS[str(score)] + "* — logged ✓\n\nWaiting for " + display_name(other(w)) + " to log their mood..."
    await query.edit_message_text(text, parse_mode="Markdown")

async def moodchart(update, ctx):
    try:
        data = supabase.table("moods").select("*").order("key", desc=True).limit(14).execute().data
    except:
        data = []
    if not data:
        await update.message.reply_text("No mood data yet. Use /mood to start.")
        return
    lines = ["*📊 Last 14 days*\n"]
    for row in reversed(data):
        d = row["data"]
        e = MOOD_EMOJI.get(str(d.get("eldor")), "—") if d.get("eldor") else "—"
        r = MOOD_EMOJI.get(str(d.get("rano")), "—") if d.get("rano") else "—"
        lines.append("`" + row["key"][5:] + "` E: " + e + "  R: " + r)
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def journal_cmd(update, ctx):
    await update.message.reply_text("📖 *New Memory*\n\nGive this moment a title:", parse_mode="Markdown")
    return JOURNAL_TITLE

async def journal_title(update, ctx):
    ctx.user_data["journal_title"] = update.message.text
    await update.message.reply_text("Now write the memory — what happened, what it felt like:")
    return JOURNAL_BODY

async def journal_body(update, ctx):
    ctx.user_data["journal_body"] = update.message.text
    keyboard = [
        [InlineKeyboardButton(t, callback_data="tag:" + t) for t in ["First", "Milestone", "Favorite"]],
        [InlineKeyboardButton(t, callback_data="tag:" + t) for t in ["Funny", "Deep", "Everyday"]]
    ]
    await update.message.reply_text("Tag this memory:", reply_markup=InlineKeyboardMarkup(keyboard))
    return JOURNAL_TAG

async def journal_tag(update, ctx):
    query = update.callback_query
    await query.answer()
    tag = query.data[4:]
    w = who(update.effective_user.username or "")
    entry = {
        "id": int(datetime.now().timestamp()),
        "title": ctx.user_data.get("journal_title", ""),
        "body": ctx.user_data.get("journal_body", ""),
        "tag": tag,
        "by": w,
        "date": date.today().strftime("%d %b %Y"),
        "ts": int(datetime.now().timestamp()),
    }
    existing = db_get_data("journal", "entries") or []
    existing.insert(0, entry)
    db_set("journal", "entries", existing)
    body_preview = entry["body"][:100]
    await query.edit_message_text(
        "📖 *Memory saved* ✓\n\n*" + entry["title"] + "*\n_" + body_preview + "_\n\nTagged: " + tag + " · By " + display_name(w),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def memories(update, ctx):
    entries = db_get_data("journal", "entries") or []
    if not entries:
        await update.message.reply_text("No memories yet. Use /journal to add your first.")
        return
    lines = ["📖 *" + str(len(entries)) + " memories*\n"]
    for e in entries[:8]:
        by = "E" if e.get("by") == "eldor" else "R"
        lines.append("[" + by + "] *" + e["title"] + "* · " + e.get("tag", "") + " · " + e.get("date", ""))
        if e.get("body"):
            preview = e["body"][:60] + ("..." if len(e["body"]) > 60 else "")
            lines.append("_" + preview + "_")
        lines.append("")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def goals_cmd(update, ctx):
    keyboard = [[InlineKeyboardButton(l, callback_data="goalcat:" + c)] for c, l in GOAL_CATEGORIES]
    keyboard.append([InlineKeyboardButton("📌 View all goals", callback_data="goalcat:view")])
    await update.message.reply_text("*🌍 Life Goals*\n\nPick a category:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def goals_callback(update, ctx):
    query = update.callback_query
    await query.answer()
    if query.data == "goalcat:view":
        goals = db_get_data("goals", "main") or {}
        lines = ["*🌍 Life Goals*\n"]
        for cat_id, label in GOAL_CATEGORIES:
            g = goals.get(cat_id, {})
            if g.get("eldor") or g.get("rano"):
                lines.append("*" + label + "*")
                if g.get("eldor"):
                    lines.append("  Eldor: " + g["eldor"])
                if g.get("rano"):
                    lines.append("  Ra'no: " + g["rano"])
                if g.get("note"):
                    lines.append("  Note: " + g["note"])
                lines.append("")
        await query.edit_message_text("\n".join(lines) or "No goals yet.", parse_mode="Markdown")
        return
    cat_id = query.data[8:]
    ctx.user_data["goal_cat"] = cat_id
    label = next(l for c, l in GOAL_CATEGORIES if c == cat_id)
    g = (db_get_data("goals", "main") or {}).get(cat_id, {})
    existing_text = ""
    if g.get("eldor"):
        existing_text += "\nEldor: _" + g["eldor"] + "_"
    if g.get("rano"):
        existing_text += "\nRa'no: _" + g["rano"] + "_"
    keyboard = [
        [InlineKeyboardButton("Eldor's view", callback_data="goalwho:eldor"),
         InlineKeyboardButton("Ra'no's view", callback_data="goalwho:rano")],
        [InlineKeyboardButton("Shared note", callback_data="goalwho:note")],
    ]
    await query.edit_message_text("*" + label + "*" + existing_text + "\n\nWhose perspective?", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def goalwho_callback(update, ctx):
    query = update.callback_query
    await query.answer()
    w = query.data[8:]
    ctx.user_data["goal_who"] = w
    label = "Eldor" if w == "eldor" else ("Ra'no" if w == "rano" else "shared note")
    await query.edit_message_text("Type " + label + "'s perspective:")
    return GOAL_TEXT

async def goal_text_handler(update, ctx):
    cat_id = ctx.user_data.get("goal_cat")
    w = ctx.user_data.get("goal_who")
    goals = db_get_data("goals", "main") or {}
    if cat_id not in goals:
        goals[cat_id] = {}
    goals[cat_id][w] = update.message.text
    db_set("goals", "main", goals)
    label = next(l for c, l in GOAL_CATEGORIES if c == cat_id)
    await update.message.reply_text("Saved under *" + label + "*", parse_mode="Markdown")
    return ConversationHandler.END

async def quiz_cmd(update, ctx):
    ctx.user_data["quiz_answers"] = []
    ctx.user_data["quiz_idx"] = 0
    q, w = QUIZ_QUESTIONS[0]
    await update.message.reply_text(
        "🎯 *Couples Quiz*\n\n*" + display_name(w) + "* — answer this about yourself:\n\n_" + q + "_\n\n_(1/" + str(len(QUIZ_QUESTIONS)) + ")_",
        parse_mode="Markdown"
    )
    return QUIZ_ANSWER

async def quiz_answer(update, ctx):
    idx = ctx.user_data["quiz_idx"]
    q, w = QUIZ_QUESTIONS[idx]
    ctx.user_data["quiz_answers"].append({"q": q, "who": w, "answer": update.message.text})
    idx += 1
    ctx.user_data["quiz_idx"] = idx
    if idx < len(QUIZ_QUESTIONS):
        q2, w2 = QUIZ_QUESTIONS[idx]
        await update.message.reply_text(
            "*" + display_name(w2) + "* — answer this:\n\n_" + q2 + "_\n\n_(" + str(idx+1) + "/" + str(len(QUIZ_QUESTIONS)) + ")_",
            parse_mode="Markdown"
        )
        return QUIZ_ANSWER
    ctx.user_data["quiz_idx"] = 0
    ctx.user_data["quiz_guesses"] = []
    ctx.user_data["quiz_score"] = 0
    a = ctx.user_data["quiz_answers"][0]
    await update.message.reply_text(
        "All answered! Now *" + display_name(other(a["who"])) + "* guesses.\n\n*" + display_name(a["who"]) + "* was asked:\n_" + a["q"] + "_\n\nWhat did they say?",
        parse_mode="Markdown"
    )
    return QUIZ_GUESS

async def quiz_guess(update, ctx):
    idx = ctx.user_data["quiz_idx"]
    answers = ctx.user_data["quiz_answers"]
    current = answers[idx]
    guess = update.message.text
    correct = current["answer"].lower()
    close = (guess.lower() in correct or correct in guess.lower() or
             any(word in correct for word in guess.lower().split() if len(word) > 3))
    if close:
        ctx.user_data["quiz_score"] += 1
    ctx.user_data["quiz_guesses"].append({"q": current["q"], "who": current["who"], "answer": current["answer"], "guess": guess, "correct": close})
    idx += 1
    ctx.user_data["quiz_idx"] = idx
    if idx < len(answers):
        a = answers[idx]
        result = "Close!" if close else "They said: " + current["answer"]
        mark = "✅" if close else "❌"
        await update.message.reply_text(
            mark + " " + result + "\n\n*" + display_name(other(a["who"])) + "* — what did *" + display_name(a["who"]) + "* say?\n\n_" + a["q"] + "_",
            parse_mode="Markdown"
        )
        return QUIZ_GUESS
    score = ctx.user_data["quiz_score"]
    total = len(answers)
    pct = round(score / total * 100)
    if pct >= 80:
        emoji = "🥰"
        msg = "You know each other deeply 💛"
    elif pct >= 50:
        emoji = "😊"
        msg = "Pretty well — keep learning each other 🌊"
    else:
        emoji = "🌱"
        msg = "Room to grow — that's what this is for 🌱"
    lines = [emoji + " *" + str(pct) + "% — " + msg + "*\n"]
    for g in ctx.user_data["quiz_guesses"]:
        mark = "✅" if g["correct"] else "❌"
        lines.append(mark + " _" + g["q"] + "_")
        lines.append("  Answer: " + g["answer"])
        lines.append("  Guess: " + g["guess"] + "\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return ConversationHandler.END

async def us(update, ctx):
    try:
        mood_rows = supabase.table("moods").select("*").execute().data or []
        entries = db_get_data("journal", "entries") or []
        goals = db_get_data("goals", "main") or {}
    except:
        mood_rows, entries, goals = [], [], {}
    days = len(mood_rows)
    filled = sum(1 for g in goals.values() if g.get("eldor") and g.get("rano"))
    if mood_rows:
        e_scores = [r["data"]["eldor"] for r in mood_rows if r["data"].get("eldor")]
        r_scores = [r["data"]["rano"] for r in mood_rows if r["data"].get("rano")]
        ae = sum(e_scores) / len(e_scores) if e_scores else 0
        ar = sum(r_scores) / len(r_scores) if r_scores else 0
        mood_line = "Eldor avg: " + str(round(ae, 1)) + "/5  Ra'no avg: " + str(round(ar, 1)) + "/5"
    else:
        mood_line = "No mood data yet"
    await update.message.reply_text(
        "🐧💛🐧 *Eldor & Ra'no*\n\n📊 Mood days: *" + str(days) + "*\n_" + mood_line + "_\n\n📖 Memories: *" + str(len(entries)) + "*\n🌍 Goals aligned: *" + str(filled) + "/" + str(len(GOAL_CATEGORIES)) + "*\n\n_Just the two of you. Keep going._ 💛",
        parse_mode="Markdown"
    )

async def cancel(update, ctx):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("question", question))
    app.add_handler(CommandHandler("moodchart", moodchart))
    app.add_handler(CommandHandler("memories", memories))
    app.add_handler(CommandHandler("goals", goals_cmd))
    app.add_handler(CommandHandler("us", us))
    app.add_handler(CommandHandler("mood", mood_cmd))
    app.add_handler(CallbackQueryHandler(topic_callback, pattern="^topic:"))
    app.add_handler(CallbackQueryHandler(mood_callback, pattern="^mood:"))
    app.add_handler(CallbackQueryHandler(goals_callback, pattern="^goalcat:"))
    app.add_handler(CallbackQueryHandler(goalwho_callback, pattern="^goalwho:"))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("journal", journal_cmd)],
        states={
            JOURNAL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, journal_title)],
            JOURNAL_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, journal_body)],

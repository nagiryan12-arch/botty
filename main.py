import os
import json
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask
from threading import Thread
from dotenv import load_dotenv  # <-- added

# -----------------------------
# Load .env file
# -----------------------------
load_dotenv()

# -----------------------------
# Environment variables / config
# -----------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
STAFF_ROLE_NAME = os.getenv("STAFF_ROLE_NAME", "Staff")
MESSAGE_WEIGHT = int(os.getenv("MESSAGE_WEIGHT", "1"))
MOD_ACTION_WEIGHT = int(os.getenv("MOD_ACTION_WEIGHT", "5"))
LEADERBOARD_CHANNEL_ID = int(os.getenv("LEADERBOARD_CHANNEL_ID", "0"))  # 0 -> not set
LEADERBOARD_CHANNEL_NAME = os.getenv("LEADERBOARD_CHANNEL_NAME", "staff-activity")
RESET_INTERVAL_DAYS = int(os.getenv("RESET_INTERVAL_DAYS", "7"))

# basic sanity checks
if not DISCORD_TOKEN:
    print("❌ ERROR: DISCORD_TOKEN not set in environment.")
if not DATABASE_URL:
    print("⚠️ WARNING: DATABASE_URL not set — database functionality will fail until provided.")

# -----------------------------
# Flask keep-alive web server
# -----------------------------
app = Flask('')

@app.route('/')
def home():
    return "✅ Staff Tracker Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web, daemon=True)
    t.start()

# -----------------------------
# Discord bot setup
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# Database helpers (Postgres)
# -----------------------------
def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not configured")
    return psycopg2.connect(DATABASE_URL)

def init_database():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS staff_activity (
                user_id TEXT PRIMARY KEY,
                messages INTEGER DEFAULT 0,
                mod_actions INTEGER DEFAULT 0
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bot_config (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized")
    except Exception as e:
        print("❌ DB init error:", e)

def get_staff_data(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT messages, mod_actions FROM staff_activity WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return dict(row)
    except Exception as e:
        print("Error getting staff data:", e)
    return {"messages": 0, "mod_actions": 0}

def increment_messages(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO staff_activity (user_id, messages, mod_actions)
            VALUES (%s, 1, 0)
            ON CONFLICT (user_id)
            DO UPDATE SET messages = staff_activity.messages + 1;
        """, (user_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error incrementing messages:", e)

def increment_mod_actions(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO staff_activity (user_id, messages, mod_actions)
            VALUES (%s, 0, 1)
            ON CONFLICT (user_id)
            DO UPDATE SET mod_actions = staff_activity.mod_actions + 1;
        """, (user_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error incrementing mod actions:", e)

def get_all_staff_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT user_id, messages, mod_actions FROM staff_activity")
        results = cur.fetchall()
        cur.close()
        conn.close()
        return {row['user_id']: {"messages": row['messages'], "mod_actions": row['mod_actions']} for row in results}
    except Exception as e:
        print("Error fetching all staff data:", e)
        return {}

def reset_all_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM staff_activity;")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error resetting data:", e)

def get_config(key, default=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM bot_config WHERE key = %s", (key,))
        res = cur.fetchone()
        cur.close()
        conn.close()
        return res[0] if res else default
    except Exception as e:
        print("Error getting config:", e)
        return default

def set_config(key, value):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO bot_config (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key)
            DO UPDATE SET value = %s;
        """, (key, value, value))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error setting config:", e)

# -----------------------------
# Utility functions
# -----------------------------
def calculate_points(data):
    return data.get("messages", 0) * MESSAGE_WEIGHT + data.get("mod_actions", 0) * MOD_ACTION_WEIGHT

def find_leaderboard_channel(guild):
    if LEADERBOARD_CHANNEL_ID and LEADERBOARD_CHANNEL_ID != 0:
        ch = guild.get_channel(LEADERBOARD_CHANNEL_ID)
        if ch:
            return ch
    for ch in guild.text_channels:
        if ch.name == LEADERBOARD_CHANNEL_NAME:
            return ch
    if guild.system_channel:
        return guild.system_channel
    return guild.text_channels[0] if guild.text_channels else None

# -----------------------------
# Event: message tracking
# -----------------------------
@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        await bot.process_commands(message)
        return

    staff_role = discord.utils.get(message.guild.roles, name=STAFF_ROLE_NAME)
    if staff_role and staff_role in message.author.roles:
        increment_messages(str(message.author.id))

    await bot.process_commands(message)

# -----------------------------
# Commands: points + leaderboard
# -----------------------------
@bot.command(name="points")
async def points_cmd(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = get_staff_data(str(member.id))
    total = calculate_points(data)
    await ctx.send(f"**{member.display_name}** — {total} pts ({data.get('messages',0)} msgs, {data.get('mod_actions',0)} mod actions)")

@bot.command(name="leaderboard")
@commands.has_role(STAFF_ROLE_NAME)
async def leaderboard_cmd(ctx):
    all_data = get_all_staff_data()
    if not all_data:
        await ctx.send("No staff activity recorded yet.")
        return

    board = sorted(((uid, calculate_points(d)) for uid, d in all_data.items()), key=lambda x: x[1], reverse=True)
    lines = []
    for i, (uid, pts) in enumerate(board[:10], start=1):
        member = ctx.guild.get_member(int(uid))
        name = member.display_name if member else f"<Left user {uid}>"
        d = all_data.get(uid, {"messages": 0, "mod_actions": 0})
        lines.append(f"**{i}. {name}** — {pts} pts ({d['messages']} msgs, {d['mod_actions']} actions)")

    embed = discord.Embed(title="🏆 Staff Leaderboard", description="\n".join(lines), color=0xFFD700)
    next_reset = get_config("next_reset")
    if next_reset:
        try:
            reset_dt = datetime.fromisoformat(next_reset)
            embed.set_footer(text=f"Resets on {reset_dt.strftime('%Y-%m-%d %H:%M UTC')}")
        except Exception:
            pass
    await ctx.send(embed=embed)

# -----------------------------
# Audit log tracking (kicks/bans)
# -----------------------------
@bot.event
async def on_member_remove(member):
    try:
        await asyncio.sleep(1)
        async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
            if getattr(entry.target, "id", None) == member.id:
                actor = entry.user
                if actor and not actor.bot:
                    staff_role = discord.utils.get(member.guild.roles, name=STAFF_ROLE_NAME)
                    if staff_role and staff_role in actor.roles:
                        increment_mod_actions(str(actor.id))
                        print(f"✅ Counted kick by {actor} in {member.guild.name}")
                break
    except discord.Forbidden:
        print("⚠️ Missing permission to read audit logs for kicks.")
    except Exception as e:
        print("Error in on_member_remove:", e)

@bot.event
async def on_member_ban(guild, user):
    try:
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if getattr(entry.target, "id", None) == getattr(user, "id", None):
                actor = entry.user
                if actor and not actor.bot:
                    staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
                    if staff_role and staff_role in actor.roles:
                        increment_mod_actions(str(actor.id))
                        print(f"✅ Counted ban by {actor} in {guild.name}")
                break
    except discord.Forbidden:
        print("⚠️ Missing permission to read audit logs for bans.")
    except Exception as e:
        print("Error in on_member_ban:", e)

# -----------------------------
# Scheduled leaderboard posting & reset
# -----------------------------
@tasks.loop(hours=24)
async def scheduled_leaderboard():
    try:
        now = datetime.utcnow()
        next_reset_iso = get_config("next_reset")
        if next_reset_iso:
            try:
                next_reset = datetime.fromisoformat(next_reset_iso)
            except Exception:
                next_reset = now + timedelta(days=RESET_INTERVAL_DAYS)
        else:
            next_reset = now + timedelta(days=RESET_INTERVAL_DAYS)

        if now >= next_reset:
            if not bot.guilds:
                print("⚠️ Bot not in any guilds to post leaderboard.")
            else:
                guild = bot.guilds[0]
                channel = find_leaderboard_channel(guild)
                if not channel:
                    print("⚠️ No leaderboard channel configured/found.")
                else:
                    all_data = get_all_staff_data()
                    if not all_data:
                        await channel.send("No staff activity recorded this period.")
                    else:
                        board = sorted(((uid, calculate_points(d)) for uid, d in all_data.items()), key=lambda x: x[1], reverse=True)
                        lines = []
                        for i, (uid, pts) in enumerate(board, start=1):
                            member = guild.get_member(int(uid))
                            name = member.display_name if member else f"<Left user {uid}>"
                            d = all_data.get(uid, {"messages": 0, "mod_actions": 0})
                            lines.append(f"**{i}. {name}** — {pts} pts ({d['messages']} msgs, {d['mod_actions']} actions)")
                        embed = discord.Embed(title=f"🏆 {'Weekly' if RESET_INTERVAL_DAYS==7 else 'Period'} Staff Leaderboard",
                                              description="\n".join(lines), color=0xFFD700)
                        await channel.send(embed=embed)

            reset_all_data()
            set_config("next_reset", (now + timedelta(days=RESET_INTERVAL_DAYS)).isoformat())
    except Exception as e:
        print("Error in scheduled_leaderboard:", e)

# -----------------------------
# Bot startup
# -----------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        init_database()
    except Exception as e:
        print("DB init failed:", e)
    if not get_config("next_reset"):
        set_config("next_reset", (datetime.utcnow() + timedelta(days=RESET_INTERVAL_DAYS)).isoformat())
    scheduled_leaderboard.start()

# -----------------------------
# Run (start webserver then bot)
# -----------------------------
if __name__ == "__main__":
    keep_alive()
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_TOKEN missing in environment. Add it to .env/Secrets.")
        exit(1)
    bot.run(DISCORD_TOKEN)

code = '''import discord
from discord import app_commands, Embed, Color, ButtonStyle, SelectOption, Interaction, File
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
import asyncio
import json
import os
from datetime import datetime, timedelta
import aiohttp
import io

# ==================== CONFIGURATION ====================
TOKEN = "MTUxMTIxNjI0MjE3Mjc1NjExMA.GO5cDg.8ImxZVvIHmF-7VkUhWfi6mx7R2VzdAZ3tD3Zos"  # ضع توكن البوت هنا
PREFIX = "!"
LOG_CHANNEL_ID = 1499871362884440225
PRISON_ROLE_ID = 1511209543000916069
PRISON_CHANNEL_ID = 1511209661439672481
OWNER_ID = None  # اختياري: ايدي المالك

# ==================== DATA STORAGE ====================
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"warnings": {}, "auto_replies": {}, "invites": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ==================== BOT SETUP ====================
intents = discord.Intents.all()

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.synced = False
    
    async def setup_hook(self):
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            print("**تم مزامنة السلاش كوماندز**")
    
    async def on_ready(self):
        print(f"**البوت {self.user} جاهز**")
        print(f"**عدد السيرفرات: {len(self.guilds)}**")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="**اوامر البوت**"))

bot = Bot()

# ==================== LOG SYSTEM ====================
async def send_log(guild, title, description, color=Color.blue()):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = Embed(title=title, description=description, color=color, timestamp=datetime.now())
        embed.set_footer(text=f"**{guild.name}**")
        await channel.send(embed=embed)

# ==================== CHECKS ====================
def has_perm(perm):
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        perms = {
            "ban": ctx.author.guild_permissions.ban_members,
            "kick": ctx.author.guild_permissions.kick_members,
            "mute": ctx.author.guild_permissions.manage_roles,
            "manage": ctx.author.guild_permissions.manage_channels,
            "manage_roles": ctx.author.guild_permissions.manage_roles,
            "manage_messages": ctx.author.guild_permissions.manage_messages,
            "timeout": ctx.author.guild_permissions.moderate_members,
        }
        if not perms.get(perm, False):
            await ctx.send("**ليس لديك الصلاحية**")
            return False
        return True
    return commands.check(predicate)

# ==================== PREFIX COMMANDS ====================

# --- Avatar ---
@bot.command(name="افتار")
async def avatar_prefix(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = Embed(title=f"**افتار {member}**", color=Color.blue())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

# --- Ban ---
@bot.command(name="لف", aliases=["بنعالي"])
@has_perm("ban")
async def ban_prefix(ctx, member: discord.Member, *, reason="**لا يوجد سبب**"):
    await member.ban(reason=reason)
    await ctx.send(f"**تم تبنيد العضو**")
    await send_log(ctx.guild, "**تبنيد عضو**", f"**العضو:** {member.mention}\\n**بواسطة:** {ctx.author.mention}\\n**السبب:** {reason}", Color.red())

# --- Delete Messages ---
@bot.command(name="م")
@has_perm("manage_messages")
async def clear_prefix(ctx, amount: int = 100):
    if amount > 100:
        amount = 100
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"**تم الحذف**")
    await asyncio.sleep(3)
    await msg.delete()

# --- Help ---
@bot.command(name="help")
async def help_prefix(ctx):
    embed = Embed(title="**اوامر البوت**", color=Color.gold())
    embed.add_field(name="**اوامر الادارة**", value="""
**تايم** - مؤقت عدم تحدث
**سولف** - فك التايم
**اسكت** - ميوت صوتي
**تكلم** - فك الميوت الصوتي
**اص** - ميوت كتابي
**خلاص** - فك الميوت الكتابي
**تف** - طرد عضو
**لف** - بان عضو
**فك** - فك البان
**ت** - تحذير
**شيل** - شيل تحذير
**تحذيرات** - عرض التحذيرات
**ق** - قفل الروم
**ف** - فتح الروم
**م** - مسح الرسائل
**سلو مود** - مؤقت للرسائل
**سلو** - فك السلو مود
**سحب** - سحب عضو صوتي
**سحب الكل** - سحب جميع الاعضاء
**خذ رول** - اعطاء رتبة
**سحب رول** - سحب رتبة
**رتب** - رتب السيرفر
**السيرفر** - معلومات السيرفر
**سجن** - سجن عضو
**افتار** - رؤية افتار
**help** - اوامر البوت
**""", inline=False)
    await ctx.send(embed=embed)

# --- Kick ---
@bot.command(name="تف")
@has_perm("kick")
async def kick_prefix(ctx, member: discord.Member, *, reason="**لا يوجد سبب**"):
    await member.kick(reason=reason)
    await ctx.send(f"**تم طرد العضو**")
    await send_log(ctx.guild, "**طرد عضو**", f"**العضو:** {member.mention}\\n**بواسطة:** {ctx.author.mention}", Color.orange())

# --- Lock ---
@bot.command(name="ق")
@has_perm("manage")
async def lock_prefix(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("**تم قفل الروم**")
    await send_log(ctx.guild, "**قفل روم**", f"**الروم:** {ctx.channel.mention}\\n**بواسطة:** {ctx.author.mention}", Color.red())

# --- Unlock ---
@bot.command(name="ف")
@has_perm("manage")
async def unlock_prefix(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("**تم فتح الروم**")
    await send_log(ctx.guild, "**فتح روم**", f"**الروم:** {ctx.channel.mention}\\n**بواسطة:** {ctx.author.mention}", Color.green())

# --- Move All ---
@bot.command(name="سحب الكل")
@has_perm("manage")
async def move_all_prefix(ctx, channel: discord.VoiceChannel):
    moved = 0
    for member in ctx.guild.members:
        if member.voice and member.voice.channel:
            await member.move_to(channel)
            moved += 1
    await ctx.send("**تم سحب جميع الاعضاء الصوتيين**")
    await send_log(ctx.guild, "**سحب الكل**", f"**الروم:** {channel.mention}\\n**العدد:** {moved}\\n**بواسطة:** {ctx.author.mention}", Color.blue())

# --- Move ---
@bot.command(name="سحب")
@has_perm("manage")
async def move_prefix(ctx, member: discord.Member, channel: discord.VoiceChannel):
    if member.voice and member.voice.channel:
        await member.move_to(channel)
        await ctx.send("**تم سحب العضو**")
        await send_log(ctx.guild, "**سحب عضو**", f"**العضو:** {member.mention}\\n**الروم:** {channel.mention}\\n**بواسطة:** {ctx.author.mention}", Color.blue())
    else:
        await ctx.send("**العضو ليس في فويس**")

# --- Mute Text ---
@bot.command(name="اص")
@has_perm("mute")
async def mute_text_prefix(ctx, member: discord.Member = None):
    if not member and ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = ref.author
    member = member or ctx.author
    
    overwrite = ctx.channel.overwrites_for(member)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(member, overwrite=overwrite)
    await ctx.send("**تم اسكات العضو كتابياً**")
    await send_log(ctx.guild, "**ميوت كتابي**", f"**العضو:** {member.mention}\\n**الروم:** {ctx.channel.mention}\\n**بواسطة:** {ctx.author.mention}", Color.red())

# --- Mute Voice ---
@bot.command(name="اسكت")
@has_perm("mute")
async def mute_voice_prefix(ctx, member: discord.Member = None):
    if not member and ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = ref.author
    member = member or ctx.author
    
    await member.edit(mute=True)
    await ctx.send("**تم اسكات العضو صوتياً**")
    await send_log(ctx.guild, "**ميوت صوتي**", f"**العضو:** {member.mention}\\n**بواسطة:** {ctx.author.mention}", Color.red())

# --- Role Give ---
@bot.command(name="خذ رول")
@has_perm("manage_roles")
async def role_give_prefix(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send("**تم اعطاء العضو الرول**")
    await send_log(ctx.guild, "**اعطاء رول**", f"**العضو:** {member.mention}\\n**الرول:** {role.mention}\\n**بواسطة:** {ctx.author.mention}", Color.green())

# --- Role Remove ---
@bot.command(name="سحب رول")
@has_perm("manage_roles")
async def role_remove_prefix(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send("**تم سحب الرول من العضو**")
    await send_log(ctx.guild, "**سحب رول**", f"**العضو:** {member.mention}\\n**الرول:** {role.mention}\\n**بواسطة:** {ctx.author.mention}", Color.orange())

# --- Roles ---
@bot.command(name="رتب")
async def roles_prefix(ctx):
    roles = sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True)
    roles_text = "\\n".join([f"**{role.name}** - {len(role.members)} عضو" for role in roles if role.name != "@everyone"])
    embed = Embed(title="**رتب السيرفر**", description=roles_text, color=Color.purple())
    await ctx.send(embed=embed)

# --- Server Info ---
@bot.command(name="السيرفر")
async def server_prefix(ctx):
    guild = ctx.guild
    embed = Embed(title="**معلومات السيرفر**", color=Color.blue())
    embed.add_field(name="**الانشاء**", value=f"**{guild.created_at.strftime('%Y/%m/%d')}**", inline=False)
    embed.add_field(name="**المالك**", value=f"**{guild.owner.mention}**", inline=False)
    embed.add_field(name="**عدد الرومات**", value=f"**{len(guild.channels)}**", inline=False)
    embed.add_field(name="**عدد الرتب**", value=f"**{len(guild.roles)}**", inline=False)
    embed.add_field(name="**عدد البوستات**", value=f"**{guild.premium_subscription_count}**", inline=False)
    await ctx.send(embed=embed)

# --- Slowmode ---
@bot.command(name="سلو مود")
@has_perm("manage")
async def slowmode_prefix(ctx, time: str, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    time_lower = time.lower()
    if time_lower.endswith("s"):
        seconds = int(time_lower[:-1])
    elif time_lower.endswith("m"):
        seconds = int(time_lower[:-1]) * 60
    elif time_lower.endswith("h"):
        seconds = int(time_lower[:-1]) * 3600
    elif time_lower.endswith("d"):
        seconds = int(time_lower[:-1]) * 86400
    else:
        seconds = int(time_lower)
    
    await channel.edit(slowmode_delay=seconds)
    await ctx.send("**تم وضع مؤقت في الروم**")
    await send_log(ctx.guild, "**سلو مود**", f"**الروم:** {channel.mention}\\n**المدة:** {time}\\n**بواسطة:** {ctx.author.mention}", Color.yellow())

# --- Unslowmode ---
@bot.command(name="سلو")
@has_perm("manage")
async def unslowmode_prefix(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.edit(slowmode_delay=0)
    await ctx.send("**تم فك السلو مود من الروم**")
    await send_log(ctx.guild, "**فك سلو مود**", f"**الروم:** {channel.mention}\\n**بواسطة:** {ctx.author.mention}", Color.green())

# --- Timeout ---
@bot.command(name="تايم")
@has_perm("timeout")
async def timeout_prefix(ctx, time: str, member: discord.Member = None):
    if not member and ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = ref.author
    member = member or ctx.author
    
    time_lower = time.lower()
    if time_lower.endswith("s"):
        duration = timedelta(seconds=int(time_lower[:-1]))
    elif time_lower.endswith("m"):
        duration = timedelta(minutes=int(time_lower[:-1]))
    elif time_lower.endswith("h"):
        duration = timedelta(hours=int(time_lower[:-1]))
    elif time_lower.endswith("d"):
        duration = timedelta(days=int(time_lower[:-1]))
    else:
        duration = timedelta(minutes=int(time_lower))
    
    await member.timeout(duration, reason="**تايم اوت**")
    await ctx.send("**تم اعطاء تايم اوت للعضو**")
    await send_log(ctx.guild, "**تايم اوت**", f"**العضو:** {member.mention}\\n**المدة:** {time}\\n**بواسطة:** {ctx.author.mention}", Color.red())

# --- Untimeout ---
@bot.command(name="سولف")
@has_perm("timeout")
async def untimeout_prefix(ctx, member: discord.Member = None):
    if not member and ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = ref.author
    member = member or ctx.author
    
    await member.timeout(None, reason="**فك تايم اوت**")
    await ctx.send("**تم فك التايم اوت من العضو**")
    await send_log(ctx.guild, "**فك تايم اوت**", f"**العضو:** {member.mention}\\n**بواسطة:** {ctx.author.mention}", Color.green())

# --- Unmute Voice ---
@bot.command(name="تكلم")
@has_perm("mute")
async def unmute_voice_prefix(ctx, member: discord.Member = None):
    if not member and ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = ref.author
    member = member or ctx.author
    
    await member.edit(mute=False)
    await ctx.send("**تم فك الميوت الصوتي من العضو**")
    await send_log(ctx.guild, "**فك ميوت صوتي**", f"**العضو:** {member.mention}\\n**بواسطة:** {ctx.author.mention}", Color.green())

# --- Unmute Text ---
@bot.command(name="خلاص")
@has_perm("mute")
async def unmute_text_prefix(ctx, member: discord.Member = None):
    if not member and ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = ref.author
    member = member or ctx.author
    
    overwrite = ctx.channel.overwrites_for(member)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(member, overwrite=overwrite)
    await ctx.send("**تم فك الميوت الكتابي من العضو**")
    await send_log(ctx.guild, "**فك ميوت كتابي**", f"**العضو:** {member.mention}\\n**الروم:** {ctx.channel.mention}\\n**بواسطة:** {ctx.author.mention}", Color.green())

# --- Unban ---
@bot.command(name="فك")
@has_perm("ban")
async def unban_prefix(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send("**تم فك الباند من العضو**")
    await send_log(ctx.guild, "**فك بان**", f"**العضو:** {user.mention}\\n**بواسطة:** {ctx.author.mention}", Color.green())

# --- Warn ---
@bot.command(name="ت", aliases=["تحذير"])
@has_perm("manage_messages")
async def warn_prefix(ctx, member: discord.Member = None, *, reason="**لا يوجد سبب**"):
    if not member and ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = ref.author
    member = member or ctx.author
    
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    
    if guild_id not in data["warnings"]:
        data["warnings"][guild_id] = {}
    if user_id not in data["warnings"][guild_id]:
        data["warnings"][guild_id][user_id] = []
    
    data["warnings"][guild_id][user_id].append({
        "reason": reason,
        "by": ctx.author.id,
        "time": datetime.now().isoformat()
    })
    save_data(data)
    
    await ctx.send("**تم تحذير العضو**")
    await send_log(ctx.guild, "**تحذير**", f"**العضو:** {member.mention}\\n**السبب:** {reason}\\n**بواسطة:** {ctx.author.mention}", Color.orange())

# --- Remove Warn ---
@bot.command(name="شيل")
@has_perm("manage_messages")
async def remove_warn_prefix(ctx, arg: str = None, member: discord.Member = None):
    guild_id = str(ctx.guild.id)
    
    if arg == "الكل":
        if member:
            user_id = str(member.id)
            if guild_id in data["warnings"] and user_id in data["warnings"][guild_id]:
                del data["warnings"][guild_id][user_id]
                save_data(data)
                await ctx.send("**تم ازالة تحذيرات العضو**")
            else:
                await ctx.send("**لا يوجد تحذيرات**")
        else:
            if guild_id in data["warnings"]:
                data["warnings"][guild_id] = {}
                save_data(data)
                await ctx.send("**تم ازالة تحذيرات الاعضاء**")
    else:
        if arg and arg.isdigit():
            amount = int(arg)
            if member:
                user_id = str(member.id)
                if guild_id in data["warnings"] and user_id in data["warnings"][guild_id]:
                    data["warnings"][guild_id][user_id] = data["warnings"][guild_id][user_id][:-amount]
                    save_data(data)
                    await ctx.send(f"**تم ازالة {amount} تحذيرات من العضو**")
            else:
                user_id = str(ctx.author.id)
                if guild_id in data["warnings"] and user_id in data["warnings"][guild_id]:
                    data["warnings"][guild_id][user_id] = data["warnings"][guild_id][user_id][:-amount]
                    save_data(data)
                    await ctx.send(f"**تم ازالة {amount} تحذيرات منك**")
        else:
            if member:
                user_id = str(member.id)
                if guild_id in data["warnings"] and user_id in data["warnings"][guild_id]:
                    data["warnings"][guild_id][user_id] = data["warnings"][guild_id][user_id][:-1]
                    save_data(data)
                    await ctx.send("**تم ازالة تحذيرات العضو**")
            else:
                user_id = str(ctx.author.id)
                if guild_id in data["warnings"] and user_id in data["warnings"][guild_id]:
                    data["warnings"][guild_id][user_id] = data["warnings"][guild_id][user_id][:-1]
                    save_data(data)
                    await ctx.send("**تم ازالة تحذيراتك**")

# --- Warnings ---
@bot.command(name="تحذيرات")
async def warnings_prefix(ctx, member: discord.Member = None):
    guild_id = str(ctx.guild.id)
    
    if not member:
        if guild_id not in data["warnings"] or not data["warnings"][guild_id]:
            await ctx.send("**لا يوجد تحذيرات في السيرفر**")
            return
        
        embed = Embed(title="**تحذيرات السيرفر**", color=Color.orange())
        for user_id, warns in data["warnings"][guild_id].items():
            user = ctx.guild.get_member(int(user_id))
            if user and warns:
                embed.add_field(name=f"**{user}**", value=f"**عدد التحذيرات: {len(warns)}**", inline=False)
        await ctx.send(embed=embed)
    else:
        user_id = str(member.id)
        if guild_id in data["warnings"] and user_id in data["warnings"][guild_id] and data["warnings"][guild_id][user_id]:
            embed = Embed(title=f"**تحذيرات {member}**", color=Color.orange())
            for i, warn in enumerate(data["warnings"][guild_id][user_id], 1):
                embed.add_field(name=f"**تحذير {i}**", value=f"**السبب:** {warn['reason']}\\n**الوقت:** {warn['time']}", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("**لا يوجد تحذيرات لهذا العضو**")

# --- Prison ---
@bot.command(name="سجن")
@has_perm("ban")
async def prison_prefix(ctx, member: discord.Member):
    prison_role = ctx.guild.get_role(PRISON_ROLE_ID)
    prison_channel = ctx.guild.get_channel(PRISON_CHANNEL_ID)
    
    if not prison_role or not prison_channel:
        await ctx.send("**لم يتم اعداد السجن**")
        return
    
    roles_to_remove = [r for r in member.roles if r != ctx.guild.default_role]
    await member.remove_roles(*roles_to_remove)
    await member.add_roles(prison_role)
    await prison_channel.set_permissions(member, read_messages=True, send_messages=True)
    
    await ctx.send(f"**تم سجن العضو {member.mention}**")
    await send_log(ctx.guild, "**سجن**", f"**العضو:** {member.mention}\\n**بواسطة:** {ctx.author.mention}", Color.dark_red())

# ==================== SLASH COMMANDS ====================

# --- Avatar ---
@bot.tree.command(name="avatar", description="رؤية افتار شخص")
@app_commands.describe(member="العضو")
async def avatar_slash(interaction: Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = Embed(title=f"**افتار {member}**", color=Color.blue())
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# --- Ban ---
@bot.tree.command(name="ban", description="لطرد شخص من السيرفر")
@app_commands.describe(member="العضو", reason="السبب")
@app_commands.checks.has_permissions(ban_members=True)
async def ban_slash(interaction: Interaction, member: discord.Member, reason: str = "**لا يوجد سبب**"):
    await member.ban(reason=reason)
    await interaction.response.send_message("**تم تبنيد العضو**")
    await send_log(interaction.guild, "**تبنيد**", f"**العضو:** {member.mention}\\n**بواسطة:** {interaction.user.mention}\\n**السبب:** {reason}", Color.red())

# --- Delete Messages ---
@bot.tree.command(name="delete_messages", description="حذف الرسائل في الشات")
@app_commands.describe(amount="عدد الرسائل", channel="الروم")
@app_commands.checks.has_permissions(manage_messages=True)
async def delete_messages_slash(interaction: Interaction, amount: int, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    if amount > 100:
        amount = 100
    await channel.purge(limit=amount)
    await interaction.response.send_message("**تم الحذف**", ephemeral=True)
    await send_log(interaction.guild, "**حذف رسائل**", f"**الروم:** {channel.mention}\\n**العدد:** {amount}\\n**بواسطة:** {interaction.user.mention}", Color.yellow())

# --- Help ---
@bot.tree.command(name="help", description="اوامر البوت")
async def help_slash(interaction: Interaction):
    embed = Embed(title="**اوامر البوت**", color=Color.gold())
    embed.add_field(name="**السلاش كوماندز**", value="""
**/avatar** - افتار
**/ban** - بان
**/delete_messages** - حذف رسائل
**/help** - المساعدة
**/invite** - عدد الاعضاء المدخلين
**/kick** - طرد
**/lock** - قفل روم
**/unlock** - فتح روم
**/move** - سحب عضو
**/move_all** - سحب الكل
**/mute_text** - ميوت كتابي
**/mute_voice** - ميوت صوتي
**/role_give** - اعطاء رول
**/role_remove** - سحب رول
**/roles** - رتب السيرفر
**/server** - معلومات السيرفر
**/slowmode** - سلو مود
**/unslomode** - فك سلو مود
**/timeout** - تايم اوت
**/untimeout** - فك تايم
**/unmute_voice** - فك ميوت صوتي
**/unmute_text** - فك ميوت كتابي
**/unban** - فك بان
**/warn** - تحذير
**/remove_warn** - شيل تحذير
**/warnings** - التحذيرات
**/add_emoji** - اضافة ايموجي
**/add_sticker** - اضافة ستيكر
**/auto_reply** - ردود تلقائية
**/bot** - عدد السيرفرات
**/delete_reply** - حذف رد تلقائي
**/server_avatar** - افتار السيرفر
**/banner** - بنر العضو
**/inrole** - معلومات رول
**/nick** - تغيير اسم
**/say** - رسالة ايمبد
**/set_icon_role** - ايكون للرول
**/prison** - سجن عضو
**""", inline=False)
    await interaction.response.send_message(embed=embed)

# --- Invite ---
@bot.tree.command(name="invite", description="عدد الاعضاء الذي ادخلهم الشخص")
@app_commands.describe(member="العضو")
async def invite_slash(interaction: Interaction, member: discord.Member):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    
    if guild_id not in data["invites"]:
        data["invites"][guild_id] = {}
    
    count = data["invites"][guild_id].get(user_id, 0)
    await interaction.response.send_message(f"**عدد الاعضاء الذي ادخلهم {member.mention}: {count}**")

# --- Kick ---
@bot.tree.command(name="kick", description="طرد عضو من السيرفر")
@app_commands.describe(member="العضو", reason="السبب")
@app_commands.checks.has_permissions(kick_members=True)
async def kick_slash(interaction: Interaction, member: discord.Member, reason: str = "**لا يوجد سبب**"):
    await member.kick(reason=reason)
    await interaction.response.send_message("**تم طرد العضو**")
    await send_log(interaction.guild, "**طرد**", f"**العضو:** {member.mention}\\n**بواسطة:** {interaction.user.mention}", Color.orange())

# --- Lock ---
@bot.tree.command(name="lock", description="قفل الروم")
@app_commands.describe(channel="الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock_slash(interaction: Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message("**تم قفل الروم**")
    await send_log(interaction.guild, "**قفل**", f"**الروم:** {channel.mention}\\n**بواسطة:** {interaction.user.mention}", Color.red())

# --- Unlock ---
@bot.tree.command(name="unlock", description="فتح روم")
@app_commands.describe(channel="الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock_slash(interaction: Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    await channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message("**تم فتح الروم**")
    await send_log(interaction.guild, "**فتح**", f"**الروم:** {channel.mention}\\n**بواسطة:** {interaction.user.mention}", Color.green())

# --- Move All ---
@bot.tree.command(name="move_all", description="سحب جميع اعضاء الفويس")
@app_commands.describe(channel="الروم الصوتي")
@app_commands.checks.has_permissions(manage_channels=True)
async def move_all_slash(interaction: Interaction, channel: discord.VoiceChannel):
    moved = 0
    for member in interaction.guild.members:
        if member.voice and member.voice.channel:
            await member.move_to(channel)
            moved += 1
    await interaction.response.send_message("**تم سحب جميع الاعضاء الصوتيين**")
    await send_log(interaction.guild, "**سحب الكل**", f"**الروم:** {channel.mention}\\n**العدد:** {moved}\\n**بواسطة:** {interaction.user.mention}", Color.blue())

# --- Move ---
@bot.tree.command(name="move", description="سحب عضو صوتي")
@app_commands.describe(member="العضو", channel="الروم الصوتي")
@app_commands.checks.has_permissions(manage_channels=True)
async def move_slash(interaction: Interaction, member: discord.Member, channel: discord.VoiceChannel):
    if member.voice and member.voice.channel:
        await member.move_to(channel)
        await interaction.response.send_message("**تم سحب العضو**")
        await send_log(interaction.guild, "**سحب**", f"**العضو:** {member.mention}\\n**الروم:** {channel.mention}\\n**بواسطة:** {interaction.user.mention}", Color.blue())
    else:
        await interaction.response.send_message("**العضو ليس في فويس**", ephemeral=True)

# --- Mute Text ---
@bot.tree.command(name="mute_text", description="ميوت كتابي")
@app_commands.describe(member="العضو", channel="الروم", reason="السبب")
@app_commands.checks.has_permissions(manage_roles=True)
async def mute_text_slash(interaction: Interaction, member: discord.Member, channel: discord.TextChannel = None, reason: str = "**لا يوجد سبب**"):
    channel = channel or interaction.channel
    
    class MuteReasonView(View):
        def __init__(self):
            super().__init__(timeout=60)
        
        @discord.ui.select(
            placeholder="**اختر سبب الميوت**",
            options=[
                SelectOption(label="قذف", value="28d", description="المدة: 28 يوم"),
                SelectOption(label="سب", value="20m", description="المدة: 20 دقيقة"),
                SelectOption(label="افتعال مشاكل", value="20m", description="المدة: 20 دقيقة"),
                SelectOption(label="سياسة", value="15m", description="المدة: 15 دقيقة"),
                SelectOption(label="نشر", value="3d", description="المدة: 3 ايام"),
            ]
        )
        async def select_callback(self, select_interaction: Interaction, select: Select):
            duration = select.values[0]
            time_lower = duration.lower()
            if time_lower.endswith("d"):
                seconds = int(time_lower[:-1]) * 86400
            elif time_lower.endswith("m"):
                seconds = int(time_lower[:-1]) * 60
            else:
                seconds = int(time_lower) * 60
            
            overwrite = channel.overwrites_for(member)
            overwrite.send_messages = False
            await channel.set_permissions(member, overwrite=overwrite)
            
            await select_interaction.response.send_message(f"**تم اسكات العضو كتابياً**")
            await send_log(interaction.guild, "**ميوت كتابي**", f"**العضو:** {member.mention}\\n**الروم:** {channel.mention}\\n**السبب:** {select.options[0].label}\\n**المدة:** {duration}\\n**بواسطة:** {interaction.user.mention}", Color.red())
    
    view = MuteReasonView()
    await interaction.response.send_message("**اختر سبب الميوت:**", view=view, ephemeral=True)

# --- Mute Voice ---
@bot.tree.command(name="mute_voice", description="ميوت صوتي")
@app_commands.describe(member="العضو")
@app_commands.checks.has_permissions(manage_roles=True)
async def mute_voice_slash(interaction: Interaction, member: discord.Member):
    await member.edit(mute=True)
    await interaction.response.send_message("**تم اسكات العضو صوتياً**")
    await send_log(interaction.guild, "**ميوت صوتي**", f"**العضو:** {member.mention}\\n**بواسطة:** {interaction.user.mention}", Color.red())

# --- Role Give ---
@bot.tree.command(name="role_give", description="اعطاء رول")
@app_commands.describe(member="العضو", role="الرول")
@app_commands.checks.has_permissions(manage_roles=True)
async def role_give_slash(interaction: Interaction, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await interaction.response.send_message("**تم اعطاء العضو الرول**")
    await send_log(interaction.guild, "**اعطاء رول**", f"**العضو:** {member.mention}\\n**الرول:** {role.mention}\\n**بواسطة:** {interaction.user.mention}", Color.green())

# --- Role Remove ---
@bot.tree.command(name="role_remove", description="سحب رول")
@app_commands.describe(member="العضو", role="الرول")
@app_commands.checks.has_permissions(manage_roles=True)
async def role_remove_slash(interaction: Interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await interaction.response.send_message("**تم سحب الرول من العضو**")
    await send_log(interaction.guild, "**سحب رول**", f"**العضو:** {member.mention}\\n**الرول:** {role.mention}\\n**بواسطة:** {interaction.user.mention}", Color.orange())

# --- Roles ---
@bot.tree.command(name="roles", description="رتب السيرفر")
async def roles_slash(interaction: Interaction):
    roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
    roles_text = "\\n".join([f"**{role.name}** - {len(role.members)} عضو" for role in roles if role.name != "@everyone"])
    embed = Embed(title="**رتب السيرفر**", description=roles_text, color=Color.purple())
    await interaction.response.send_message(embed=embed)

# --- Server ---
@bot.tree.command(name="server", description="معلومات السيرفر")
async def server_slash(interaction: Interaction):
    guild = interaction.guild
    embed = Embed(title="**معلومات السيرفر**", color=Color.blue())
    embed.add_field(name="**الانشاء**", value=f"**{guild.created_at.strftime('%Y/%m/%d')}**", inline=False)
    embed.add_field(name="**المالك**", value=f"**{guild.owner.mention}**", inline=False)
    embed.add_field(name="**عدد الرومات**", value=f"**{len(guild.channels)}**", inline=False)
    embed.add_field(name="**عدد الرتب**", value=f"**{len(guild.roles)}**", inline=False)
    embed.add_field(name="**عدد البوستات**", value=f"**{guild.premium_subscription_count}**", inline=False)
    await interaction.response.send_message(embed=embed)

# --- Slowmode ---
@bot.tree.command(name="slowmode", description="مؤقت للرسائل في الرومات")
@app_commands.describe(time="المدة (مثال: 7s, 7m, 7h, 7d)", channel="الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode_slash(interaction: Interaction, time: str, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    time_lower = time.lower()
    if time_lower.endswith("s"):
        seconds = int(time_lower[:-1])
    elif time_lower.endswith("m"):
        seconds = int(time_lower[:-1]) * 60
    elif time_lower.endswith("h"):
        seconds = int(time_lower[:-1]) * 3600
    elif time_lower.endswith("d"):
        seconds = int(time_lower[:-1]) * 86400
    else:
        seconds = int(time_lower)
    
    await channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message("**تم وضع مؤقت في الروم**")
    await send_log(interaction.guild, "**سلو مود**", f"**الروم:** {channel.mention}\\n**المدة:** {time}\\n**بواسطة:** {interaction.user.mention}", Color.yellow())

# --- Unslowmode ---
@bot.tree.command(name="unslomode", description="شيل مؤقت الرسائل في الرومات")
@app_commands.describe(channel="الروم")
@app_commands.checks.has_permissions(manage_channels=True)
async def unslomode_slash(interaction: Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    await channel.edit(slowmode_delay=0)
    await interaction.response.send_message("**تم فك السلو مود من الروم**")
    await send_log(interaction.guild, "**فك سلو مود**", f"**الروم:** {channel.mention}\\n**بواسطة:** {interaction.user.mention}", Color.green())

# --- Timeout ---
@bot.tree.command(name="timeout", description="مؤقت عدم تحدث للشخص")
@app_commands.describe(member="العضو", time="المدة (مثال: 10m, 1h, 1d)", reason="السبب")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout_slash(interaction: Interaction, member: discord.Member, time: str, reason: str = "**لا يوجد سبب**"):
    time_lower = time.lower()
    if time_lower.endswith("s"):
        duration = timedelta(seconds=int(time_lower[:-1]))
    elif time_lower.endswith("m"):
        duration = timedelta(minutes=int(time_lower[:-1]))
    elif time_lower.endswith("h"):
        duration = timedelta(hours=int(time_lower[:-1]))
    elif time_lower.endswith("d"):
        duration = timedelta(days=int(time_lower[:-1]))
    else:
        duration = timedelta(minutes=int(time_lower))
    
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message("**تم اعطاء تايم اوت للعضو**")
    await send_log(interaction.guild, "**تايم اوت**", f"**العضو:** {member.mention}\\n**المدة:** {time}\\n**بواسطة:** {interaction.user.mention}", Color.red())

# --- Untimeout ---
@bot.tree.command(name="untimeout", description="شيل مؤقت عدم تحدث الشخص")
@app_commands.describe(member="العضو")
@app_commands.checks.has_permissions(moderate_members=True)
async def untimeout_slash(interaction: Interaction, member: discord.Member):
    await member.timeout(None, reason="**فك تايم**")
    await interaction.response.send_message("**تم فك التايم اوت من العضو**")
    await send_log(interaction.guild, "**فك تايم**", f"**العضو:** {member.mention}\\n**بواسطة:** {interaction.user.mention}", Color.green())

# --- Unmute Voice ---
@bot.tree.command(name="unmute_voice", description="فك الميوت الصوتي")
@app_commands.describe(member="العضو")
@app_commands.checks.has_permissions(manage_roles=True)
async def unmute_voice_slash(interaction: Interaction, member: discord.Member):
    await member.edit(mute=False)
    await interaction.response.send_message("**تم فك الميوت الصوتي من العضو**")
    await send_log(interaction.guild, "**فك ميوت صوتي**", f"**العضو:** {member.mention}\\n**بواسطة:** {interaction.user.mention}", Color.green())

# --- Unmute Text ---
@bot.tree.command(name="unmute_text", description="فك الميوت الكتابي")
@app_commands.describe(member="العضو", channel="الروم")
@app_commands.checks.has_permissions(manage_roles=True)
async def unmute_text_slash(interaction: Interaction, member: discord.Member, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    overwrite = channel.overwrites_for(member)
    overwrite.send_messages = True
    await channel.set_permissions(member, overwrite=overwrite)
    await interaction.response.send_message("**تم فك الميوت الكتابي من العضو**")
    await send_log(interaction.guild, "**فك ميوت كتابي**", f"**العضو:** {member.mention}\\n**الروم:** {channel.mention}\\n**بواسطة:** {interaction.user.mention}", Color.green())

# --- Unban ---
@bot.tree.command(name="unban", description="فك الباند")
@app_commands.describe(user_id="ايدي العضو")
@app_commands.checks.has_permissions(ban_members=True)
async def unban_slash(interaction: Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message("**تم فك الباند من العضو**")
    await send_log(interaction.guild, "**فك بان**", f"**العضو:** {user.mention}\\n**بواسطة:** {interaction.user.mention}", Color.green())

# --- Warn ---
@bot.tree.command(name="warn", description="تحذير عضو")
@app_commands.describe(member="العضو", reason="السبب")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn_slash(interaction: Interaction, member: discord.Member, reason: str = "**لا يوجد سبب**"):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    
    if guild_id not in data["warnings"]:
        data["warnings"][guild_id] = {}
    if user_id not in data["warnings"][guild_id]:
        data["warnings"][guild_id][user_id] = []
    
    data["warnings"][guild_id][user_id].append({
        "reason": reason,
        "by": interaction.user.id,
        "time": datetime.now().isoformat()
    })
    save_data(data)
    
    await interaction.response.send_message("**تم تحذير العضو**")
    await send_log(interaction.guild, "**تحذير**", f"**العضو:** {member.mention}\\n**السبب:** {reason}\\n**بواسطة:** {interaction.user.mention}", Color.orange())

# --- Remove Warn ---
@bot.tree.command(name="remove_warn", description="شيل تحذير العضو")
@app_commands.describe(member="العضو", amount="عدد التحذيرات (اكتب 'all' للكل)")
@app_commands.checks.has_permissions(manage_messages=True)
async def remove_warn_slash(interaction: Interaction, member: discord.Member = None, amount: str = "1"):
    guild_id = str(interaction.guild.id)
    
    if not member:
        member = interaction.user
    
    user_id = str(member.id)
    
    if amount.lower() == "all":
        if guild_id in data["warnings"] and user_id in data["warnings"][guild_id]:
            del data["warnings"][guild_id][user_id]
            save_data(data)
            if member == interaction.user:
                await interaction.response.send_message("**تم ازالة تحذيراتك**")
            else:
                await interaction.response.send_message("**تم ازالة تحذيرات العضو**")
        else:
            await interaction.response.send_message("**لا يوجد تحذيرات**", ephemeral=True)
    else:
        try:
            num = int(amount)
            if guild_id in data["warnings"] and user_id in data["warnings"][guild_id]:
                data["warnings"][guild_id][user_id] = data["warnings"][guild_id][user_id][:-num]
                save_data(data)
                if member == interaction.user:
                    await interaction.response.send_message(f"**تم ازالة {num} تحذيرات منك**")
                else:
                    await interaction.response.send_message(f"**تم ازالة {num} تحذيرات من العضو**")
            else:
                await interaction.response.send_message("**لا يوجد تحذيرات**", ephemeral=True)
        except:
            await interaction.response.send_message("**رقم غير صحيح**", ephemeral=True)

# --- Warnings ---
@bot.tree.command(name="warnings", description="التحذيرات كلها")
@app_commands.describe(member="العضو")
async def warnings_slash(interaction: Interaction, member: discord.Member = None):
    guild_id = str(interaction.guild.id)
    
    if not member:
        if guild_id not in data["warnings"] or not data["warnings"][guild_id]:
            await interaction.response.send_message("**لا يوجد تحذيرات في السيرفر**", ephemeral=True)
            return
        
        embed = Embed(title="**تحذيرات السيرفر**", color=Color.orange())
        for user_id, warns in data["warnings"][guild_id].items():
            user = interaction.guild.get_member(int(user_id))
            if user and warns:
                embed.add_field(name=f"**{user}**", value=f"**عدد التحذيرات: {len(warns)}**", inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        user_id = str(member.id)
        if guild_id in data["warnings"] and user_id in data["warnings"][guild_id] and data["warnings"][guild_id][user_id]:
            embed = Embed(title=f"**تحذيرات {member}**", color=Color.orange())
            for i, warn in enumerate(data["warnings"][guild_id][user_id], 1):
                embed.add_field(name=f"**تحذير {i}**", value=f"**السبب:** {warn['reason']}\\n**الوقت:** {warn['time']}", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("**لا يوجد تحذيرات لهذا العضو**", ephemeral=True)

# --- Add Emoji ---
@bot.tree.command(name="add_emoji", description="اضافة ايموجي من سيرفر اخر الى هنا")
@app_commands.describe(emoji_id="ايدي الايموجي", name="الاسم الجديد")
@app_commands.checks.has_permissions(manage_emojis=True)
async def add_emoji_slash(interaction: Interaction, emoji_id: str, name: str = None):
    try:
        emoji = None
        for guild in bot.guilds:
            for e in guild.emojis:
                if str(e.id) == emoji_id:
                    emoji = e
                    break
            if emoji:
                break
        
        if not emoji:
            await interaction.response.send_message("**لم يتم العثور على الايموجي**", ephemeral=True)
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.get(emoji.url) as resp:
                if resp.status == 200:
                    emoji_data = await resp.read()
                    new_name = name or emoji.name
                    new_emoji = await interaction.guild.create_custom_emoji(name=new_name, image=emoji_data)
                    await interaction.response.send_message(f"**تمت اضافة الايموجي** {new_emoji}")
                    await send_log(interaction.guild, "**اضافة ايموجي**", f"**الايموجي:** {new_emoji}\\n**بواسطة:** {interaction.user.mention}", Color.green())
    except Exception as e:
        await interaction.response.send_message(f"**خطأ:** {str(e)}", ephemeral=True)

# --- Add Sticker ---
@bot.tree.command(name="add_sticker", description="اضافة ستيكر من سيرفر اخر الى هنا")
@app_commands.describe(sticker_id="ايدي الستيكر", name="الاسم الجديد")
@app_commands.checks.has_permissions(manage_emojis=True)
async def add_sticker_slash(interaction: Interaction, sticker_id: str, name: str = None):
    try:
        sticker = None
        for guild in bot.guilds:
            for s in guild.stickers:
                if str(s.id) == sticker_id:
                    sticker = s
                    break
            if sticker:
                break
        
        if not sticker:
            await interaction.response.send_message("**لم يتم العثور على الستيكر**", ephemeral=True)
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.get(sticker.url) as resp:
                if resp.status == 200:
                    sticker_data = await resp.read()
                    new_name = name or sticker.name
                    await interaction.guild.create_sticker(name=new_name, description="**ستيكر**", file=discord.File(io.BytesIO(sticker_data), filename="sticker.png"))
                    await interaction.response.send_message("**تمت اضافة الستيكر**")
                    await send_log(interaction.guild, "**اضافة ستيكر**", f"**الستيكر:** {new_name}\\n**بواسطة:** {interaction.user.mention}", Color.green())
    except Exception as e:
        await interaction.response.send_message(f"**خطأ:** {str(e)}", ephemeral=True)

# --- Auto Reply ---
class AutoReplyModal(Modal, title="**ردود تلقائية**"):
    key = TextInput(label="**الكلمة المفتاحية**", placeholder="اكتب الكلمة المفتاحية", required=True)
    reply = TextInput(label="**الرد**", placeholder="اكتب رد البوت", required=True, style=discord.TextStyle.paragraph)
    include = TextInput(label="**include (True/False)**", placeholder="True او False", required=True)
    
    async def on_submit(self, interaction: Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in data["auto_replies"]:
            data["auto_replies"][guild_id] = []
        
        include_bool = self.include.value.lower() == "true"
        data["auto_replies"][guild_id].append({
            "key": self.key.value,
            "reply": self.reply.value,
            "include": include_bool
        })
        save_data(data)
        await interaction.response.send_message("**تمت اضافة الرد**", ephemeral=True)

@bot.tree.command(name="auto_reply", description="ردود تلقائية")
async def auto_reply_slash(interaction: Interaction):
    await interaction.response.send_modal(AutoReplyModal())

# --- Bot Info ---
@bot.tree.command(name="bot", description="عدد السيرفرات التي تستخدم البوت")
async def bot_slash(interaction: Interaction):
    await interaction.response.send_message(f"**عدد السيرفرات التي تستخدم البوت: {len(bot.guilds)}**")

# --- Delete Reply ---
@bot.tree.command(name="delete_reply", description="حذف رد تلقائي")
async def delete_reply_slash(interaction: Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in data["auto_replies"] or not data["auto_replies"][guild_id]:
        await interaction.response.send_message("**لا يوجد ردود تلقائية**", ephemeral=True)
        return
    
    class DeleteReplyView(View):
        def __init__(self, replies):
            super().__init__(timeout=60)
            self.replies = replies
        
        @discord.ui.select(
            placeholder="**اختر رد لحذفه**",
            options=[SelectOption(label=reply["key"][:25], value=str(i), description=reply["reply"][:50]) for i, reply in enumerate(replies)]
        )
        async def select_callback(self, select_interaction: Interaction, select: Select):
            index = int(select.values[0])
            deleted = self.replies.pop(index)
            data["auto_replies"][guild_id] = self.replies
            save_data(data)
            await select_interaction.response.send_message(f"**تم حذف الرد: {deleted['key']}**")
    
    view = DeleteReplyView(data["auto_replies"][guild_id])
    await interaction.response.send_message("**اختر رد لحذفه:**", view=view, ephemeral=True)

# --- Server Avatar ---
@bot.tree.command(name="server_avatar", description="لرؤية افتار السيرفر")
async def server_avatar_slash(interaction: Interaction):
    if interaction.guild.icon:
        embed = Embed(title=f"**افتار {interaction.guild.name}**", color=Color.blue())
        embed.set_image(url=interaction.guild.icon.url)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("**لا يوجد افتار للسيرفر**", ephemeral=True)

# --- Banner ---
@bot.tree.command(name="banner", description="لرؤية بنر العضو")
@app_commands.describe(member="العضو")
async def banner_slash(interaction: Interaction, member: discord.Member):
    user = await bot.fetch_user(member.id)
    if user.banner:
        embed = Embed(title=f"**بنر {member}**", color=Color.blue())
        embed.set_image(url=user.banner.url)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("**لا يوجد بنر لهذا العضو**", ephemeral=True)

# --- Inrole ---
@bot.tree.command(name="inrole", description="لرؤية معلومات رول")
@app_commands.describe(role="الرول")
async def inrole_slash(interaction: Interaction, role: discord.Role):
    embed = Embed(title=f"**معلومات الرول**", color=Color.purple())
    embed.add_field(name="**اسم الخادم**", value=f"**{interaction.guild.name}**", inline=False)
    embed.add_field(name="**اسم الرتبة**", value=f"**{role.name}**", inline=False)
    embed.add_field(name="**ايدي الرتبة**", value=f"**{role.id}**", inline=False)
    embed.add_field(name="**وقت انشاء الرتبة**", value=f"**{role.created_at.strftime('%Y/%m/%d %H:%M')}**", inline=False)
    embed.add_field(name="**الي يملكون الرتبة**", value=f"**{len(role.members)}**", inline=False)
    embed.add_field(name="**لون الرتبة**", value=f"**{role.color}**", inline=False)
    await interaction.response.send_message(embed=embed)

# --- Nick ---
@bot.tree.command(name="nick", description="تغيير اسم عضو")
@app_commands.describe(member="العضو", name="الاسم الجديد")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nick_slash(interaction: Interaction, member: discord.Member, name: str):
    await member.edit(nick=name)
    await interaction.response.send_message("**تم تغيير الاسم بنجاح**")
    await send_log(interaction.guild, "**تغيير اسم**", f"**العضو:** {member.mention}\\n**الاسم الجديد:** {name}\\n**بواسطة:** {interaction.user.mention}", Color.blue())

# --- Say ---
@bot.tree.command(name="say", description="ارسال رسالة على شكل ايمبد")
@app_commands.describe(message="الرسالة", channel="الروم")
async def say_slash(interaction: Interaction, message: str, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    embed = Embed(description=message, color=Color.blue())
    embed.set_footer(text=f"**{interaction.user}**")
    await channel.send(embed=embed)
    await interaction.response.send_message("**تم الارسال**", ephemeral=True)

# --- Set Icon Role ---
@bot.tree.command(name="set_icon_role", description="لوضع ايكون لرول")
@app_commands.describe(role="الرول")
@app_commands.checks.has_permissions(manage_roles=True)
async def set_icon_role_slash(interaction: Interaction, role: discord.Role):
    class IconView(View):
        def __init__(self):
            super().__init__(timeout=120)
        
        @discord.ui.button(label="**استخدام ايموجي**", style=ButtonStyle.primary)
        async def emoji_button(self, button_interaction: Interaction, button: Button):
            class EmojiModal(Modal, title="**ايدي الايموجي**"):
                emoji_id = TextInput(label="**ايدي الايموجي**", required=True)
                
                async def on_submit(self, modal_interaction: Interaction):
                    try:
                        emoji = await bot.fetch_emoji(int(self.emoji_id.value))
                        async with aiohttp.ClientSession() as session:
                            async with session.get(emoji.url) as resp:
                                if resp.status == 200:
                                    await role.edit(display_icon=await resp.read())
                                    await modal_interaction.response.send_message("**تم تعيين ايكون للرول**")
                                    await send_log(interaction.guild, "**ايكون رول**", f"**الرول:** {role.mention}\\n**بواسطة:** {interaction.user.mention}", Color.green())
                    except Exception as e:
                        await modal_interaction.response.send_message(f"**خطأ:** {str(e)}", ephemeral=True)
            
            await button_interaction.response.send_modal(EmojiModal())
        
        @discord.ui.button(label="**استخدام صورة**", style=ButtonStyle.secondary)
        async def image_button(self, button_interaction: Interaction, button: Button):
            await button_interaction.response.send_message("**ارفع صورة في الشات وسأستخدمها**", ephemeral=True)
            
            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel and m.attachments
            
            try:
                msg = await bot.wait_for("message", check=check, timeout=60)
                attachment = msg.attachments[0]
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            await role.edit(display_icon=await resp.read())
                            await button_interaction.followup.send("**تم تعيين ايكون للرول**")
                            await send_log(interaction.guild, "**ايكون رول**", f"**الرول:** {role.mention}\\n**بواسطة:** {interaction.user.mention}", Color.green())
            except asyncio.TimeoutError:
                await button_interaction.followup.send("**انتهى الوقت**", ephemeral=True)
    
    view = IconView()
    await interaction.response.send_message("**اختر طريقة:**", view=view, ephemeral=True)

# --- Prison ---
@bot.tree.command(name="prison", description="سجن عضو")
@app_commands.describe(member="العضو")
@app_commands.checks.has_permissions(ban_members=True)
async def prison_slash(interaction: Interaction, member: discord.Member):
    prison_role = interaction.guild.get_role(PRISON_ROLE_ID)
    prison_channel = interaction.guild.get_channel(PRISON_CHANNEL_ID)
    
    if not prison_role or not prison_channel:
        await interaction.response.send_message("**لم يتم اعداد السجن**", ephemeral=True)
        return
    
    roles_to_remove = [r for r in member.roles if r != interaction.guild.default_role]
    await member.remove_roles(*roles_to_remove)
    await member.add_roles(prison_role)
    await prison_channel.set_permissions(member, read_messages=True, send_messages=True)
    
    await interaction.response.send_message(f"**تم سجن العضو {member.mention}**")
    await send_log(interaction.guild, "**سجن**", f"**العضو:** {member.mention}\\n**بواسطة:** {interaction.user.mention}", Color.dark_red())

# ==================== AUTO REPLIES ====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    guild_id = str(message.guild.id) if message.guild else None
    if guild_id and guild_id in data.get("auto_replies", {}):
        for reply in data["auto_replies"][guild_id]:
            key = reply["key"].lower()
            content = message.content.lower()
            if reply["include"]:
                if key in content:
                    await message.channel.send(reply["reply"])
            else:
                if content == key:
                    await message.channel.send(reply["reply"])
    
    await bot.process_commands(message)

# ==================== INVITE TRACKING ====================
@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    if guild_id not in data["invites"]:
        data["invites"][guild_id] = {}
    
    # Simple tracking - in production you'd compare invite counts
    # This is a simplified version

# ==================== ERROR HANDLING ====================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("**ليس لديك الصلاحية**")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("**ناقص معلومات**")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("**لم يتم العثور على العضو**")
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send("**لم يتم العثور على الرول**")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send("**لم يتم العثور على الروم**")
    else:
        print(f"**Error:** {error}")

@bot.tree.error
async def on_app_command_error(interaction: Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("**ليس لديك الصلاحية**", ephemeral=True)
    elif isinstance(error, app_commands.CommandInvokeError):
        await interaction.response.send_message(f"**خطأ:** {str(error.original)}", ephemeral=True)
    else:
        await interaction.response.send_message(f"**خطأ:** {str(error)}", ephemeral=True)

# ==================== RUN ====================
if __name__ == "__main__":
    bot.run(TOKEN)
'''

with open("/mnt/agents/output/bot.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Done! File saved successfully.")

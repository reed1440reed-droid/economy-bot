import discord
from discord.ext import commands
from discord import app_commands
import datetime

# ⚠️ ضع آيدي سيرفرك هنا عشان تتفعل الأوامر فيه فوراً وبدون انتظار
MY_GUILD = discord.Object(id=1439839910172295303) 

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. أمر الحظر (Ban)
    @app_commands.command(name="ban", description="حظر عضو من السيرفر نهائياً")
    @app_commands.describe(member="العضو المراد حظره", reason="سبب الحظر")
    @app_commands.default_permissions(ban_members=True) # الأمر يظهر فقط لمن لديه صلاحية الباند
    @app_commands.guilds(MY_GUILD) # ربط الأمر بالسيرفر للظهور السريع
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
        # حماية: منع حظر شخص رتبته أعلى أو مساوية لمنفذ الأمر
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ لا يمكنك حظر شخص رتبته أعلى أو مساوية لك!", ephemeral=True)
        
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"🔨 تم حظر {member.mention} بنجاح.\n📄 **السبب:** {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ البوت لا يملك صلاحية (أو رتبته أقل من العضو) لتنفيذ الحظر.", ephemeral=True)

    # 2. أمر الطرد (Kick)
    @app_commands.command(name="kick", description="طرد عضو من السيرفر")
    @app_commands.describe(member="العضو المراد طرده", reason="سبب الطرد")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.guilds(MY_GUILD)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ لا يمكنك طرد شخص رتبته أعلى أو مساوية لك!", ephemeral=True)
        
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"👢 تم طرد {member.mention} بنجاح.\n📄 **السبب:** {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ البوت لا يملك صلاحية لطرد هذا العضو.", ephemeral=True)

    # 3. أمر التايم اوت (Timeout)
    @app_commands.command(name="timeout", description="إسكات عضو لمدة محددة (تايم اوت)")
    @app_commands.describe(member="العضو", minutes="المدة بالدقائق", reason="السبب")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guilds(MY_GUILD)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "بدون سبب"):
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ لا يمكنك إعطاء تايم اوت لشخص رتبته أعلى أو مساوية لك!", ephemeral=True)
        
        try:
            # تحويل الدقائق إلى صيغة وقت يفهمها الديسكورد
            duration = datetime.timedelta(minutes=minutes)
            await member.timeout(duration, reason=reason)
            await interaction.response.send_message(f"⏳ تم إسكات {member.mention} لمدة **{minutes} دقيقة**.\n📄 **السبب:** {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ البوت لا يملك صلاحية إعطاء تايم اوت لهذا العضو.", ephemeral=True)

# دالة التشغيل
async def setup(bot):
    await bot.add_cog(Moderation(bot))
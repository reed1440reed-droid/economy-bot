import discord
from discord.ext import commands
from discord import app_commands
import asyncio

# ================= الإعدادات الأساسية =================
MY_GUILD = discord.Object(id=1439839910172295303) 
GUILD_ID = 1439839910172295303          # آيدي السيرفر
RESTRICT_ROLE_ID = 1518295982041731283   # ⚠️ آيدي رتبة "المعاقبين" أو "المحظورين"
TICKET_CHANNEL_ID = 1511687480951439461  # ⚠️ آيدي روم التذاكر اللي بيروح له العضو
# ======================================================

class TempBanSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tempban", description="إعطاء عضو رتبة حظر مؤقت (تقييد) وإرسال رسالة له بالخاص")
    @app_commands.describe(
        member="العضو المراد حظره مؤقتاً",
        minutes="مدة الحظر بالدقائق",
        reason="سبب الحظر"
    )
    @app_commands.default_permissions(moderate_members=True) # مخصص للإدارة فقط
    @app_commands.guilds(MY_GUILD)
    async def tempban(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
        # 1. التأكد من أن الوقت منطقي
        if minutes < 1:
            return await interaction.response.send_message("❌ يجب أن تكون المدة دقيقة واحدة على الأقل.", ephemeral=True)

        # 2. جلب رتبة الحظر من السيرفر
        restrict_role = interaction.guild.get_role(RESTRICT_ROLE_ID)
        if not restrict_role:
            return await interaction.response.send_message("❌ لم يتم العثور على رتبة الحظر! تأكد من وضع الآيدي الصحيح في الكود.", ephemeral=True)

        # 3. إعطاء الرتبة للعضو
        try:
            await member.add_roles(restrict_role, reason=f"حظر مؤقت لمدة {minutes} دقيقة. السبب: {reason}")
        except discord.Forbidden:
            return await interaction.response.send_message("❌ البوت لا يملك صلاحية لإعطاء هذه الرتبة (تأكد أن رتبة البوت أعلى من رتبة الحظر).", ephemeral=True)

        # 4. تصميم الإيمبد الخاص الذي سيُرسل للعضو
        embed = discord.Embed(
            title="⛔ إشعار حظر مؤقت",
            description=f"مرحباً بك،\nلقد تم حظرك من قبل الإدارة لمدة **{minutes} دقيقة**.\n\n📄 **السبب:** {reason}",
            color=discord.Color.red()
        )
        
        # 5. تصميم الزر الذي ينقل العضو لروم التذاكر
        view = discord.ui.View()
        # ديسكورد يدعم تحويل الروابط المباشرة إلى رومات داخل السيرفر
        ticket_url = f"https://discord.com/channels/{GUILD_ID}/{TICKET_CHANNEL_ID}"
        ticket_button = discord.ui.Button(label="📩 التوجه لروم التذاكر", style=discord.ButtonStyle.link, url=ticket_url)
        view.add_item(ticket_button)

        # 6. محاولة إرسال الرسالة في الخاص
        dm_status = "✅ وتم تنبيهه في الخاص."
        try:
            await member.send(embed=embed, view=view)
        except discord.Forbidden:
            dm_status = "⚠️ لكن الخاص لديه مغلق، لم تصله الرسالة."

        # 7. الرد على الإداري لتأكيد العملية
        await interaction.response.send_message(f"✅ تم إعطاء رتبة الحظر للعضو {member.mention} لمدة `{minutes}` دقيقة.\n{dm_status}", ephemeral=True)

        # 8. البقاء في وضع الانتظار (Sleep) حتى تنتهي المدة لسحب الرتبة
        await asyncio.sleep(minutes * 60)
        
        # 9. سحب الرتبة بعد انتهاء الوقت (إذا كانت لا تزال لديه)
        if restrict_role in member.roles:
            try:
                await member.remove_roles(restrict_role, reason="انتهاء مدة الحظر المؤقت")
                # إرسال رسالة تبشره بانتهاء الحظر (اختياري)
                try:
                    await member.send(f"🔓 لقد انتهت مدة الحظر المؤقت الخاصة بك في سيرفر **{interaction.guild.name}**. نرجو الالتزام بالقوانين.")
                except discord.Forbidden:
                    pass
            except discord.Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(TempBanSystem(bot))
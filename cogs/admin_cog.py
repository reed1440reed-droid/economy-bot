import discord
from discord.ext import commands
import sys
import time
import datetime

class AdminSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # حفظ وقت تشغيل البوت لحساب مدة العمل (Uptime)
        self.start_time = time.time()

    # 1. أمر تغيير الأفتار (صورة البوت)
    @commands.command(name="setavatar")
    @commands.is_owner()
    async def set_avatar(self, ctx):
        if not ctx.message.attachments:
            return await ctx.send("❌ يرجى إرفاق صورة مع الأمر!")
        
        attachment = ctx.message.attachments[0]
        try:
            image_bytes = await attachment.read()
            await self.bot.user.edit(avatar=image_bytes)
            await ctx.send("✅ تم تغيير صورة البوت بنجاح!")
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ حدث خطأ (قد تكون غيرت الصورة مرات كثيرة مؤخراً): {e}")

    # 2. أمر تغيير البنر (خلفية البوت)
    @commands.command(name="setbanner")
    @commands.is_owner()
    async def set_banner(self, ctx):
        if not ctx.message.attachments:
            return await ctx.send("❌ يرجى إرفاق صورة مع الأمر!")
        
        attachment = ctx.message.attachments[0]
        try:
            image_bytes = await attachment.read()
            await self.bot.user.edit(banner=image_bytes)
            await ctx.send("✅ تم تغيير بنر البوت بنجاح!")
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ حدث خطأ: {e}")

    # 3. أمر إحصائيات الكوجات والنظام
    @commands.command(name="stats")
    @commands.is_owner()
    async def stats(self, ctx):
        # حساب مدة التشغيل (Uptime)
        current_time = time.time()
        uptime_seconds = int(round(current_time - self.start_time))
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))

        # جلب الكوجات المحملة
        loaded_cogs = list(self.bot.cogs.keys())
        cogs_count = len(loaded_cogs)
        
        # حساب إجمالي الأوامر
        commands_count = len(self.bot.commands)
        slash_commands_count = len(self.bot.tree.get_commands())

        # سرعة الاستجابة
        ping = round(self.bot.latency * 1000)

        # ترتيب الرسالة في إيمبد (Embed) مرتب
        embed = discord.Embed(title="📊 إحصائيات نظام البوت", color=discord.Color.blue())
        embed.add_field(name="⏱️ مدة التشغيل", value=f"`{uptime_str}`", inline=False)
        embed.add_field(name="🏓 سرعة الاستجابة (Ping)", value=f"`{ping}ms`", inline=False)
        embed.add_field(name="📦 الكوجات المحملة", value=f"`{cogs_count} Cogs`\n{', '.join(loaded_cogs)}", inline=False)
        embed.add_field(name="⌨️ الأوامر العادية", value=f"`{commands_count}`", inline=True)
        embed.add_field(name="⚡ أوامر السلاش", value=f"`{slash_commands_count}`", inline=True)
        
        await ctx.send(embed=embed)

    # 4. أمر إعادة تشغيل البوت
    @commands.command(name="restart")
    @commands.is_owner()
    async def restart(self, ctx):
        await ctx.send("🔄 جاري إطفاء البوت لإعادة التشغيل...")
        
        # إيقاف العملية (الاستضافة ستقوم بتشغيله تلقائياً بمجرد انطفائه)
        sys.exit(0)

async def setup(bot):
    await bot.add_cog(AdminSettings(bot))
import discord
from discord.ext import commands
import aiosqlite
import random

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_user(self, user_id):
        try:
            await self.bot.db.execute("ALTER TABLE users ADD COLUMN gold INTEGER DEFAULT 0")
            await self.bot.db.execute("ALTER TABLE users ADD COLUMN job TEXT DEFAULT 'عاطل'")
            await self.bot.db.commit()
        except:
            pass 

        cursor = await self.bot.db.execute("SELECT wallet, bank, gold, job FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            await self.bot.db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            await self.bot.db.commit()
            return (0, 0, 0, 'عاطل')
        return row

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        prefixless_commands = ["كشف", "توب", "راتب", "رصيد"]
        content = message.content.strip()

        if content in prefixless_commands:
            ctx = await self.bot.get_context(message)
            ctx.command = self.bot.get_command(content)
            if ctx.command:
                await self.bot.invoke(ctx)

    # ==================== الأوامر الإبداعية ====================

    # 1. أمر الراتب (قسيمة راتب عشوائية وواقعية)
    @commands.command(name="راتب")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def salary(self, ctx):
        await self.get_user(ctx.author.id)
        
        # نظام الراتب العشوائي
        base_salary = random.randint(1500, 4500) # راتب أساسي عشوائي
        
        # مكافأة عشوائية (فرصة 35% للحصول عليها)
        has_bonus = random.randint(1, 100) <= 35
        bonus = random.randint(500, 2000) if has_bonus else 0
        
        # خصم رسوم حكومية أو بنكية (3% إلى 7%)
        tax_rate = random.uniform(0.03, 0.07)
        tax = int((base_salary + bonus) * tax_rate)
        
        # صافي الراتب
        net_salary = base_salary + bonus - tax
        
        # إضافة الراتب للمحفظة
        await self.bot.db.execute("UPDATE users SET wallet = wallet + ? WHERE user_id = ?", (net_salary, ctx.author.id))
        await self.bot.db.commit()
        
        # تصميم قسيمة الراتب
        embed = discord.Embed(title="🧾 قسيمة الراتب اليومية", color=0x000000)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        
        embed.add_field(name="الراتب الأساسي", value=f"💵 `{base_salary:,}` عملة", inline=False)
        
        if has_bonus:
            embed.add_field(name="مكافأة أداء مميز", value=f"🎁 `+{bonus:,}` عملة", inline=False)
            
        embed.add_field(name="رسوم وضرائب", value=f"📉 `-{tax:,}` عملة", inline=False)
        
        embed.add_field(name="صافي الراتب المستلم", value=f"💰 **`{net_salary:,}` عملة**", inline=False)
        
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png") # أيقونة بنكية فخمة
        embed.set_footer(text="تم إيداع المبلغ في محفظتك بنجاح ✅")
        
        await ctx.send(embed=embed)

    @salary.error
    async def salary_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(int(error.retry_after), 3600)
            minutes, seconds = divmod(remainder, 60)
            embed = discord.Embed(
                title="🛑 توقف!", 
                description=f"لقد استلمت راتبك مسبقاً يا {ctx.author.mention}.\n\n⏳ **متبقي لك:** `{hours} ساعة و {minutes} دقيقة`", 
                color=0x000000
            )
            await ctx.send(embed=embed)

    # 2. أمر توب (قائمة الأثرياء الخارقة)
    @commands.command(name="توب")
    async def top(self, ctx):
        cursor = await self.bot.db.execute("SELECT user_id, (wallet + bank) as total FROM users ORDER BY total DESC LIMIT 10")
        top_users = await cursor.fetchall()

        if not top_users:
            return await ctx.send("لا يوجد أحد في قاعدة البيانات حتى الآن!")

        embed = discord.Embed(title="🏆 قائمة فوربس لأثرياء السيرفر", description="أغنى 10 شخصيات اقتصادية:", color=0x000000)
        
        # حساب إجمالي أموال السيرفر لمعرفة نسبة ثروة الأول
        cursor_total = await self.bot.db.execute("SELECT SUM(wallet + bank) FROM users")
        server_total = await cursor_total.fetchone()
        server_total = server_total[0] if server_total[0] else 1 # لمنع القسمة على صفر

        for index, (user_id, total) in enumerate(top_users, start=1):
            user = self.bot.get_user(user_id)
            if not user:
                try:
                    user = await self.bot.fetch_user(user_id)
                except:
                    user = None
                    
            username = user.display_name if user else f"مستثمر غامض"
            
            # تنسيق الميداليات والألقاب
            if index == 1:
                percentage = (total / server_total) * 100
                prefix = f"👑 **إمبراطور الاقتصاد** | {username}"
                value = f"💎 **الثروة:** `{total:,}` عملة\n📊 يستحوذ على `{percentage:.1f}%` من أموال السيرفر!"
            elif index in [2, 3]:
                medal = "🥈" if index == 2 else "🥉"
                prefix = f"{medal} **من كبار الأثرياء** | {username}"
                value = f"💰 **الثروة:** `{total:,}` عملة"
            else:
                prefix = f"**{index}.** 💼 تاجر | {username}"
                value = f"💵 `{total:,}` عملة"

            embed.add_field(name=prefix, value=value, inline=False)

        embed.set_footer(text=f"إجمالي الأموال المتداولة في البوت: {server_total:,} عملة 🌍")
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2830/2830284.png") # أيقونة تاج وثروة
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
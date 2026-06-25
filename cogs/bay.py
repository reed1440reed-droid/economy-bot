import discord
from discord.ext import commands
import random

class Bay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.items = {
            "سيارة": 50000, "طيارة": 500000, "جزيرة": 1000000, 
            "بيت": 200000, "مستشفى": 750000, "يخت": 300000, "أسهم": 10000
        }

    # 1. أمر أسعار (تتغير يومياً)
    @commands.command(name="أسعار")
    async def prices(self, ctx):
        embed = discord.Embed(title="📊 بورصة السوق اليومية", color=0x000000)
        for item, price in self.items.items():
            # تغيير السعر بنسبة بسيطة عشوائياً
            new_price = int(price * random.uniform(0.9, 1.1))
            embed.add_field(name=item, value=f"`{new_price:,}` عملة", inline=True)
        await ctx.send(embed=embed)

    # 2. أمر شراء (بمنيو)
    @commands.command(name="شراء")
    async def buy(self, ctx):
        options = [discord.SelectOption(label=item, value=str(price)) for item, price in self.items.items()]
        select = discord.ui.Select(placeholder="اختر ما تريد شراءه...", options=options)
        
        async def callback(interaction):
            item_price = int(select.values[0])
            item_name = next(k for k, v in self.items.items() if v == item_price)
            
            cursor = await self.bot.db.execute("SELECT wallet FROM users WHERE user_id = ?", (interaction.user.id,))
            row = await cursor.fetchone()
            
            if row and row[0] >= item_price:
                await self.bot.db.execute("UPDATE users SET wallet = wallet - ? WHERE user_id = ?", (item_price, interaction.user.id))
                await self.bot.db.execute("INSERT INTO inventory (user_id, item_name) VALUES (?, ?)", (interaction.user.id, item_name))
                await self.bot.db.commit()
                await interaction.response.send_message(f"✅ تم شراء **{item_name}** بنجاح!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ رصيدك غير كافٍ!", ephemeral=True)

        select.callback = callback
        view = discord.ui.View()
        view.add_item(select)
        await ctx.send("🛒 متجر السوق:", view=view)

    # 3. أمر بيع (بمنيو لأغراض المستخدم)
    @commands.command(name="بيع")
    async def sell(self, ctx):
        cursor = await self.bot.db.execute("SELECT item_name FROM inventory WHERE user_id = ?", (ctx.author.id,))
        rows = await cursor.fetchall()
        
        if not rows:
            return await ctx.send("❌ لا تملك أي ممتلكات لبيعها!")

        options = [discord.SelectOption(label=row[0], value=row[0]) for row in rows]
        select = discord.ui.Select(placeholder="اختر الغرض لبيعه...", options=options)

        async def callback(interaction):
            item = select.values[0]
            price = int(self.items[item] * 0.7) # يبيع بـ 70% من السعر
            await self.bot.db.execute("DELETE FROM inventory WHERE user_id = ? AND item_name = ? LIMIT 1", (interaction.user.id, item))
            await self.bot.db.execute("UPDATE users SET wallet = wallet + ? WHERE user_id = ?", (price, interaction.user.id))
            await self.bot.db.commit()
            await interaction.response.send_message(f"✅ تم بيع **{item}** مقابل **{price}** عملة.", ephemeral=True)

        select.callback = callback
        view = discord.ui.View()
        view.add_item(select)
        await ctx.send("💰 ماذا تريد أن تبيع اليوم؟", view=view)

    # 4. أمر هدية
    @commands.command(name="هدية")
    @commands.cooldown(1, 43200, commands.BucketType.user) # 12 ساعة
    async def gift(self, ctx, member: discord.Member, amount: int):
        if amount <= 0: return await ctx.send("❌ المبلغ غير صحيح.")
        # خصم من المرسل وإضافة للمستلم (نفس منطق التحويل سابقاً)
        await self.bot.db.execute("UPDATE users SET wallet = wallet - ? WHERE user_id = ?", (amount, ctx.author.id))
        await self.bot.db.execute("UPDATE users SET wallet = wallet + ? WHERE user_id = ?", (amount, member.id))
        await self.bot.db.commit()
        await ctx.send(f"🎁 أرسل {ctx.author.mention} هدية بقيمة **{amount}** عملة إلى {member.mention}!")

async def setup(bot):
    await bot.add_cog(Bay(bot))
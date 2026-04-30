import discord
import os
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from flask import Flask
from threading import Thread

# --- ระบบ Web Server สำหรับ UptimeRobot ---
app = Flask('')
@app.route('/')
def home():
    return "I'm alive!"

def run_web():
    # ดึงค่า Port จาก Render (สำคัญมาก)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ================= ตั้งค่า ID ห้อง และ คำห้ามใช้ =================
TOKEN = os.getenv('DISCORD_TOKEN')
SETUP_CHANNEL_ID = 1491787842790096997
LOG_CHANNEL_ID = 1499440045743149147

BANNED_WORDS = ["ขี้เกรียจ", "เงี่ยน", "ไม่อยากมา", "เบื่อ", "เซ็ง", "กินเหล้า"]

class LeaveModal(discord.ui.Modal, title='แบบฟอร์มการแจ้งลา'):
    leave_type = discord.ui.TextInput(label='ประเภทการลา', placeholder='ระบุประเภทการลาของคุณ...', required=True)
    reason = discord.ui.TextInput(label='สาเหตุการลา', style=discord.TextStyle.long, placeholder='อธิบายรายละเอียดการลา...', required=True, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        if any(word in self.reason.value for word in BANNED_WORDS):
            await interaction.response.send_message("❌ **ลาดีๆสัสเดี๋ยวตบหน้าหรอก** ไปตายไป", ephemeral=True)
            return

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="📋 รายงานการแจ้งลาใหม่", color=discord.Color.red(), timestamp=datetime.now())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="👤 ผู้แจ้งลา", value=f"{interaction.user.mention}", inline=False)
            embed.add_field(name="📂 ประเภท", value=f"```\n{self.leave_type.value}\n```", inline=True)
            embed.add_field(name="📝 สาเหตุ", value=f"```\n{self.reason.value}\n```", inline=False)
            await log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ ส่งใบลาเรียบร้อยแล้ว!", ephemeral=True)

class LeaveView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label='ลาทำ💩อะไร', style=discord.ButtonStyle.danger, custom_id='persistent_leave_button')
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LeaveModal())

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        self.add_view(LeaveView())
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        await self.tree.sync()

# --- เริ่มการรันบอท ---
if __name__ == "__main__":
    keep_alive() # เปิดเว็บเซิร์ฟเวอร์
    bot = MyBot()

    @bot.tree.command(name="setup_leave", description="สร้างปุ่มแจ้งลา")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_leave(interaction: discord.Interaction):
        if interaction.channel_id != SETUP_CHANNEL_ID:
            await interaction.response.send_message(f"❌ กรุณาใช้ในห้อง <#{SETUP_CHANNEL_ID}>", ephemeral=True)
            return
        embed = discord.Embed(title="📝 ระบบเเจ้งลา", description="กรุณากดปุ่มด้านล่าง", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=LeaveView())

    bot.run(TOKEN)

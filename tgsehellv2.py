import telebot
import subprocess
import os
import time

# ███████ SENİN BİLGİLERİN ███████
TOKEN = '8305734741:AAH1MPoGdcI_DG3_dmMfs5ICZlOEvZo3g8s'
CHAT_ID = 7432353263                     # sadece sen komut gönderebilesin
# █████████████████████████████

bot = telebot.TeleBot(TOKEN)

# YENİ: En son bulunulan dizini kaydetmek için dosya
WORKING_DIR_FILE = "/tmp/telebot_last_dir"

# YENİ: Bot başladığında en son dizini yükle
if os.path.exists(WORKING_DIR_FILE):
    with open(WORKING_DIR_FILE, "r") as f:
        try:
            os.chdir(f.read().strip())
            print(f"En son dizine geçildi: {os.getcwd()}")
        except:
            print("En son dizin bulunamadı, ev dizininde başlıyor...")
else:
    os.chdir(os.path.expanduser("~"))  # ilk açılışta ev dizini

def get_public_ip():
    try:
        return subprocess.check_output("curl -s ifconfig.me", shell=True).decode().strip()
    except:
        return "IP alınamadı"

@bot.message_handler(func=lambda m: m.chat.id == CHAT_ID)
def commander(message):
    cmd = message.text.strip()

    if not cmd:
        return

    # port açma özel komutu (değişmedi)
    if cmd.startswith("port_ac "):
        try:
            port = cmd.split()[1]
            os.system(f'sudo ufw allow {port} >/dev/null 2>&1')
            os.system('sudo ufw reload >/dev/null 2>&1')
            ip = get_public_ip()
            bot.reply_to(message, f"Port {port} açıldı!\nIP:Port → {ip}:{port}")
        except:
            bot.reply_to(message, "Port açma hatası")
        return

    # YENİ: cd komutu için özel işlem
    if cmd.startswith("cd "):
        try:
            yol = cmd[3:].strip()
            # ~ işareti desteği
            yol = os.path.expanduser(yol)
            # boş cd → ev dizinine git
            if not yol or yol == "~":
                os.chdir(os.path.expanduser("~"))
            else:
                os.chdir(yol)
            # Yeni dizini kaydet
            with open(WORKING_DIR_FILE, "w") as f:
                f.write(os.getcwd())
            bot.reply_to(message, f"✓ Dizin değiştirildi:\n`{os.getcwd()}`", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"cd hatası: {e}")
        return

    # Mevcut dizini her komutta ortam değişkeni olarak veriyoruz
    env = os.environ.copy()
    env['PWD'] = os.getcwd()

    # normal komutlar
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,  # biraz artırdım, uzun işler için
            cwd=os.getcwd(),   # YENİ: komutlar şu anki dizinde çalışsın
            env=env
        )
        output = proc.stdout + proc.stderr
        if not output.strip():
            output = "Komut çalıştı, çıktı yok"
        if len(output) > 4000:
            output = output[:4000] + "\n\n... (devamı kesildi, çok uzun)"
        
        # pwd yazarsa anlık dizini göster
        if cmd.strip() in ["pwd", "pwd -P"]:
            output = os.getcwd()

        bot.reply_to(message, f"```{output}```", parse_mode='Markdown')
    except subprocess.TimeoutExpired:
        bot.reply_to(message, "⏰ Komut zaman aşımına uğradı (60 sn)")
    except Exception as e:
        bot.reply_to(message, f"Hata: {e}")

print("Bot aktif – sadece sen komut gönderebilirsin")
print(f"Başlangıç dizini: {os.getcwd()}")

while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print("Polling yeniden başlatılıyor:", e)
        time.sleep(5)
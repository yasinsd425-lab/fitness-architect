import streamlit as st
import json
import os
import pandas as pd
import time
from datetime import datetime, timedelta
from gtts import gTTS
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
# نام دقیق شیتی که در گوگل شیت ساختی
SHEET_NAME = "gym_database" 
THEME_IMG_URL = "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1470&auto=format&fit=crop"

# --- CLOUD DATABASE FUNCTIONS (GOOGLE SHEETS) ---
def get_google_sheet_client():
    # اتصال با استفاده از سکرت‌های استریم‌لیت
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def load_db():
    """دانلود دیتابیس از گوگل شیت"""
    try:
        client = get_google_sheet_client()
        sheet = client.open(SHEET_NAME).sheet1
        # تمام دیتا در سلول A1 ذخیره می‌شود
        data = sheet.acell('A1').value
        if not data:
            return {}
        return json.loads(data)
    except Exception as e:
        # اگر خطا داد (مثلا شیت خالی بود) دیکشنری خالی برگردان
        return {}

def save_db(data):
    """آپلود دیتابیس به گوگل شیت"""
    try:
        client = get_google_sheet_client()
        sheet = client.open(SHEET_NAME).sheet1
        # تبدیل دیتا به متن و ذخیره در A1
        json_str = json.dumps(data)
        sheet.update_acell('A1', json_str)
    except Exception as e:
        st.error(f"خطا در ذخیره سازی ابری: {e}")

# --- DETAILED EXERCISE LIBRARY ---
EXERCISE_LIB = {
    # --- WARM UP ---
    "WarmUp_Upper": {
        "name": "گرم‌کردن تخصصی بالاتنه", 
        "desc": """
        <div style='background-color: #2c3e50; padding: 15px; border-radius: 10px; border-left: 5px solid #3498db;'>
        <h4>🔥 مراحل گرم کردن:</h4>
        <ul>
            <li><b>چرخش بازوها:</b> ۱۰ تکرار به جلو، ۱۰ تکرار به عقب (دایره‌های بزرگ).</li>
            <li><b>چرخش مچ دست:</b> ۳۰ ثانیه در هم قفل کنید و بچرخانید.</li>
            <li><b>پروانه (Jumping Jacks):</b> ۳۰ ثانیه برای افزایش ضربان قلب.</li>
        </ul>
        <p style='color: #f39c12;'>⚠️ نکته: بدون گرم کردن شانه، ریسک آسیب در پرس‌ها بالاست.</p>
        </div>
        """,
        "voice": "پنج دقیقه گرم کردن حیاتی. بازوها رو کامل بچرخون. مچ دستت رو گرم کن."
    },
    "WarmUp_Lower": {
        "name": "گرم‌کردن تخصصی پایین‌تنه", 
        "desc": """
        <div style='background-color: #2c3e50; padding: 15px; border-radius: 10px; border-left: 5px solid #e67e22;'>
        <h4>🔥 مراحل گرم کردن:</h4>
        <ul>
            <li><b>اسکوات وزن بدن:</b> ۱۵ تکرار سریع و نیمه.</li>
            <li><b>کشش کشاله ران:</b> مدل پروانه‌ای بنشینید.</li>
            <li><b>زانو بلند درجا:</b> ۳۰ ثانیه.</li>
        </ul>
        </div>
        """,
        "voice": "گرم کردن پایین تنه. اسکوات سریع بزن بدون وزنه."
    },
    
    # --- UPPER BODY ---
    "Floor Press": {
        "name": "پرس سینه روی زمین (Floor Press)", 
        "desc": """
        <div style='background-color: #1e272e; padding: 15px; border-radius: 10px; border: 1px solid #4ecdc4;'>
        <p>✅ <b>نحوه اجرا:</b> به پشت دراز بکشید، زانوها خم. دمبل‌ها را بالای سینه پرس کنید.</p>
        <p style='color: #ff6b6b;'>⛔ <b>هشدار ایمنی:</b> آرنج‌ها را ۹۰ درجه باز نکنید (فشار روی شانه). زاویه ۴۵ درجه با بدن صحیح است.</p>
        <p>💡 <b>تکنیک:</b> وقتی آرنج به زمین خورد، ۱ ثانیه مکث کنید تا فشار از روی عضله برداشته شود، سپس انفجاری پرس کنید.</p>
        </div>
        """,
        "voice": "پرس سینه روی زمین. آرنجت رو به بدنت نزدیک کن. زاویه چهل و پنج درجه."
    },
    "One Arm Row": {
        "name": "زیربغل دمبل تک‌خم", 
        "desc": """
        <div style='background-color: #1e272e; padding: 15px; border-radius: 10px; border: 1px solid #4ecdc4;'>
        <p>✅ <b>نحوه اجرا:</b> یک دست و زانو روی نیمکت. کمر کاملاً صاف (مثل میز).</p>
        <p style='color: #ff6b6b;'>⛔ <b>هشدار ایمنی:</b> قوز کردن ممنوع! اگر کمر گرد شود، به دیسک فشار می‌آید.</p>
        <p>💡 <b>تکنیک:</b> دمبل را به سمت جیب شلوار بکشید (عقب)، نه به سمت سینه (بالا).</p>
        </div>
        """,
        "voice": "زیربغل تک خم. کمرت رو اصلا قوز نکن. دمبل رو بکش سمت لگنت."
    },
    "Overhead Press": {
        "name": "پرس سرشانه ایستاده", 
        "desc": """
        <div style='background-color: #1e272e; padding: 15px; border-radius: 10px; border: 1px solid #4ecdc4;'>
        <p>✅ <b>نحوه اجرا:</b> دمبل‌ها کنار گوش. پرس به سمت سقف.</p>
        <p style='color: #ff6b6b;'>⛔ <b>هشدار ایمنی:</b> موقع بالا بردن، کمر را قوس ندهید. شکم را سفت نگه دارید.</p>
        </div>
        """,
        "voice": "پرس سرشانه. شکمت رو سفت کن."
    },
    "Bicep Curl": {
        "name": "جلوبازو ایستاده", 
        "desc": """
        <div style='background-color: #1e272e; padding: 15px; border-radius: 10px; border: 1px solid #4ecdc4;'>
        <p>✅ <b>نحوه اجرا:</b> آرنج‌ها چسبیده به پهلو. فقط ساعد بالا بیاید.</p>
        <p style='color: #ff6b6b;'>⛔ <b>اشتباه رایج:</b> تاب دادن کمر برای بالا آوردن وزنه تقلب است.</p>
        </div>
        """,
        "voice": "جلوبازو. آرنجت رو تکون نده."
    },
    "Tricep Ext": {
        "name": "پشت بازو جفت دست", 
        "desc": """
        <div style='background-color: #1e272e; padding: 15px; border-radius: 10px; border: 1px solid #4ecdc4;'>
        <p>✅ <b>نحوه اجرا:</b> دمبل پشت سر. آرنج‌ها رو به سقف و ثابت.</p>
        </div>
        """,
        "voice": "پشت بازو. آرنجت رو به سقف باشه."
    },

    # --- LOWER BODY ---
    "Goblet Squat": {
        "name": "گابلت اسکوات", 
        "desc": """
        <div style='background-color: #1e272e; padding: 15px; border-radius: 10px; border: 1px solid #ffeaa7;'>
        <p>✅ <b>نحوه اجرا:</b> دمبل چسبیده به سینه. پاها کمی بازتر از عرض شانه.</p>
        <p style='color: #ff6b6b;'>⛔ <b>هشدار ایمنی:</b> زانوها نباید به داخل متمایل شوند. سینه را بالا نگه دارید.</p>
        <p>💡 <b>تکنیک:</b> تصور کنید می‌خواهید روی صندلی بنشینید. وزن روی پاشنه پا.</p>
        </div>
        """,
        "voice": "گابلت اسکوات. سینه رو بده جلو. سنگینی روی پاشنه."
    },
    "RDL": {
        "name": "ددلیفت رومانیایی", 
        "desc": """
        <div style='background-color: #1e272e; padding: 15px; border-radius: 10px; border: 1px solid #ffeaa7;'>
        <p>✅ <b>نحوه اجرا:</b> زانو کمی خم و قفل. خم شدن از لگن با کمر صاف.</p>
        <p style='color: #ff6b6b;'>⛔ <b>خطرناکترین حرکت برای کمر اگر قوز کنید!</b> نگاه به جلو پایین باشد.</p>
        <p>💡 <b>تکنیک:</b> باسن را به عقب هل دهید تا کشش شدیدی پشت ران حس کنید.</p>
        </div>
        """,
        "voice": "ددلیفت رومانیایی. قوز نکن. باسن رو بده عقب."
    },
    "Lunges": {
        "name": "لانژ (Lunges)", 
        "desc": "✅ **اجرا:** گام به عقب. هر دو زانو ۹۰ درجه. تنه صاف.", 
        "voice": "لانژ. زانوی پای عقب رو کنترل شده ببر پایین."
    },

    # --- CORE ---
    "Plank": {
        "name": "پلانک (Plank)", 
        "desc": "✅ **اجرا:** بدن مثل خط‌کش. باسن بالا نباشد. شکم منقبض.", 
        "voice": "پلانک. شکم رو بده تو. نفس بکش."
    },
    "Shadow Boxing": {
        "name": "بوکس سرعتی", 
        "desc": "✅ **اجرا:** گارد بوکس. ضربات مستقیم پی‌درپی. رقص پا.", 
        "voice": "بوکس سرعتی. نفس بگیر."
    }
}

# --- HELPERS ---
def autoplay_audio(text):
    try:
        tts = gTTS(text=text, lang='fa')
        filename = "temp_audio.mp3"
        tts.save(filename)
        with open(filename, "rb") as f:
            audio_bytes = f.read()
        b64 = base64.b64encode(audio_bytes).decode()
        md = f"""<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>"""
        st.markdown(md, unsafe_allow_html=True)
    except: pass

def get_weekly_status(history, total_days_in_plan):
    today = datetime.now().date()
    # اگر تاریخ عضویت به فرمت رشته است، تبدیل به تاریخ
    if isinstance(total_days_in_plan, str):
        try:
            start_date = datetime.strptime(total_days_in_plan, "%Y-%m-%d").date()
        except:
            start_date = today # فال‌بک
    else:
        start_date = total_days_in_plan

    days_passed = (today - start_date).days
    current_week = (days_passed // 7) + 1
    week_start_day = start_date + timedelta(weeks=current_week-1)

    completed_this_week = []
    for log in history:
        try:
            log_date = datetime.strptime(log['date'], "%Y-%m-%d").date()
            if log_date >= week_start_day:
                day_name = log.get('day', log.get('plan'))
                if day_name: completed_this_week.append(day_name)
        except: continue
    return current_week, completed_this_week

def prepare_export_data(history):
    """آماده سازی دیتا برای خروجی مربی با جزییات کامل"""
    export_list = []
    for log in history:
        details = ""
        if 'details' in log:
            for ex, w in log['details'].items():
                details += f"{ex}: {w}kg | "
        
        row = {
            "تاریخ": log.get('date'),
            "برنامه": log.get('day'),
            "مدت زمان (دقیقه)": log.get('duration_min', 'نامشخص'),
            "وزن بدن": log.get('user_weight'),
            "شرح حرکات و وزنه‌ها": details
        }
        export_list.append(row)
    return pd.DataFrame(export_list)

# --- LOGIC ---
def generate_program_structure(gender, goal, level):
    reps_c = "12-15" if goal == "کاهش وزن" else "8-10"
    rest_t = 45 if goal == "کاهش وزن" else 90
    plan = {
        "Day 1 (Upper)": ["WarmUp_Upper", "Floor Press", "One Arm Row", "Overhead Press", "Bicep Curl", "Tricep Ext"],
        "Day 2 (Lower)": ["WarmUp_Lower", "Goblet Squat", "RDL", "Lunges", "Plank"],
        "Day 3 (Full)": ["WarmUp_Upper", "Shadow Boxing", "Goblet Squat", "Floor Press", "Plank"]
    }
    structured_plan = {}
    for day, exercises in plan.items():
        day_exs = []
        for ex_key in exercises:
            day_exs.append({
                "id": ex_key,
                "sets": 3,
                "reps": reps_c if "WarmUp" not in ex_key and "Plank" not in ex_key else "Time",
                "rest": rest_t if "WarmUp" not in ex_key else 0
            })
        structured_plan[day] = day_exs
    return structured_plan

def init_user(username, password, gender, goal, level):
    db = load_db()
    if username in db: return False, "نام کاربری تکراری است"
    prog = generate_program_structure(gender, goal, level)
    weights = {}
    for day, exs in prog.items():
        for ex in exs:
            eid = ex['id']
            if eid not in weights:
                if "Squat" in eid or "RDL" in eid: w = 10
                elif "Press" in eid: w = 8 if gender == "آقا" else 4
                else: w = 0
                weights[eid] = w

    db[username] = {
        "password": password,
        "profile": {"gender": gender, "goal": goal, "level": level, "weight": 0, "height": 0, "joined": str(datetime.now().date())},
        "program": prog,
        "weights": weights,
        "history": []
    }
    save_db(db)
    return True, "خوش آمدید"

# --- UI SETUP ---
st.set_page_config(page_title="Gym Architect Pro", page_icon="💪", layout="wide")

st.markdown(f"""
<style>
.stApp {{
    background-image: linear_gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.95)), url("{THEME_IMG_URL}");
    background-size: cover;
    background-attachment: fixed;
}}
h1, h2, h3, h4 {{ color: #ffffff !important; font-family: 'Tahoma', sans-serif; }}
p, div, label, li {{ color: #ecf0f1 !important; font-size: 16px; }}
.stMetric {{
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 10px;
    text-align: center;
}}
/* Timer Style */
.timer-box {{
    border: 4px solid #f1c40f;
    border-radius: 50%;
    width: 150px;
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
    background-color: rgba(0,0,0,0.5);
    box-shadow: 0 0 20px rgba(241, 196, 15, 0.5);
}}
.timer-text {{
    font-size: 60px;
    font-weight: bold;
    color: #f1c40f;
}}
/* Session Timer */
.session-timer {{
    position: fixed;
    top: 60px;
    right: 20px;
    background-color: rgba(46, 204, 113, 0.2);
    border: 1px solid #2ecc71;
    padding: 5px 15px;
    border-radius: 20px;
    color: #2ecc71;
    z-index: 100;
}}
</style>
""", unsafe_allow_html=True)

# --- APP LOGIC ---
if 'user' not in st.session_state: st.session_state['user'] = None

if not st.session_state['user']:
    st.title("🏗️ Gym Architect Pro (Cloud)")
    t1, t2 = st.tabs(["ورود", "ثبت نام"])
    with t1:
        u = st.text_input("نام کاربری")
        p = st.text_input("رمز عبور", type="password")
        if st.button("ورود"):
            db = load_db()
            if u in db and db[u]['password'] == p:
                st.session_state['user'] = u
                st.rerun()
            else: st.error("اطلاعات نادرست یا کاربر یافت نشد")
    with t2:
        u_n = st.text_input("نام کاربری جدید")
        p_n = st.text_input("رمز عبور جدید", type="password")
        c1, c2, c3 = st.columns(3)
        g = c1.selectbox("جنسیت", ["آقا", "خانم"])
        gl = c2.selectbox("هدف", ["کاهش وزن", "عضله سازی"])
        lv = c3.selectbox("سطح", ["مبتدی", "متوسط"])
        if st.button("ثبت نام"):
            ok, msg = init_user(u_n, p_n, g, gl, lv)
            if ok: st.success(msg)
            else: st.error(msg)
    st.stop()

# --- DASHBOARD ---
user = st.session_state['user']
db = load_db()
udata = db[user]

# SIDEBAR
with st.sidebar:
    st.title(f"پروفایل {user}")
    st.markdown("### 🎧 موزیک انرژی")
    st.markdown("""<iframe style="border-radius:12px" src="http://googleusercontent.com/spotify.com/3" width="100%" height="80" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>""", unsafe_allow_html=True)
    
    st.markdown("### 📊 BMI")
    w = st.number_input("وزن (kg)", value=float(udata['profile']['weight']))
    h = st.number_input("قد (cm)", value=float(udata['profile']['height']))
    if st.button("آپدیت وزن"):
        udata['profile']['weight'] = w
        udata['profile']['height'] = h
        save_db(db)
        st.rerun()
    if w > 0 and h > 0:
        bmi = w / ((h/100)**2)
        pos = min(max((bmi - 15) / 20 * 100, 0), 100)
        st.markdown(f"""
            <div style="width: 100%; background: linear-gradient(to right, #3498db, #2ecc71, #f1c40f, #e74c3c); height: 10px; border-radius: 5px; position: relative; margin-top: 10px;">
                <div style="position: absolute; left: {pos}%; top: -5px; width: 5px; height: 20px; background: white; border: 1px solid black;"></div>
            </div>
            <p style='text-align: center; margin-top: 5px;'>BMI: {bmi:.1f}</p>
        """, unsafe_allow_html=True)
    
    if st.button("خروج"):
        st.session_state['user'] = None
        st.rerun()

# TABS
tab_plan, tab_gym, tab_report = st.tabs(["📅 برنامه و تقویم", "🏋️ اتاق تمرین", "📈 گزارش و مربی"])

# --- TAB 1: WEEKLY PLAN ---
with tab_plan:
    curr_week, completed_days = get_weekly_status(udata['history'], udata['profile']['joined'])
    st.header(f"هفته {curr_week} از دوره تمرینی")
    
    days = list(udata['program'].keys())
    cols = st.columns(len(days))
    for i, day in enumerate(days):
        done = day in completed_days
        color = "#2ecc71" if done else "#34495e"
        icon = "✅ انجام شده" if done else "⬜ تمرین امروز؟"
        with cols[i]:
            st.markdown(f"<div style='background:{color}; padding:10px; border-radius:5px; text-align:center; color:white;'>{day}<br>{icon}</div>", unsafe_allow_html=True)
            with st.expander("مشاهده کامل حرکات"):
                for ex in udata['program'][day]:
                    lib = EXERCISE_LIB[ex['id']]
                    st.markdown(f"### {lib['name']}")
                    st.markdown(lib['desc'], unsafe_allow_html=True) # HTML Render
                    st.markdown("---")

# --- TAB 2: WORKOUT ROOM ---
with tab_gym:
    st.header("اتاق تمرین هوشمند")
    
    selected_day = st.selectbox("برنامه امروز:", list(udata['program'].keys()))
    
    if st.button("🚀 شروع جلسه تمرینی"):
        st.session_state['active'] = True
        st.session_state['day'] = selected_day
        st.session_state['idx'] = 0
        st.session_state['start_time'] = time.time() # Start Session Timer
        st.session_state['session_weights'] = {} # Track weights for this session
        st.rerun()
        
    if st.session_state.get('active'):
        # Session Timer Display
        elapsed = int(time.time() - st.session_state['start_time'])
        mins, secs = divmod(elapsed, 60)
        # JS for live update
        start_ts = st.session_state['start_time'] * 1000
        st.markdown(f"""
        <div id="live_timer" class="session-timer">00:00</div>
        <script>
        function updateTimer() {{
            var start = {start_ts};
            var now = new Date().getTime();
            var diff = Math.floor((now - start) / 1000);
            var m = Math.floor(diff / 60);
            var s = diff % 60;
            m = m < 10 ? "0" + m : m;
            s = s < 10 ? "0" + s : s;
            document.getElementById("live_timer").innerHTML = "⏱️ " + m + ":" + s;
        }}
        setInterval(updateTimer, 1000);
        </script>
        """, unsafe_allow_html=True)
        
        day_plan = udata['program'][st.session_state['day']]
        idx = st.session_state['idx']
        
        if idx < len(day_plan):
            ex_conf = day_plan[idx]
            lib = EXERCISE_LIB[ex_conf['id']]
            
            # Autoplay only once
            if f"p_{idx}" not in st.session_state:
                autoplay_audio(lib['voice'])
                st.session_state[f"p_{idx}"] = True
            
            # Layout
            st.markdown(f"## {idx+1}. {lib['name']}")
            st.markdown(lib['desc'], unsafe_allow_html=True) # Detailed Description
            
            c1, c2 = st.columns([1, 1])
            with c1:
                rec_w = udata['weights'].get(ex_conf['id'], 0)
                st.info(f"📊 **هدف:** {ex_conf['sets']} ست | {ex_conf['reps']} تکرار")
                st.metric("وزن پیشنهادی سیستم", f"{rec_w} kg")
                
                # Feedback
                fb = st.radio("فشار حرکت:", ["سبک", "مناسب", "سنگین"], horizontal=True, key=f"f_{idx}")

            with c2:
                # Graphical Rest Timer
                rest_t = ex_conf['rest']
                st.write("") # Spacer
                if rest_t > 0:
                    if st.button("⏳ شروع استراحت"):
                        ph = st.empty()
                        for s in range(rest_t, -1, -1):
                            ph.markdown(f"""
                                <div class="timer-box">
                                    <span class="timer-text">{s}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            time.sleep(1)
                        ph.markdown("<h2 style='text-align:center; color:#2ecc71;'>حرکت کن!</h2>", unsafe_allow_html=True)
                        st.balloons()
                else:
                    st.warning("این حرکت استراحت ندارد (سوپرست یا گرم کردن)")
            
            st.markdown("---")
            if st.button("✅ ثبت و بعدی", use_container_width=True):
                # Save Weight Data for Report
                st.session_state['session_weights'][lib['name']] = rec_w
                
                # Logic for Next Weight
                if fb == "سبک": udata['weights'][ex_conf['id']] += 1
                elif fb == "سنگین" and udata['weights'][ex_conf['id']] > 0: udata['weights'][ex_conf['id']] -= 1
                save_db(db)
                
                st.session_state['idx'] += 1
                st.rerun()
        else:
            # End of Session
            total_time = int((time.time() - st.session_state['start_time']) / 60)
            st.success(f"🎉 پایان تمرین! مدت زمان: {total_time} دقیقه")
            
            if st.button("ذخیره نهایی در کارنامه"):
                log_entry = {
                    "date": str(datetime.now().date()),
                    "day": st.session_state['day'],
                    "duration_min": total_time,
                    "user_weight": udata['profile']['weight'],
                    "details": st.session_state['session_weights'] # Log exact weights used
                }
                udata['history'].append(log_entry)
                save_db(db)
                
                # Cleanup
                st.session_state['active'] = False
                st.rerun()

# --- TAB 3: REPORTS ---
with tab_report:
    st.header("گزارش حرفه‌ای (مخصوص مربی)")
    
    if udata['history']:
        # Prepare Dataframe
        df = prepare_export_data(udata['history'])
        
        st.write("این فایل شامل جزئیات کامل (وزن هر حرکت + مدت زمان) است:")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 دانلود خروجی کامل (Excel/CSV)", csv, "gym_report_full.csv", "text/csv")
        
        st.markdown("### تاریخچه اخیر")
        st.dataframe(df.tail(5)) # Show last 5 sessions
    else:
        st.info("هنوز تمرینی ثبت نشده است.")

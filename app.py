import os
import streamlit as st
import requests
import time
from io import BytesIO

st.set_page_config(page_title="TECH BIT 3D - Video Generator", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    html, body, .main { background-color: #0f172a; color: #f8fafc; direction: rtl; }
    h1 { color: #38bdf8; font-family: 'Segoe UI', Tahoma; }
    .stButton>button { background-image: linear-gradient(to right, #0284c7, #3b82f6); color: white; }
    .stTextInput>div>input { direction: ltr; }
    .stTextArea>div>textarea { direction: rtl; }
    .stSlider>div>div>div { direction: ltr; }
    </style>
""", unsafe_allow_html=True)

st.title("🎬 TECH BIT 3D Studio")
st.subheader("منصة توليد الفيديو الذكي عبر OpenRouter API")

env_api_key = os.getenv("OPENROUTER_API_KEY", "")

with st.sidebar:
    st.header("🎛️ Agent Studio")
    st.markdown(
        """
        منصة استوديو TECH BIT تمنحك إعدادات جاهزة، خيارات دقة متقدمة، واستخدام مفتاح بيئة آمن.
        يمكنك ضبط القالب والخيارات من هنا قبل بدء التوليد.
        """
    )
    st.info("يمكنك تعيين OPENROUTER_API_KEY في بيئتك لتجنب إدخال المفتاح يدويًا.")
    prompt_presets = {
        "اختر قالبًا": None,
        "مدينة مستقبلية" : "A cinematic futuristic cityscape in neon blue and amber lighting, featuring a stylized 3D cartoon character called Tech Bit walking through a glowing street.",
        "استوديو إنتاج" : "A cinematic animation inside a high-tech production studio, featuring a stylized 3D cartoon character interacting with holographic screens and robots.",
        "مغامرة الفضاء" : "A cinematic space adventure with Tech Bit flying through a luminous alien city with floating vehicles, 4k resolution and dramatic lighting.",
    }
    preset_choice = st.selectbox("اختر قالبًا جاهزًا:", list(prompt_presets.keys()))
    st.markdown("---")
    st.markdown("### إعدادات إضافية")
    use_worker = st.checkbox("استخدام عامل خلفي (RQ/Redis)", value=False)
    st.markdown("- مدة أطول تدعم ملخصات فيديو أكبر.")
    st.markdown("- إذا كان لديك Redis وRQ، يمكنك تمكين المعالجة الخلفية لاحقًا.")

api_input = st.text_input(
    "مفتاح واجهة برمجة التطبيقات (OpenRouter API Key):",
    type="password",
    placeholder="أدخل مفتاح OpenRouter أو اضبط OPENROUTER_API_KEY في البيئة",
)
api_key = api_input.strip() if api_input else env_api_key
if not api_input and env_api_key:
    st.success("✅ يتم استخدام المفتاح من متغير البيئة OPENROUTER_API_KEY.")

model_option = st.selectbox("اختر نموذج توليد الفيديو الاستراتيجي:", [
    "google/veo-3.1-lite",
    "xai/grok-imagine-video",
    "kuaishou/kling-v3.0-standard",
])

default_prompt = (
    "A cinematic, stylized 3D cartoon character named 'Tech Bit' walking forward on a glowing neon blue pathway, "
    "transitioning from a dimly lit startup garage with holographic blueprints on the left into an ultra-modern futuristic "
    "tech metropolis with giant 3D printers, Pixar-style, warm amber and neon blue lighting, 4k resolution."
)
if prompt_presets.get(preset_choice):
    default_prompt = prompt_presets[preset_choice]

prompt_text = st.text_area("أمر توليد المشهد السينمائي (Prompt):", value=default_prompt, height=160)

output_name = st.text_input("اسم ملف الفيديو النهائي:", value="techbit_video")

col1, col2 = st.columns(2)
with col1:
    duration = st.slider("مدة الفيديو (ثواني):", 1, 30, 7)
    aspect_ratio = st.selectbox("نسبة العرض إلى الارتفاع:", ["16:9", "9:16", "1:1"])
with col2:
    resolution = st.selectbox("دقة الفيديو:", ["480p", "720p", "1080p"])
    generate_audio = st.checkbox("تضمين صوت (إن وُجد)", value=False)

STATUS_POLL_ATTEMPTS = st.session_state.get("poll_attempts", 60)
POLL_INTERVAL = st.session_state.get("poll_interval", 5)


def try_post_videos(url, headers, payload):
    try:
        return requests.post(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException:
        return None


def normalize_polling_url(raw, base="https://openrouter.ai"):
    if not raw:
        return None
    if raw.startswith("http"):
        return raw
    return base.rstrip("/") + "/" + raw.lstrip("/")


def download_bytes(url, headers=None):
    try:
        with requests.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            buf = BytesIO()
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    buf.write(chunk)
            buf.seek(0)
            return buf
    except requests.RequestException:
        return None


if st.button("🚀 ابدأ توليد فيديو TECH BIT"):
    if not api_key:
        st.error("⚠️ من فضلك أدخل مفتاح OpenRouter API الخاص بك أولاً.")
    else:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model_option,
            "prompt": prompt_text,
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "generate_audio": generate_audio,
        }

        status_box = st.empty()
        progress = st.progress(0)

        with st.spinner("⏳ يتم الآن إرسال المشهد إلى سيرفرات التوليد..."):
            response = try_post_videos("https://openrouter.ai/api/v1/videos", headers, payload) or \
                       try_post_videos("https://openrouter.ai/v1/videos", headers, payload)

            if response is None:
                st.error("❌ تعذر الاتصال بخوادم OpenRouter. تحقق من الشبكة أو عنوان الـ API.")
            elif response.status_code not in (200, 201):
                st.error(f"❌ خطأ من OpenRouter API: {response.status_code} — {response.text}")
            else:
                job_data = response.json()
                job_id = job_data.get("id") or job_data.get("job_id")
                polling_url = job_data.get("polling_url") or job_data.get("status_url")
                if not polling_url and job_id:
                    polling_url = f"/api/v1/videos/{job_id}"

                polling_url = normalize_polling_url(polling_url)
                st.info(f"✅ تم إرسال المهمة بنجاح! رقم المعرف: {job_id}")

                if use_worker:
                    st.info("تم وضع المهمة في قائمة الانتظار. (ملاحظة: عامل RQ مطلوب لمعالجة الخلفية)")
                    st.write("راجع README لتشغيل العامل الخلفي أو استخدم الخيار المتزامن.")
                else:
                    final_url = None
                    for i in range(STATUS_POLL_ATTEMPTS):
                        try:
                            status_res = requests.get(polling_url, headers=headers, timeout=30)
                        except requests.RequestException as e:
                            status_box.text(f"⚠️ فشل في استعلام الحالة: {e} (محاولة {i+1})")
                            time.sleep(POLL_INTERVAL)
                            progress.progress(int((i+1) / STATUS_POLL_ATTEMPTS * 100))
                            continue

                        if status_res.status_code != 200:
                            status_box.text(f"⚠️ استجابة الحالة: {status_res.status_code} (محاولة {i+1})")
                        else:
                            s_data = status_res.json()
                            current_status = s_data.get("status") or s_data.get("state")
                            status_box.text(f"🔄 الحالة الحالية: {current_status} (فحص رقم {i+1})")
                            if current_status and current_status.lower() == "completed":
                                final_url = s_data.get("content_url") or s_data.get("download_url") or s_data.get("result_url")
                                status_box.success("🎉 ممتاز! تم اكتمال توليد الفيديو بنجاح.")
                                break
                            if current_status and current_status.lower() in ("failed", "error", "cancelled"):
                                status_box.error("❌ فشلت عملية التوليد.")
                                break

                        progress.progress(int((i+1) / STATUS_POLL_ATTEMPTS * 100))
                        time.sleep(POLL_INTERVAL)

                    if final_url:
                        status_box.info("📥 جارٍ تنزيل الفيديو للمعاينة والتنزيل...")
                        buf = download_bytes(final_url, headers=headers)
                        if buf:
                            st.video(buf.getvalue())
                            st.download_button(
                                "⬇️ تنزيل الفيديو",
                                data=buf.getvalue(),
                                file_name=f"{output_name}_{job_id}.mp4",
                                mime="video/mp4",
                            )
                        else:
                            st.warning("⚠️ لا يمكن تنزيل الملف تلقائياً. عرض الرابط فقط:")
                            st.write(final_url)

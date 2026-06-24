import base64
import os
import json
import time
from pathlib import Path
from io import BytesIO

import requests
import streamlit as st

# إعداد الصفحة الافتراضية
st.set_page_config(
    page_title="TECH BIT STUDIO",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ملف حفظ المعرض المحلي
GALLERY_FILE = Path("studio_gallery.json")
MODELS_CACHE_FILE = Path("studio_models_cache.json")

# فرض التصميم النيوني والمستقبلي المتطور (Cyberpunk / Glassmorphism Style)
st.markdown("""
    <style>
    .main {
        background: radial-gradient(circle, #090d16 0%, #020408 100%);
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] {
        background-color: #020617 !important;
        border-right: 2px solid #00f0ff;
    }
    .streamlit-expanderHeader {
        color: #00f0ff !important;
    }
    h1, h2, h3, h4, h5 {
        color: #00f0ff !important;
        text-shadow: 0 0 10px #00f0ff, 0 0 20px #00f0ff;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        background: linear-gradient(45deg, #ff007f, #7928ca);
        color: white !important;
        border: none !important;
        box-shadow: 0 0 15px #ff007f;
        transition: all 0.2s ease;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        transform: scale(1.04);
        box-shadow: 0 0 25px #ff007f, 0 0 35px #7928ca;
    }
    .agent-box {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(0, 240, 255, 0.4);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.15);
        margin-bottom: 22px;
    }
    .stTextArea>div>textarea,
    .stTextInput>div>input,
    .stSelectbox>div>div>div>span {
        background: rgba(255, 255, 255, 0.06) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
    }
    .stRadio>div>label,
    .stCheckbox>div>label {
        color: #e2e8f0 !important;
    }
    .contact-box {
        background: rgba(4, 12, 27, 0.9);
        border: 1px solid rgba(0, 240, 255, 0.25);
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.08);
        margin-top: 18px;
    }
    .contact-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        background: linear-gradient(135deg, #ff007f, #7928ca);
        color: #ffffff !important;
        text-decoration: none;
        padding: 10px 16px;
        border-radius: 12px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .contact-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 0 18px rgba(255, 0, 127, 0.25);
    }
    </style>
""", unsafe_allow_html=True)

# تحميل وحفظ معرض الاستوديو

def load_gallery():
    if GALLERY_FILE.exists():
        try:
            return json.loads(GALLERY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_gallery(items):
    try:
        GALLERY_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


API_BASE_URL = "https://openrouter.ai/api/v1"


def try_post(endpoint, headers, payload):
    try:
        return requests.post(endpoint, headers=headers, json=payload, timeout=60)
    except requests.RequestException:
        return None


def normalize_url(raw, base="https://openrouter.ai/api/v1"):
    if not raw:
        return None
    if raw.startswith("http"):
        return raw
    return base.rstrip("/") + "/" + raw.lstrip("/")


def download_content(url, headers=None):
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=120)
        response.raise_for_status()
        return response.content
    except requests.RequestException:
        return None


def create_video_job(prompt_payload, model_option, duration, resolution, aspect_ratio, enable_audio, headers):
    payload = {
        "model": model_option,
        "prompt": prompt_payload,
        "duration": duration,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "generate_audio": enable_audio,
    }
    response = try_post(f"{API_BASE_URL}/videos", headers, payload)
    if response is None:
        return {"error": "connection"}
    if response.status_code not in (200, 201, 202):
        return {"error": response.text or f"HTTP {response.status_code}"}

    try:
        data = response.json()
    except ValueError:
        body_text = response.text.strip()
        if response.status_code == 202 and not body_text:
            return {"error": "accepted_no_body"}
        return {"error": f"invalid_json_response: {body_text[:400]}"}

    polling_url = normalize_url(data.get("polling_url") or data.get("status_url") or f"/videos/{data.get('id') or data.get('job_id', '')}")
    return {"polling_url": polling_url, "job_id": data.get("id") or data.get("job_id")}


def poll_video_job(job_id, polling_url, headers):
    status_box = st.empty()
    progress = st.progress(0)
    for attempt in range(25):
        try:
            status_res = requests.get(polling_url, headers=headers, timeout=60)
        except requests.RequestException as exc:
            status_box.warning(f"⚠️ خطأ في استعلام الحالة: {exc} (محاولة {attempt + 1})")
            time.sleep(5)
            progress.progress(int((attempt + 1) / 25 * 100))
            continue

        if status_res.status_code != 200:
            status_box.warning(f"⚠️ استجابة الحالة: {status_res.status_code} (محاولة {attempt + 1})")
        else:
            try:
                result = status_res.json()
            except ValueError:
                status_box.warning("⚠️ استقبلنا استجابة حالة غير صالحة من الخادم.")
                result = {}

            current_status = result.get("status") or result.get("state")
            status_box.info(f"🔄 الحالة الحالية: {current_status} (فحص رقم {attempt + 1})")
            if current_status and current_status.lower() == "completed":
                final_url = None
                urls = result.get("unsigned_urls") or result.get("urls") or []
                if isinstance(urls, list) and urls:
                    first = urls[0]
                    if isinstance(first, str):
                        final_url = normalize_url(first)

                if not final_url:
                    final_url = normalize_url(result.get("content_url") or result.get("download_url") or result.get("result_url"))

                status_box.success("🎉 تم اكتمال توليد الفيديو بنجاح.")
                return {"final_url": final_url, "job_id": job_id}

            if current_status and current_status.lower() in ("failed", "error", "cancelled"):
                status_box.error("❌ فشلت عملية التوليد.")
                return {"error": f"video_status_{current_status}", "job_id": job_id}

        progress.progress(int((attempt + 1) / 25 * 100))
        time.sleep(5)

    return {"error": "timeout", "job_id": job_id}


def fetch_video_content(job_id, headers):
    url = f"{API_BASE_URL}/videos/{job_id}/content"
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=120)
    except requests.RequestException as exc:
        return {"error": str(exc)}

    if response.status_code == 200:
        return response.content

    try:
        data = response.json()
        error_text = data.get("error") or json.dumps(data)
    except ValueError:
        error_text = response.text.strip()[:400]
    return {"error": f"status_{response.status_code}: {error_text}"}


def create_image(prompt_payload, model_option, headers):
    payload = {
        "model": model_option,
        "prompt": prompt_payload,
        "size": "1024x1024",
        "output_format": "png",
        "n": 1,
    }
    response = try_post(f"{API_BASE_URL}/images", headers, payload)
    if response is None:
        return {"error": "connection"}
    if response.status_code not in (200, 201, 202):
        return {"error": response.text or f"HTTP {response.status_code}"}
    try:
        data = response.json()
    except ValueError:
        return {"error": f"invalid_json_response: {response.text.strip()[:400]}"}
    output = data.get("output") or data.get("data")
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, str):
            return {"url": normalize_url(first)}
        if isinstance(first, dict):
            if first.get("url"):
                return {"url": normalize_url(first.get("url"))}
            if first.get("image_url"):
                return {"url": normalize_url(first.get("image_url"))}
            if first.get("b64_json"):
                return {"b64_json": first.get("b64_json")}
    return {"error": "no_image"}


def _extract_models_from_list(data):
    models = []
    if not data:
        return models
    # Some endpoints return a dict with a list under various keys
    if isinstance(data, dict):
        for k in ("models", "data", "items", "results"):
            if k in data and isinstance(data[k], list):
                data = data[k]
                break
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                models.append(item)
            elif isinstance(item, dict):
                # prefer commonly used fields
                for key in ("id", "name", "model", "slug"):
                    if key in item and isinstance(item[key], str):
                        models.append(item[key])
                        break
                else:
                    # try author+slug
                    author = item.get("author")
                    slug = item.get("slug") or item.get("name") or item.get("id")
                    if author and slug:
                        models.append(f"{author}/{slug}")
    # unique preserve order
    seen = {}
    out = []
    for m in models:
        if m and m not in seen:
            seen[m] = True
            out.append(m)
    return out


def get_provider_logo_html(provider):
    provider_key = (provider or '').lower().replace(' ', '')
    colors = {
        'openai': '#6f5dfc',
        'google': '#4285f4',
        'x-ai': '#00c2ff',
        'alibaba': '#ff8c00',
        'kuaishou': '#ff8800',
        'stabilityai': '#0d47a1',
        'microsoft': '#737373',
        'sourceful': '#00b37e',
        'recraft': '#eb3b5a',
    }
    name = provider_key.split('/')[0] if '/' in provider_key else provider_key
    color = colors.get(name, '#2d3748')
    initials = ''.join([part[0].upper() for part in name.split('-') if part])[:2] or '?'
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">'
        f'<rect width="32" height="32" rx="8" fill="{color}" />'
        f'<text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle" '
        f'font-family="Segoe UI, sans-serif" font-size="16" fill="#ffffff">{initials}</text>'
        '</svg>'
    )
    encoded = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    return f'<img src="data:image/svg+xml;base64,{encoded}" style="height:32px;width:32px;border-radius:8px;margin-right:10px;vertical-align:middle;" />\n'


def get_model_kind(meta, model_id=''):
    if isinstance(meta, dict):
        architecture = meta.get('architecture')
        if isinstance(architecture, dict):
            output_modalities = architecture.get('output_modalities')
            if isinstance(output_modalities, list):
                lowered = [str(item).lower() for item in output_modalities if item]
                if 'image' in lowered:
                    return 'Image'
                if 'video' in lowered:
                    return 'Video'
        if meta.get('supported_durations') or meta.get('supported_frame_images') or meta.get('supported_aspect_ratios'):
            return 'Video'
        if meta.get('supported_parameters') or meta.get('size'):
            return 'Image'
    model_id = (model_id or '').lower()
    if 'video' in model_id or 'veo' in model_id or 'kling' in model_id:
        return 'Video'
    if 'image' in model_id or 'gpt-image' in model_id or 'grok' in model_id:
        return 'Image'
    return 'Unknown'


def get_available_models(api_key=None):
    """Query OpenRouter for available video and image models.
    Returns a list of model identifiers or None on failure.
    """
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    endpoints = [f"{API_BASE_URL}/videos/models", f"{API_BASE_URL}/images/models"]
    results = []
    for ep in endpoints:
        try:
            r = requests.get(ep, headers=headers, timeout=8)
            if r.status_code == 200:
                try:
                    data = r.json()
                except ValueError:
                    continue
                # expect data to contain a 'data' list of model objects
                models_data = None
                if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                    models_data = data['data']
                else:
                    # fall back to extracting lists
                    models_data = _extract_models_from_list(data)

                if isinstance(models_data, list):
                    for m in models_data:
                        if isinstance(m, dict):
                            # normalize to include id and name
                            mid = m.get('id') or m.get('slug') or m.get('name')
                            if not mid:
                                continue
                            entry = {
                                'id': mid,
                                'name': m.get('name') or mid,
                                'description': m.get('description') or m.get('summary') or '',
                                'provider': m.get('provider') or m.get('author') or m.get('canonical_slug') or '',
                                'meta': m,
                            }
                            results.append(entry)
                        elif isinstance(m, str):
                            results.append({'id': m, 'name': m, 'description': '', 'provider': '', 'meta': {}})
        except requests.RequestException:
            continue

    return results or None


def save_models_cache_to_file(models):
    try:
        MODELS_CACHE_FILE.write_text(json.dumps({'ts': time.time(), 'models': models}, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


def load_models_cache_from_file(max_age=0):
    if not MODELS_CACHE_FILE.exists():
        return None
    try:
        raw = json.loads(MODELS_CACHE_FILE.read_text(encoding='utf-8'))
        ts = raw.get('ts', 0)
        if max_age and time.time() - ts > max_age:
            return None
        return raw.get('models')
    except Exception:
        return None


def _cached_models_get(api_key=None, max_age=300):
    """Return cached models from session_state or refresh if expired.
    max_age in seconds.
    """
    now = time.time()
    # check session cache
    cache = st.session_state.get("models_cache")
    if cache and isinstance(cache, dict):
        ts = cache.get("ts", 0)
        if now - ts < max_age and cache.get("models"):
            return cache.get("models")

    # check persisted file cache
    file_models = load_models_cache_from_file(max_age=max_age)
    if file_models:
        st.session_state.models_cache = {"models": file_models, "ts": time.time()}
        return file_models

    models = get_available_models(api_key)
    if models:
        st.session_state.models_cache = {"models": models, "ts": now}
        save_models_cache_to_file(models)
    return models


if "gallery" not in st.session_state:
    st.session_state.gallery = load_gallery()

# مفتاح API من البيئة أو الإدخال
api_key_env = os.getenv("OPENROUTER_API_KEY", "")

# --- القائمة الجانبية: الوكلاء، الإعدادات، ومفتاح الـ API ---
with st.sidebar:
    st.markdown("## ⚙️ إعدادات TECH BIT STUDIO")
    api_input = st.text_input(
        "أدخل مفتاح OpenRouter API:",
        type="password",
        placeholder="يمكنك ضبط OPENROUTER_API_KEY في البيئة",
        value="",
    )

    api_key = api_input.strip() if api_input else api_key_env
    if not api_input and api_key_env:
        st.success("✅ يتم استخدام المفتاح من متغير البيئة OPENROUTER_API_KEY.")

    st.markdown("---")
    st.markdown("### 🤖 وكيل الواجهة المتحدث (UI Agent Persona)")
    st.markdown(
        "<div class='agent-box' style='border-color: #ff007f; box-shadow: 0 0 10px rgba(255,0,127,0.2);'>"
        "<strong>🤖 سيمور:</strong><br>"
        "<span style='color: #cbd5e1; font-size: 0.95rem;'>مرحباً بك في TECH BIT STUDIO. سأكون دليلك الرقمي خلال رحلة إنتاج الفيديو والصور ثلاثية الأبعاد. اختر مشهدك، واسمح للوكلاء المتخصصين بتحويله إلى عمل سينمائي حقيقي.</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### 🎯 وضع الوكلاء")
    orchestration_mode = st.selectbox(
        "اختر استراتيجية التوليد:",
        ["Cinematic Director", "Art Studio", "Fast Draft"],
        index=0,
    )
    enable_gallery_save = st.checkbox("حفظ المعرض محلياً في ملف JSON", value=True)
    st.markdown("---")
    st.markdown("### 📌 نماذج مدعومة")
    st.write("- google/veo-3.1-lite")
    st.write("- xai/grok-imagine-video")
    st.write("- kuaishou/kling-v3.0-standard")
    st.write("- stabilityai/stable-diffusion-3")
    st.markdown("---")
    st.markdown("### 🏷️ دليل مقدمي النماذج")
    legend_html = "<div style='display:flex; flex-wrap:wrap; gap:8px;'>"
    for provider in ["openai", "google", "x-ai", "alibaba", "kuaishou", "stabilityai", "microsoft", "sourceful", "recraft"]:
        legend_html += (
            '<div style="display:flex; align-items:center; gap:8px; background: rgba(255,255,255,0.06); '
            'border: 1px solid rgba(0,240,255,0.14); border-radius: 14px; padding: 8px 10px;">'
            + get_provider_logo_html(provider)
            + f'<span style="color:#e2e8f0; font-size:0.9rem;">{provider}</span>'
            + '</div>'
        )
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)

    contact_html = """
    <div class='contact-box'>
      <div style='display:flex; align-items:center; gap:12px; margin-bottom:14px;'>
        <div style='width:42px; height:42px; border-radius:14px; background: linear-gradient(135deg, #ff007f, #7928ca); display:flex; align-items:center; justify-content:center;'>
          <span style='font-size:1.2rem;'>💬</span>
        </div>
        <div>
          <strong>للطلبات أو استفسار الاشتراكات</strong><br>
          <span style='color:#cbd5e1; font-size:0.92rem;'>تواصل معنا عبر تلغرام أو واتساب مباشرة.</span>
        </div>
      </div>
      <div style='display:flex; flex-direction:column; gap:8px;'>
        <a href='https://t.me/TECHBITTrading' target='_blank' class='contact-button'>📱 TELEGRAM</a>
        <a href='https://wa.me/967739942424' target='_blank' class='contact-button'>📲 WHATSAPP</a>
      </div>
      <div style='margin-top:14px; color:#cbd5e1; font-size:0.92rem;'>
        <strong>PHONE:</strong> +967 784983835
      </div>
    </div>
    """
    st.markdown(contact_html, unsafe_allow_html=True)

# --- الوجهة الرئيسية للتطبيق ---
st.title("🌌 TECH BIT STUDIO")
st.markdown(
    "منصة استوديو تقنية متعددة الوكلاء لتوليد الفيديو والصور والأعمال الفنية الرقمية بأسلوب نيوني وسينمائي."
)

# تقسيم الواجهة إلى تبويبات
tab_generate, tab_gallery, tab_workshop = st.tabs(
    ["🚀 التوليد والإنتاج", "🎨 معرض الاستوديو", "🧠 ورشة الوكلاء"]
)

with tab_generate:
    left, right = st.columns([2.2, 1])

    with left:
        st.markdown("### ✨ توليد المشهد السينمائي")
        prompt_presets = {
            "اختر قالباً": "",
            "مدينة مستقبلية متوهجة": "A cinematic futuristic city with neon-lit highways, hovering drones, and a stylized 3D character walking through a high-tech metropolis.",
            "استوديو إنتاج ثلاثي الأبعاد": "A cinematic 3D production studio with holographic screens, animated robots, and a bright neon palette, featuring the Tech Bit character.",
            "مغامرة فضائية": "A cinematic space adventure with Tech Bit flying through a glowing interstellar city, futuristic vehicles, and sweeping camera motion.",
        }
        selected_preset = st.selectbox("قالب جاهز للمشهد:", list(prompt_presets.keys()))
        prompt_text = st.text_area(
            "اكتب وصف المشهد أو الفكرة:",
            value=prompt_presets[selected_preset] if selected_preset != "اختر قالباً" else "",
            height=160,
        )
        if selected_preset != "اختر قالباً":
            st.caption("تم تعبئة القالب الجاهز تلقائياً. يمكنك التعديل عليه إذا رغبت.")

        st.markdown("---")
        st.markdown("### 🧩 إعدادات الإنتاج")
        media_type = st.radio(
            "اختر نوع الإنتاج:",
            ["فيديو سينمائي متحرك (Video)", "لوحة فنية عالية الدقة (Image)"]
        )
        # Try to fetch available models from OpenRouter with caching (falls back to static list)
        default_models = ["google/veo-3.1-lite", "xai/grok-imagine-video", "kuaishou/kling-v3.0-standard", "stabilityai/stable-diffusion-3"]
        # UI: TTL control, filter, and refresh
        col_m1, col_m2 = st.columns([4, 1])
        with col_m1:
            cache_ttl = st.number_input("Cache TTL (seconds)", min_value=0, value=300, step=60)
            filter_text = st.text_input("فلتر النماذج (بحث بالاسم أو المعرف):", value="")
        with col_m2:
            refresh_clicked = st.button("⟳ تحديث")

        # load models (session -> file -> network)
        fetched_models = _cached_models_get(api_key or api_key_env, max_age=cache_ttl)
        models_list = []
        if fetched_models:
            # ensure list of dicts
            for m in fetched_models:
                if isinstance(m, dict):
                    models_list.append(m)
                else:
                    models_list.append({'id': str(m), 'name': str(m), 'description': '', 'provider': '', 'meta': {}})
        else:
            # fallback static
            for m in default_models:
                models_list.append({'id': m, 'name': m, 'description': '', 'provider': '', 'meta': {}})

        if refresh_clicked:
            new = get_available_models(api_key or api_key_env)
            if new:
                # normalize new into list of dicts and persist
                norm = []
                for m in new:
                    if isinstance(m, dict):
                        norm.append(m)
                    else:
                        norm.append({'id': str(m), 'name': str(m), 'description': '', 'provider': '', 'meta': {}})
                st.session_state.models_cache = {'models': norm, 'ts': time.time()}
                save_models_cache_to_file(norm)
                models_list = norm
            else:
                st.warning("⚠️ لم نتمكن من جلب النماذج. راجع الاتصال أو المفتاح.")

        # provider filter
        providers = sorted({(m.get('provider') or '').strip() for m in models_list if (m.get('provider') or '').strip()})
        provider_choices = ['All Providers'] + providers
        provider_filter = st.selectbox('مزود النموذج:', provider_choices, index=0)

        # apply text + provider filter
        def model_matches(m, txt, provider_sel):
            txt = (txt or '').lower().strip()
            if provider_sel and provider_sel != 'All Providers':
                if (m.get('provider') or '') != provider_sel:
                    return False
            if not txt:
                return True
            return txt in (m.get('id') or '').lower() or txt in (m.get('name') or '').lower() or txt in (m.get('description') or '').lower()

        filtered = [m for m in models_list if model_matches(m, filter_text, provider_filter)]
        option_labels = [f"{m.get('id')} — {m.get('name')}" for m in filtered]
        option_ids = [m.get('id') for m in filtered]
        if not option_labels:
            option_labels = ['(no models)']
            option_ids = ['']

        # prefer explicit selection from session_state if present
        preferred_default_model = "x-ai/grok-imagine-video-20260512"
        prev_sel = st.session_state.get('selected_model_id')
        if prev_sel and prev_sel in option_ids:
            default_index = option_ids.index(prev_sel)
        elif preferred_default_model in option_ids:
            default_index = option_ids.index(preferred_default_model)
        else:
            default_index = 0

        selected_label = st.selectbox("اختر النموذج:", option_labels, index=default_index)
        try:
            sel_idx = option_labels.index(selected_label)
        except ValueError:
            sel_idx = 0
        model_option = option_ids[sel_idx]

        # show provider/info for selected model and interactive cards for quick selection
        sel_meta = filtered[sel_idx].get('meta') if sel_idx < len(filtered) else {}
        # small emoji mapping for known providers
        emoji_map = {
            'openai': '🟣', 'google': '🔵', 'alibaba': '🟠', 'x-ai': '🟢', 'kwaivgi': '🟡', 'kwaishou': '🟡'
        }

        # model cards (top 6)
        if filtered:
            cards = filtered[:6]
            cols = st.columns(len(cards))
            for i, m in enumerate(cards):
                with cols[i]:
                    provider = m.get('provider') or ''
                    provider_html = get_provider_logo_html(provider) if provider else ''
                    kind = get_model_kind(m.get('meta'), m.get('id'))
                    desc = (m.get('description') or 'No description available.')[:140]
                    card_html = (
                        f'<div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(0,240,255,0.18); '
                        f'border-radius: 18px; padding: 18px; margin-bottom: 12px; height: 250px; display: flex; '
                        f'flex-direction: column; justify-content: space-between;">'
                        f'<div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">{provider_html}'
                        f'<div><strong style="font-size:1rem; display:block;">{m.get("name")}</strong>'
                        f'<span style="color:#94a3b8; font-size:0.85rem;">{provider or "Unknown provider"}</span></div></div>'
                        f'<div style="color:#cbd5e1; font-size:0.85rem; min-height:90px; margin-bottom:12px;">{desc}</div>'
                        f'<div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px;">'
                        f'<span style="background: rgba(56,189,248,0.16); color:#7dd3fc; padding:5px 10px; border-radius:999px; font-size:0.75rem;">{kind}</span>'
                        f'<span style="background: rgba(165,180,252,0.16); color:#c7d2fe; padding:5px 10px; border-radius:999px; font-size:0.75rem;">{m.get("id")[:24]}</span>'
                        '</div>'
                        f'<div style="display:flex; justify-content:flex-end;">'
                        f'<span style="color:#94a3b8; font-size:0.75rem;">{provider or "Unknown"}</span>'
                        '</div>'
                        '</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                    if st.button("Select", key=f"sel_{m.get('id')}"):
                        st.session_state['selected_model_id'] = m.get('id')
                        st.experimental_rerun()

        with st.expander('تفاصيل النموذج', expanded=False):
            prov = filtered[sel_idx].get('provider', '')
            prov_html = get_provider_logo_html(prov) if prov else ''
            kind = get_model_kind(sel_meta, model_option)
            st.markdown(
                f"<div style='display:flex; align-items:center; gap:10px; margin-bottom:8px;'>"
                f"{prov_html}<div><strong>{filtered[sel_idx].get('name', '')}</strong><br/>"
                f"<span style='color:#94a3b8;'>Provider: {prov or 'Unknown'}</span></div></div>"
                f"<div style='margin-bottom:8px;'><span style='background: rgba(56,189,248,0.16); color:#7dd3fc; padding:4px 10px; border-radius:999px; font-size:0.85rem;'>{kind}</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**ID:** {model_option}")
            desc = filtered[sel_idx].get('description', '')
            if desc:
                st.write(desc)
            # show some meta fields if present
            if isinstance(sel_meta, dict):
                if sel_meta.get('supported_resolutions'):
                    st.write('Supported resolutions: ' + ', '.join(map(str, sel_meta.get('supported_resolutions'))))
                if sel_meta.get('supported_aspect_ratios'):
                    st.write('Supported aspect ratios: ' + ', '.join(map(str, sel_meta.get('supported_aspect_ratios'))))
                if sel_meta.get('supported_durations'):
                    st.write('Supported durations: ' + ', '.join(map(str, sel_meta.get('supported_durations'))))
                if sel_meta.get('supported_parameters'):
                    st.write('Supported params: ' + ', '.join(sorted(sel_meta.get('supported_parameters').keys())))

        # size/duration controls adapt to selected model meta if available
        supported_resolutions = None
        supported_aspects = None
        supported_durations = None
        try:
            if isinstance(sel_meta, dict):
                supported_resolutions = sel_meta.get('supported_resolutions')
                supported_aspects = sel_meta.get('supported_aspect_ratios') or sel_meta.get('supported_aspects')
                supported_durations = sel_meta.get('supported_durations') or sel_meta.get('supported_lengths')
        except Exception:
            supported_resolutions = None

        col_a, col_b = st.columns(2)
        with col_a:
            if media_type.startswith("فيديو"):
                if supported_durations:
                    # ensure list of ints or strings
                    duration = st.selectbox('مدة الفيديو (بالثواني)', list(map(str, supported_durations)), index=0)
                    try:
                        duration = int(duration)
                    except Exception:
                        pass
                else:
                    duration = st.number_input('مدة الفيديو (بالثواني)', min_value=1, max_value=300, value=10)

                if supported_resolutions:
                    resolution = st.selectbox('دقة', list(map(str, supported_resolutions)), index=min(1, len(supported_resolutions)-1))
                else:
                    resolution = st.selectbox('دقة', ['480p', '720p', '1080p'], index=1)
            else:
                duration = None
                if supported_resolutions:
                    resolution = st.selectbox('دقة الصورة', list(map(str, supported_resolutions)), index=min(1, len(supported_resolutions)-1))
                else:
                    resolution = st.selectbox('دقة الصورة', ['512x512', '768x768', '1024x1024'], index=1)

        with col_b:
            if supported_aspects:
                aspect_ratio = st.selectbox('نسبة العرض إلى الارتفاع:', list(map(str, supported_aspects)), index=0)
            else:
                aspect_ratio = st.selectbox('نسبة العرض إلى الارتفاع:', ['16:9', '9:16', '1:1'])
            enable_audio = st.checkbox('تضمين صوت تلقائي', value=False)

        output_filename = st.text_input("اسم ملف المشروع النهائي:", value="techbit_studio_output")

        st.markdown("---")
        st.markdown("### 🚀 الوكلاء المتخصصون")
        st.write("Director Agent: صياغة النص السينمائي.")
        st.write("Art Agent: توليد الصور والفنون.")
        st.write("Movie Agent: بناء لقطة الفيديو وتحريك المشهد.")

        if st.button("🔮 بدء توليد TECH BIT STUDIO"):
            if not api_key:
                st.error("⚠️ يرجى إدخال مفتاح OpenRouter API أو تعيينه في متغيرات البيئة.")
            elif not prompt_text.strip():
                st.warning("⚠️ اكتب وصفاً أو اختر قالباً جاهزاً لبدء التوليد.")
            else:
                prompt_payload = f"{prompt_text.strip()} | Style: {orchestration_mode} | Format: {media_type} | Ratio: {aspect_ratio}"
                with st.spinner("⏳ الوكلاء يجهزون المشهد ويستعدون للإطلاق..."):
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    result_url = None
                    video_bytes = None
                    image_bytes = None
                    result_type = media_type
                    if media_type.startswith("فيديو"):
                        job_response = create_video_job(
                            prompt_payload,
                            model_option,
                            duration,
                            resolution,
                            aspect_ratio,
                            enable_audio,
                            headers,
                        )
                        if job_response.get("error"):
                            st.error(f"❌ فشل إنشاء مهمة الفيديو: {job_response['error']}")
                        else:
                            polling_url = job_response.get("polling_url")
                            job_id = job_response.get("job_id")
                            if polling_url:
                                poll_result = poll_video_job(job_id, polling_url, headers)
                                if poll_result.get("final_url"):
                                    result_url = poll_result["final_url"]
                                elif poll_result.get("job_id"):
                                    content_response = fetch_video_content(poll_result["job_id"], headers)
                                    if isinstance(content_response, bytes):
                                        video_bytes = content_response
                                    else:
                                        st.error(f"❌ لم يتم الحصول على محتوى الفيديو: {content_response.get('error')}")
                                else:
                                    st.error("❌ لم يتم الحصول على رابط الفيديو بعد اكتمال المهمة.")
                            else:
                                st.error("❌ لم يتم تلقي رابط متابعة صالح من OpenRouter.")
                    else:
                        image_response = create_image(prompt_payload, model_option, headers)
                        if image_response.get("error"):
                            st.error(f"❌ فشل توليد الصورة: {image_response['error']}")
                        elif image_response.get("url"):
                            result_url = image_response["url"]
                        elif image_response.get("b64_json"):
                            try:
                                image_bytes = base64.b64decode(image_response["b64_json"])
                            except Exception as exc:
                                st.error(f"❌ خطأ في فك تشفير الصورة: {exc}")

                    if result_url or image_bytes or video_bytes:
                        gallery_item = {
                            "prompt": prompt_payload,
                            "type": result_type,
                            "model": model_option,
                            "url": result_url if result_url else "",
                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "filename": f"{output_filename}.mp4" if media_type.startswith("فيديو") else f"{output_filename}.png",
                        }
                        st.session_state.gallery.append(gallery_item)
                        if enable_gallery_save:
                            save_gallery(st.session_state.gallery)
                        st.success("🎉 تم توليد العمل الفني وحفظه في المعرض.")

                        if media_type.startswith("فيديو"):
                            if video_bytes:
                                st.video(video_bytes)
                                st.download_button(
                                    "⬇️ تنزيل الفيديو",
                                    data=video_bytes,
                                    file_name=gallery_item["filename"],
                                    mime="video/mp4",
                                )
                            elif result_url:
                                st.video(result_url)
                                downloaded = download_content(result_url, headers=headers)
                                if downloaded:
                                    st.download_button(
                                        "⬇️ تنزيل الفيديو",
                                        data=downloaded,
                                        file_name=gallery_item["filename"],
                                        mime="video/mp4",
                                    )
                                else:
                                    st.warning("⚠️ تم إنشاء الفيديو لكن لم نتمكن من تنزيله تلقائيًا.")
                        elif image_bytes:
                            st.image(image_bytes, caption="لوحة فنية من TECH BIT STUDIO")
                            st.download_button(
                                "⬇️ تنزيل الصورة",
                                data=image_bytes,
                                file_name=gallery_item["filename"],
                                mime="image/png",
                            )
                        elif result_url:
                            st.image(result_url, caption="لوحة فنية من TECH BIT STUDIO")
                            image_bytes = download_content(result_url, headers=headers)
                            if image_bytes:
                                st.download_button(
                                    "⬇️ تنزيل الصورة",
                                    data=image_bytes,
                                    file_name=gallery_item["filename"],
                                    mime="image/png",
                                )
                    else:
                        st.warning("⚠️ لم يتم إنشاء أي محتوى للعرض. تحقق من استجابة OpenRouter أو أعد المحاولة.")

    with right:
        st.markdown("### 📡 حالة الوكلاء النشطين")
        st.markdown(
            "<div class='agent-box'>"
            "<b style='color: #00f0ff;'>🎬 Director Agent</b><br>"
            "<span style='color: #a7f3d0;'>● يعمل على تحسين النصوص وصياغة الإرشادات السينمائية.</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='agent-box'>"
            "<b style='color: #00f0ff;'>🎨 Art Agent</b><br>"
            "<span style='color: #a7f3d0;'>● مسؤول عن إنشاء الأشكال الفنية والتراكيب البصرية.</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='agent-box'>"
            "<b style='color: #00f0ff;'>🎥 Movie Agent</b><br>"
            "<span style='color: #a7f3d0;'>● يبني اللقطات المتحركة ويضبط المحاكاة السينمائية.</span>"
            "</div>",
            unsafe_allow_html=True,
        )

with tab_gallery:
    st.markdown("### 🎨 معرض الأعمال المحفوظة")
    if not st.session_state.gallery:
        st.info("المعرض فارغ حالياً. أنشئ أول عمل فني ليظهر هنا.")
    else:
        for idx, item in enumerate(reversed(st.session_state.gallery), start=1):
            st.markdown("---")
            st.markdown(f"#### 🎬 عمل فني #{idx} | {item['time']}")
            st.write(f"**الوصف:** {item['prompt']}")
            st.write(f"**النموذج:** `{item['model']}` | **النوع:** {item['type']}")
            if item['type'].startswith("فيديو"):
                st.video(item['url'])
            else:
                st.image(item['url'])
            st.download_button(
                "⬇️ تنزيل الملف",
                data=requests.get(item['url']).content if item['url'].startswith("http") else None,
                file_name=item.get("filename", "techbit_item"),
                mime="video/mp4" if item['type'].startswith("فيديو") else "image/png",
            )

    if st.button("🧹 تفريغ المعرض" ):
        st.session_state.gallery = []
        save_gallery([])
        st.experimental_rerun()

with tab_workshop:
    st.markdown("### 🧠 ورشة عمل الوكلاء")
    st.write(
        "استخدم هذه المساحة لتخصيص ما يفعله كل وكيل، وضبط استراتيجيات التوليد، وتشغيل الإعدادات الخاصة بالاستديو."
    )
    st.markdown("- **Director Agent:** يحسن الأوامر ويحوّلها إلى سيناريو سينمائي.")
    st.markdown("- **Art Agent:** يتولى الجوانب الجمالية والمجسمات.")
    st.markdown("- **Movie Agent:** يبني الحركة والإخراج النهائي للفيديو.")
    st.markdown("---")
    st.write("يمكنك هنا أيضاً إضافة تعليمات خاصة أو وصف نمط الإخراج لتحسين نتائج التوليد في المرات القادمة.")
    st.text_area("تعليمات وكيل الإخراج الخاصة:", value="مثلاً: استخدم ألوان نيون، ضوء خافت، لمسات فنية مستوحاة من Cyberpunk.", height=120)

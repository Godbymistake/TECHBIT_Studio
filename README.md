# TECH BIT 3D - Streamlit Video Generator

This project is a Streamlit front-end for generating videos via OpenRouter-like APIs. It includes:

- A polished Arabic/RTL Streamlit app (`app.py`).https://techbitstudio-rfoak99gbkhqwu86er99sq.streamlit.app/
- Robust synchronous polling with progress UI and downloadable video.
- Optional background-worker integration via RQ/Redis (worker not required for the synchronous flow).

## Quick start

1. Create and activate a Python environment (recommended):

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

1. Run the Streamlit app:

```powershell
streamlit run app.py
```

1. Alternatively, run the new TECH BIT STUDIO interface:

```powershell
streamlit run studio.py
```

1. If you prefer not to paste the API key into the UI, set it as an environment variable:

```powershell
$env:OPENROUTER_API_KEY = "sk-or..."
streamlit run app.py
```

The project now includes:

- `app.py`: واجهة توليد الفيديو بالتحديثات الذكية.
- `studio.py`: واجهة TECH BIT STUDIO النيوني المتعددة الوكلاء.
- استخدام مفتاح OpenRouter من متغير البيئة `OPENROUTER_API_KEY`
- اختيار قالب جاهز من جانب الاستوديو
- إعدادات دقة ونسبة عرض/ارتفاع محسّنة
- اسم ملف قابل للتخصيص قبل التنزيل
- معرض أعمال محلي داخل الجلسة لكل عناصر التوليد

## Optional: Background worker with RQ

If you want to process jobs asynchronously, run a Redis server and an RQ worker. The app will enqueue jobs when you enable the "استخدام عامل خلفي" checkbox — a worker must be implemented/connected to process those jobs.

Install Redis (locally or use a managed Redis). Start an RQ worker:

```powershell
rq worker
```

Notes:

- The app supports both `/api/v1/videos` and `/v1/videos` endpoints and will attempt to normalize returned polling URLs.
- If automatic download fails, the app will show the direct download link.

## حقوق TECHBIT

جميع الحقوق محفوظة لـ TECHBIT. يُسمح باستخدام هذا المشروع لأغراض التطوير والاختبار والتعليم.

- لا يجوز إعادة بيع هذه النسخة مباشرة بدون إذن صريح من TECHBIT.
- يجب الحفاظ على اسم TECHBIT والشعار في واجهة المستخدم وملفات الوثائق عند نشر أو مشاركة المشروع.
- يُنصح باستخدام المشروع كقاعدة لتجربة تكامل OpenRouter وتطوير واجهة واجهات الاستخدام.

## كيف الاستخدام

1. تثبيت المتطلبات:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

1. تشغيل التطبيق:

```powershell
streamlit run studio.py
```

1. إعداد مفتاح OpenRouter:

```powershell
$env:OPENROUTER_API_KEY = "sk-or..."
streamlit run studio.py
```

1. استخدام التطبيق:

- اختر نموذجاً من قائمة النماذج.
- أدخل وصف المشهد أو استخدم قالباً جاهزاً.
- اختر نوع الإنتاج (فيديو أو صورة).
- اضغط "🔮 بدء توليد TECH BIT STUDIO".
- انتظر حتى يكتمل التوليد ثم قم بتنزيل النتيجة.

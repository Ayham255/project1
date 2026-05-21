# 🤖 Vision + Voice AI Assistant

> نظام مساعد ذكي يعمل بالكاميرا والصوت على Jetson Orin Nano - مشروع تخرج

A real-time dual-camera AI assistant running on NVIDIA Jetson Orin Nano that detects objects and road potholes, speaks Arabic descriptions, and sends alerts via Telegram.

---

## 📌 نظرة عامة (Overview)

هذا المشروع هو نظام ذكاء اصطناعي متكامل يعمل على جهاز **NVIDIA Jetson Orin Nano**. يستخدم النظام كاميرتين CSI في وقت واحد لتنفيذ مهمتين مختلفتين:

| الكاميرا | الوظيفة | النموذج |
|----------|---------|---------|
| **Camera 0** | كشف الأجسام (Object Detection) | YOLOv8s (80 فئة) |
| **Camera 1** | كشف الحفر (Pothole Detection) | YOLOv8n مدرّب محلياً |

النظام يقوم بـ:
- **التعرف على الأجسام** وإعطاء وصف صوتي بالعربية (مثال: "أرى كرسي أمامك وطاولة على يمينك")
- **كشف حفر الطرق** تلقائياً وحفظ صور لها وإرسال تنبيهات
- **إرسال تنبيهات فورية** عبر Telegram Bot
- **عرض لوحة تحكم** عبر المتصفح (Web Dashboard)
- **قراءة بيانات الحساسات** من Arduino (اختياري)

---

## 🏗️ هيكل المشروع (Project Structure)

```
vision_voice_ai/
├── app/                        # الكود الرئيسي للتطبيق
│   ├── main.py                 # نقطة الدخول الرئيسية - الحلقة الرئيسية للمعالجة
│   ├── config.py               # إعدادات النظام (الكاميرات، الدقة، المفاتيح)
│   ├── cameras.py              # إدارة كاميرات CSI عبر GStreamer
│   ├── detector.py             # نموذج YOLOv8s لكشف الأجسام العام
│   ├── pothole_detector.py     # نموذج YOLO المحلي لكشف الحفر
│   ├── distance.py             # تقدير المسافة واتجاه الأجسام
│   ├── speech.py               # محرك الكلام (Google TTS بالعربية)
│   ├── translations.py         # ترجمة أسماء الأجسام إلى العربية
│   ├── telegram_bot.py         # بوت تيليجرام للتنبيهات والتحكم
│   ├── arduino_reader.py       # قراءة بيانات الحساسات من Arduino
│   └── web_dashboard.py        # لوحة التحكم عبر المتصفح (Flask)
├── arduino/                    # كود Arduino
│   ├── sensor_sender.ino       # الكود الرئيسي لـ Arduino Nano
│   └── sensor_sender/          # مجلد المشروع
├── scripts/                    # سكربتات التشغيل والتدريب
│   ├── run_app.sh              # سكربت تشغيل النظام الرئيسي
│   ├── train_pothole.py        # سكربت تدريب نموذج كشف الحفر
│   └── upload_arduino.sh       # رفع الكود على Arduino
├── requirements-ai.txt         # مكتبات الذكاء الاصطناعي
├── requirements-base.txt       # المكتبات الأساسية
├── .gitignore
└── README.md                   # هذا الملف
```

### المجلدات التي تُنشأ تلقائياً عند التشغيل:
```
├── pothole_snapshots/          # صور الحفر المكتشفة (تُنشأ تلقائياً)
├── pothole_logs/               # سجل CSV لجميع الاكتشافات
├── runs/                       # نتائج تدريب النماذج (Ultralytics)
├── .speech_cache/              # ملفات الصوت المخزنة مؤقتاً
└── venv/                       # البيئة الافتراضية
```

---

## ⚙️ المتطلبات (Requirements)

### الأجهزة (Hardware)
- **NVIDIA Jetson Orin Nano** (8GB)
- **2x IMX219 CSI Camera** (كاميرتين)
- **شاشة HDMI** (للعرض المحلي)
- **Arduino Nano** + حساسات (اختياري)
- **اتصال إنترنت** (فقط لـ Google TTS و Telegram)

### البرمجيات (Software)
- JetPack 6.x (Ubuntu 22.04)
- Python 3.10+
- CUDA (مع تحذير إصدار الدرايفر - لا يؤثر على العمل)

---

## 🚀 التثبيت والتشغيل (Installation & Running)

### 1. إعداد البيئة
```bash
cd ~/projects/vision_voice_ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-base.txt
pip install -r requirements-ai.txt
```

### 2. تحميل نماذج YOLO
```bash
# يتم تحميلها تلقائياً عند أول تشغيل
# yolov8s.pt - نموذج كشف الأجسام العام (22MB)
```

### 3. تدريب نموذج كشف الحفر (اختياري)
```bash
# أولاً: تحميل مجموعة البيانات
python3 -c "
import kagglehub
path = kagglehub.dataset_download('mahyeks/pothrgbd-rgb-and-depth-images-of-potholes')
print('Dataset path:', path)
"

# ثانياً: بدء التدريب
python3 scripts/train_pothole.py
# النموذج يُحفظ في: runs/detect/pothole_model/weights/best.pt
```

### 4. تشغيل النظام
```bash
./scripts/run_app.sh
```

---

## 🔧 الإعدادات (Configuration)

جميع الإعدادات موجودة في `app/config.py`:

```python
# --- الكاميرات ---
CAMERA_0_INDEX = 0              # كاميرا كشف الأجسام
CAMERA_1_INDEX = 1              # كاميرا كشف الحفر
FRAME_WIDTH = 640               # عرض الإطار
FRAME_HEIGHT = 480              # ارتفاع الإطار

# --- العرض ---
DISPLAY_ON_JETSON = True        # عرض الفيديو على شاشة الجتسن

# --- Telegram Bot ---
USE_TELEGRAM = True
TELEGRAM_BOT_TOKEN = "..."      # توكن البوت

# --- كشف الحفر ---
USE_POTHOLE_DETECTION = True
POTHOLE_CONFIDENCE = 0.5        # حد الثقة الأدنى
```

---

## 📊 النماذج المستخدمة (Models)

### 1. YOLOv8s - كشف الأجسام العام
- **الملف:** `yolov8s.pt` (22MB)
- **الفئات:** 80 فئة (أشخاص، سيارات، كراسي، إلخ)
- **الدقة:** عالية - مناسب لـ Jetson
- **الاستخدام:** Camera 0

### 2. YOLOv8n - كشف الحفر (مدرّب محلياً)
- **الملف:** `runs/detect/pothole_model/weights/best.pt`
- **الفئات:** 1 فئة (pothole)
- **مجموعة البيانات:** [Pothole RGB-D Dataset](https://www.kaggle.com/datasets/mahyeks/pothrgbd-rgb-and-depth-images-of-potholes) - 1000 صورة مع Labels
- **التدريب:** 15 epochs, imgsz=640, batch=8
- **الاستخدام:** Camera 1

---

## 🧠 كيف يعمل النظام (How It Works)

### خط أنابيب المعالجة (Processing Pipeline)

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Camera 0   │───▶│  YOLOv8s Detect  │───▶│  Arabic Speech  │
│  (CSI 0)    │    │  (80 classes)    │    │  + Telegram     │
└─────────────┘    └──────────────────┘    └─────────────────┘

┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Camera 1   │───▶│  Pothole YOLO    │───▶│  Alert + Save   │
│  (CSI 1)    │    │  (Async Thread)  │    │  Snapshot       │
└─────────────┘    └──────────────────┘    └─────────────────┘
```

### تحسينات الأداء المطبقة:
1. **المعالجة غير المتزامنة (Async):** كشف الحفر يعمل في Thread منفصل لمنع تجميد الفيديو
2. **دقة مُحسّنة:** الكاميرات تسحب بـ 1280x720 وتُعرض بـ 640x480
3. **التحميل الذكي:** النظام يكتشف تلقائياً متى ينتهي تدريب النموذج ويحمّله بدون إعادة تشغيل
4. **تخزين الصوت:** Google TTS يخزّن الملفات الصوتية محلياً لتجنب إعادة التوليد

---

## 📱 بوت تيليجرام (Telegram Bot)

البوت يعمل تلقائياً ويرسل تنبيهات عند:
- كشف حفرة في الطريق (مع صورة)
- كشف سقوط شخص (من Arduino)

**الأوامر المتاحة:**
- `/help` - عرض الأوامر
- `/status` - حالة النظام

**اسم البوت:** `@DumbWarning_Bot`

---

## 🔌 Arduino (اختياري)

النظام يدعم Arduino Nano لقراءة بيانات الحساسات:
- **MPU6050** - كشف السقوط (Fall Detection)
- **حساسات إضافية** - درجة الحرارة، الرطوبة

الكود موجود في `arduino/sensor_sender.ino`

لرفع الكود:
```bash
./scripts/upload_arduino.sh
```

---

## 🌐 لوحة التحكم (Web Dashboard)

يمكن الوصول إلى لوحة التحكم عبر المتصفح:
```
http://<jetson-ip>:8000
```

تعرض:
- حالة النظام (تشغيل/إيقاف)
- عدد الكاميرات النشطة
- عدد الحفر المكتشفة
- آخر إطار من الكاميرا

---

## ⚠️ ملاحظات مهمة

1. **تحذير CUDA:** يظهر تحذير عن إصدار الدرايفر (`found version 12060`) - هذا لا يؤثر على عمل النظام ولكن التدريب يتم على CPU حتى يُحدّث الدرايفر.

2. **الكاميرتين:** يجب أن تكون الكاميرتين من نوع IMX219 CSI. لا يمكن استخدام USB cameras مع هذا الكود.

3. **الشاشة:** لعرض الفيديو محلياً يجب توصيل شاشة HDMI بالجتسن. السكربت يضبط `DISPLAY=:0` تلقائياً.

4. **الإنترنت:** مطلوب فقط لـ:
   - Google TTS (توليد الصوت) - يتم تخزينه محلياً بعد أول مرة
   - Telegram Bot (إرسال التنبيهات)
   - كشف الحفر يعمل محلياً بالكامل (Offline)

---

## 👨‍💻 المطورون

- **Ayham** - [GitHub](https://github.com/Ayham255)

---

## 📄 الترخيص

هذا المشروع تم تطويره كمشروع تخرج. جميع الحقوق محفوظة.

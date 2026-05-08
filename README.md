# 🔍 Rubika OSINT Platform
> An Enterprise-Grade, Async, and Dockerized bot for extracting hidden Rubika IDs (Users, Channels, and Groups).

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED.svg?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📌 معرفی پروژه (About)
این پروژه یک پلتفرم پیشرفته و مقیاس‌پذیر برای بستر روبیکا (Rubika) است که به عنوان یک ابزار OSINT عمل می‌کند. با استفاده از این ربات، می‌توانید پیام‌های هدایت‌شده (Forwarded) را آنالیز کرده و شناسه‌های (IDs) پنهان سیستمی را استخراج کنید.

**قابلیت‌های استخراج:**
- 📢 **کانال‌ها:** استخراج آیدی کانال‌های عمومی و خصوصی (شناسه‌های `c0...`)
- 👥 **گروه‌ها:** استخراج آیدی گروه‌ها (شناسه‌های `g0...`)
- 👤 **کاربران:** استخراج آیدی اشخاص (شناسه‌های `u0...`)

## 🚀 ویژگی‌های فنی (Technical Features)
- **معماری Asynchronous:** نوشته شده با کتابخانه قدرتمند `aiohttp` برای پردازش همزمان هزاران پیام بدون افت سرعت.
- **ایزوله‌سازی کانتینری:** داکرایز شده (Dockerized) به صورت کامل. بدون نیاز به نصب پایتون یا تنظیم محیط در سرور مقصد.
- **مدیریت تکرار (Deduplication):** استفاده از `Redis` برای جلوگیری از پردازش پیام‌های تکراری و کاهش بار ترافیکی.
- **ذخیره‌سازی دائمی (Persistence):** ذخیره تمام آیدی‌های کشف شده همراه با متادیتا در دیتابیس `PostgreSQL`.
- **لاگینگ سازمانی (Enterprise Logging):** خروجی لاگ‌ها به فرمت دقیق JSON جهت اتصال آسان به پشته‌های ELK یا Grafana.

---

## ⚙️ پیش‌نیازها (Prerequisites)
برای اجرای این پروژه، تنها به موارد زیر نیاز دارید:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- توکن ربات روبیکا (دریافت از بات‌فادر روبیکا)

---

## 🛠️ نصب و راه‌اندازی (Installation & Setup)

**۱. کلون کردن مخزن:**
```bash
git clone [https://github.com/YOUR_USERNAME/Rubika-OSINT-Platform.git](https://github.com/YOUR_USERNAME/Rubika-OSINT-Platform.git)
cd Rubika-OSINT-Platform
import os
import re
import sys
import json
import io

# Принудительно ставим UTF-8 для вывода в консоль Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# === НАСТРОЙКИ ===
BASE_URL = "http://km-eng.ru/"
OUTPUT_DIR = "scraped_data"
IMG_DIR = os.path.join(OUTPUT_DIR, "images")

# Создаём папки
os.makedirs(IMG_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def fetch_page(url):
    """Загрузить HTML страницы."""
    print(f"[*] Загружаю страницу: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.encoding = 'utf-8'
    resp.raise_for_status()
    return resp.text


def extract_image_urls(soup, base_url):
    """Извлечь ВСЕ URL изображений: src, data-original, data-src, srcset, CSS background."""
    urls = set()

    # 1. Тег <img> — src, data-original, data-src, data-lazy
    for img in soup.find_all('img'):
        for attr in ['src', 'data-original', 'data-src', 'data-lazy', 'data-bg-src']:
            val = img.get(attr)
            if val and not val.startswith('data:'):
                urls.add(urljoin(base_url, val))
        # srcset
        srcset = img.get('srcset', '')
        if srcset:
            for part in srcset.split(','):
                src = part.strip().split()[0]
                if src and not src.startswith('data:'):
                    urls.add(urljoin(base_url, src))

    # 2. Фоновые изображения в style="" атрибутах
    for tag in soup.find_all(style=True):
        style = tag['style']
        bg_urls = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
        for u in bg_urls:
            if not u.startswith('data:'):
                urls.add(urljoin(base_url, u))

    # 3. Все data-атрибуты с URL на изображения (типично для Тильды)
    img_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.bmp')
    for tag in soup.find_all(True):
        for attr_name, attr_val in tag.attrs.items():
            if isinstance(attr_val, str) and attr_name.startswith('data-'):
                # Проверяем, похож ли на URL изображения
                if any(attr_val.lower().endswith(ext) for ext in img_extensions):
                    urls.add(urljoin(base_url, attr_val))
                elif 'static.tildacdn.com' in attr_val:
                    urls.add(urljoin(base_url, attr_val))

    # 4. CSS-блоки <style> внутри HTML
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            bg_urls = re.findall(r'url\(["\']?(.*?)["\']?\)', style_tag.string)
            for u in bg_urls:
                if not u.startswith('data:'):
                    urls.add(urljoin(base_url, u))

    # 5. Тег <source> (для <picture>)
    for source in soup.find_all('source'):
        for attr in ['src', 'srcset']:
            val = source.get(attr, '')
            if val:
                for part in val.split(','):
                    src = part.strip().split()[0]
                    if src and not src.startswith('data:'):
                        urls.add(urljoin(base_url, src))

    # 6. Фавикон и мета-изображения
    for link in soup.find_all('link', rel=True):
        if any(r in link.get('rel', []) for r in ['icon', 'shortcut', 'apple-touch-icon']):
            href = link.get('href')
            if href:
                urls.add(urljoin(base_url, href))

    for meta in soup.find_all('meta'):
        if meta.get('property') in ['og:image', 'twitter:image']:
            content = meta.get('content')
            if content:
                urls.add(urljoin(base_url, content))

    return urls


def download_image(url, save_dir, index):
    """Скачать одно изображение и сохранить с оригинальным именем."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # Получаем имя файла из URL
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)

        if not filename or filename == '/':
            filename = f"image_{index}.jpg"

        # Если расширения нет, определяем по Content-Type
        if '.' not in filename:
            content_type = resp.headers.get('Content-Type', '')
            ext_map = {
                'image/jpeg': '.jpg', 'image/png': '.png',
                'image/gif': '.gif', 'image/svg+xml': '.svg',
                'image/webp': '.webp', 'image/x-icon': '.ico',
            }
            ext = ext_map.get(content_type.split(';')[0].strip(), '.jpg')
            filename += ext

        # Уникализируем имя файла при дубликатах
        filepath = os.path.join(save_dir, filename)
        counter = 1
        base, ext = os.path.splitext(filename)
        while os.path.exists(filepath):
            filepath = os.path.join(save_dir, f"{base}_{counter}{ext}")
            counter += 1

        with open(filepath, 'wb') as f:
            f.write(resp.content)

        size_kb = len(resp.content) / 1024
        print(f"   ✓ {os.path.basename(filepath)} ({size_kb:.1f} KB)")
        return os.path.basename(filepath)

    except Exception as e:
        print(f"   ✗ Ошибка: {url} — {e}")
        return None


def extract_structured_content(soup):
    """Извлечь структурированный контент сайта с сохранением иерархии."""
    content = {
        "meta": {},
        "sections": []
    }

    # Мета-информация
    title = soup.find('title')
    content["meta"]["title"] = title.get_text(strip=True) if title else ""

    desc = soup.find('meta', attrs={'name': 'description'})
    content["meta"]["description"] = desc['content'] if desc and desc.get('content') else ""

    og_desc = soup.find('meta', attrs={'property': 'og:description'})
    content["meta"]["og_description"] = og_desc['content'] if og_desc and og_desc.get('content') else ""

    # Телефон
    phone_links = soup.find_all('a', href=re.compile(r'^tel:'))
    content["meta"]["phones"] = [a.get('href', '').replace('tel:', '') for a in phone_links]

    # Email
    email_links = soup.find_all('a', href=re.compile(r'^mailto:'))
    content["meta"]["emails"] = [a.get('href', '').replace('mailto:', '') for a in email_links]

    # Навигация
    nav_items = []
    for nav_link in soup.select('.t-menulinks__item a, .t-menu__link-item a, nav a, .t228__menu a'):
        text = nav_link.get_text(strip=True)
        href = nav_link.get('href', '')
        if text:
            nav_items.append({"text": text, "href": href})
    content["navigation"] = nav_items

    # Секции Тильды (rec блоки)
    tilda_recs = soup.find_all(id=re.compile(r'^rec\d+'))
    if tilda_recs:
        for rec in tilda_recs:
            section = extract_section(rec)
            if section["headings"] or section["texts"] or section["buttons"] or section["list_items"]:
                content["sections"].append(section)
    else:
        # Если не Tilda-стиль, собираем из стандартных тегов
        section = extract_section(soup.body if soup.body else soup)
        content["sections"].append(section)

    return content


def extract_section(element):
    """Извлечь контент из одной секции."""
    section = {
        "id": element.get('id', ''),
        "data_record_type": element.get('data-record-type', ''),
        "headings": [],
        "texts": [],
        "buttons": [],
        "list_items": [],
        "images_alt": [],
    }

    # Заголовки
    for tag_name in ['h1', 'h2', 'h3', 'h4']:
        for h in element.find_all(tag_name):
            text = h.get_text(strip=True)
            if text:
                section["headings"].append({"level": tag_name, "text": text})

    # Тексты (абзацы и div-тексты)
    for p in element.find_all(['p', 'div']):
        text = p.get_text(strip=True)
        # Фильтр: минимум содержания, не дубликат заголовка
        if len(text) > 10 and not any(h["text"] == text for h in section["headings"]):
            # Не берём вложенные DIV-ы с тем же текстом
            if p.name == 'div' and p.find(['h1', 'h2', 'h3', 'h4', 'p']):
                continue
            section["texts"].append(text)

    # Кнопки
    for btn in element.find_all(['a', 'button'], class_=re.compile(r'btn|button', re.I)):
        text = btn.get_text(strip=True)
        href = btn.get('href', '')
        if text:
            section["buttons"].append({"text": text, "href": href})

    # Списки
    for li in element.find_all('li'):
        text = li.get_text(strip=True)
        if text and len(text) > 5:
            section["list_items"].append(text)

    # Alt-тексты изображений
    for img in element.find_all('img'):
        alt = img.get('alt', '').strip()
        if alt:
            section["images_alt"].append(alt)

    # Убираем дубликаты текстов
    seen = set()
    unique_texts = []
    for t in section["texts"]:
        if t not in seen:
            seen.add(t)
            unique_texts.append(t)
    section["texts"] = unique_texts

    return section


def save_text_readable(content, filepath):
    """Сохранить контент в читабельном текстовом формате."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"=== {content['meta'].get('title', 'Без названия')} ===\n\n")

        if content['meta'].get('description'):
            f.write(f"Описание: {content['meta']['description']}\n")
        if content['meta'].get('phones'):
            f.write(f"Телефон: {', '.join(content['meta']['phones'])}\n")
        if content['meta'].get('emails'):
            f.write(f"Email: {', '.join(content['meta']['emails'])}\n")
        f.write("\n")

        if content.get('navigation'):
            f.write("--- НАВИГАЦИЯ ---\n")
            for nav in content['navigation']:
                f.write(f"  • {nav['text']} → {nav['href']}\n")
            f.write("\n")

        f.write("--- СОДЕРЖАНИЕ САЙТА ---\n\n")
        for i, section in enumerate(content['sections'], 1):
            section_id = section.get('id', f'section_{i}')
            rec_type = section.get('data_record_type', '')
            f.write(f"══ Секция: {section_id}")
            if rec_type:
                f.write(f" (тип: {rec_type})")
            f.write(" ══\n\n")

            for h in section['headings']:
                prefix = '#' * int(h['level'][1])
                f.write(f"{prefix} {h['text']}\n")

            if section['headings']:
                f.write("\n")

            for text in section['texts']:
                f.write(f"{text}\n\n")

            if section['buttons']:
                f.write("Кнопки:\n")
                for btn in section['buttons']:
                    f.write(f"  [Кнопка: {btn['text']}] → {btn['href']}\n")
                f.write("\n")

            if section['list_items']:
                f.write("Список:\n")
                for item in section['list_items']:
                    f.write(f"  • {item}\n")
                f.write("\n")

            f.write("\n")


# ═══════════════════════════════════════════════
#              ОСНОВНОЙ СКРИПТ
# ═══════════════════════════════════════════════

print("═" * 50)
print("  СКРАПЕР САЙТА km-eng.ru")
print("═" * 50)

# 1. Загружаем страницу
html = fetch_page(BASE_URL)
soup = BeautifulSoup(html, "html.parser")
print("[✓] Страница загружена успешно\n")

# 2. Извлекаем и сохраняем текстовый контент
print("[*] Извлекаю текстовый контент...")
content = extract_structured_content(soup)

# Сохраняем в JSON (для программной обработки)
json_path = os.path.join(OUTPUT_DIR, "site_content.json")
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(content, f, ensure_ascii=False, indent=2)
print(f"   ✓ JSON: {json_path}")

# Сохраняем в TXT (для чтения)
txt_path = os.path.join(OUTPUT_DIR, "site_content.txt")
save_text_readable(content, txt_path)
print(f"   ✓ TXT:  {txt_path}")

sections_count = len(content['sections'])
print(f"   Найдено секций: {sections_count}\n")

# 3. Скачиваем изображения
print("[*] Ищу изображения...")
image_urls = extract_image_urls(soup, BASE_URL)
print(f"   Найдено уникальных URL изображений: {len(image_urls)}\n")

print("[*] Скачиваю изображения...")
downloaded = []
for i, img_url in enumerate(sorted(image_urls)):
    result = download_image(img_url, IMG_DIR, i)
    if result:
        downloaded.append({"original_url": img_url, "local_file": result})

# Сохраняем маппинг изображений
img_map_path = os.path.join(OUTPUT_DIR, "images_map.json")
with open(img_map_path, 'w', encoding='utf-8') as f:
    json.dump(downloaded, f, ensure_ascii=False, indent=2)

# 4. Сохраняем исходный HTML
html_path = os.path.join(OUTPUT_DIR, "original_page.html")
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n   ✓ Исходный HTML сохранён: {html_path}")

# Итого
print("\n" + "═" * 50)
print("  ГОТОВО!")
print("═" * 50)
print(f"""
📁 Результаты в папке: {OUTPUT_DIR}/
   📄 site_content.json  — структурированный контент (JSON)
   📄 site_content.txt   — читабельный контент (текст)
   📄 images_map.json    — маппинг оригинальных URL → локальные файлы
   📄 original_page.html — исходный HTML страницы
   🖼️  images/            — скачанные изображения ({len(downloaded)} шт.)
""")

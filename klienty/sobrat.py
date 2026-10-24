#!/usr/bin/env python3
"""Собирает страницу клиентов klienty/index.html из открытых данных на Маке.

Открытые данные: ~/КОМПЛЕКТ-КЛОД/клиенты/данные.json — в GitHub НЕ попадают.
Пароль: связка ключей macOS, запись «klienty-stranitsa» (аккаунт timur).
На выходе index.html с зашифрованными данными: AES-256-GCM, ключ из пароля через PBKDF2-SHA256.
Пароль в вывод не печатается.

Запуск: python3 sobrat.py          — только собрать
        python3 sobrat.py --push   — собрать и отправить на GitHub
"""
import base64, hashlib, json, os, subprocess, sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PAPKA = Path(__file__).resolve().parent
DANNYE = Path.home() / "КОМПЛЕКТ-КЛОД" / "клиенты" / "данные.json"
ITER = 600_000


def parol():
    r = subprocess.run(["security", "find-generic-password", "-a", "timur", "-s", "klienty-stranitsa", "-w"],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit("Нет пароля в связке ключей (klienty-stranitsa). Задай: security add-generic-password -a timur -s klienty-stranitsa -w")
    return r.stdout.rstrip("\n")


def zashifrovat(tekst, p):
    salt, iv = os.urandom(16), os.urandom(12)
    kluch = hashlib.pbkdf2_hmac("sha256", p.encode(), salt, ITER, dklen=32)
    data = AESGCM(kluch).encrypt(iv, tekst.encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    paket = json.dumps({"salt": b(salt), "iv": b(iv), "iter": ITER, "data": b(data)})
    return base64.b64encode(paket.encode()).decode()


def main():
    tekst = DANNYE.read_text(encoding="utf-8")
    json.loads(tekst)  # падаем сразу, если в данных ошибка
    shablon = (PAPKA / "shablon.html").read_text(encoding="utf-8")
    assert '"__SHIFR__"' in shablon, "в шаблоне нет места для данных"
    html = shablon.replace('"__SHIFR__"', '"' + zashifrovat(tekst, parol()) + '"')
    # проверка: ни одной открытой строки из данных в готовой странице
    for kusok in ("Чанкин", "Андрей"):
        if kusok in tekst and kusok in html:
            sys.exit(f"СТОП: в странице открытым текстом «{kusok}» — не публикую")
    (PAPKA / "index.html").write_text(html, encoding="utf-8")
    print("собрано:", PAPKA / "index.html")

    if "--push" in sys.argv:
        repo = PAPKA.parent
        subprocess.run(["git", "-C", str(repo), "add", "klienty/index.html", "klienty/shablon.html", "klienty/sobrat.py"], check=True)
        r = subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--quiet"])
        if r.returncode == 0:
            print("изменений нет")
            return
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "Клиенты: обновление страницы"], check=True)
        subprocess.run(["git", "-C", str(repo), "push", "-q"], check=True)
        print("отправлено: https://timuriskhakovv.github.io/klienty/")


if __name__ == "__main__":
    main()

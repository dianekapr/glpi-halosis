#!/usr/bin/env bash
# Pasang HaloSIS di laptop dengan SATU perintah (langkah 1–7 README dijalankan berurutan). Aman diulang: yang sudah
# ada tidak dibuat dua kali, data contoh tidak digandakan.
#
#   scripts/pasang.sh            # Mac/Linux: Terminal; Windows: Git Bash
#
# Butuh: Docker Desktop (menyala) dan Python 3. Pertama kali bisa 10–20 menit (mengunduh beberapa GB).
set -euo pipefail
cd "$(dirname "$0")/.."

BASE=http://localhost:8080
langkah() { printf '\n\033[1m[%s] %s\033[0m\n' "$1" "$2"; }
gagal()   { printf '\n\033[31mGAGAL: %s\033[0m\n' "$1" >&2; exit 1; }
console() { docker compose exec -T glpi php bin/console "$@" --allow-superuser >/dev/null; }
setcfg()  { console config:set "$1" "$2"; }

langkah 1/8 "Memeriksa Docker & Python"
docker info >/dev/null 2>&1 || gagal "Docker belum menyala. Buka aplikasi Docker Desktop, tunggu ikon paus diam, lalu ulangi."
PY_SYS=$(command -v python3 || command -v python || true)
[ -n "$PY_SYS" ] || gagal "Python 3 belum terpasang (lihat README › Persiapan)."
[ -f .env ] || { cp .env.example .env; echo "File pengaturan .env dibuat dari .env.example"; }

langkah 2/8 "Menyalakan semua layanan (pertama kali 10–20 menit)"
docker compose up -d
printf 'Menunggu GLPI siap'
for _ in $(seq 1 120); do
  curl -s "$BASE/" 2>/dev/null | grep -q 'login_name' && break
  printf '.'; sleep 5
done
echo
curl -s "$BASE/" | grep -q 'login_name' || gagal "GLPI belum siap setelah 10 menit. Cek: docker compose logs --tail 50 glpi"

langkah 3/8 "Mengaktifkan API GLPI (dipakai skrip pengisi data)"
setcfg enable_api 1
setcfg enable_api_login_credentials 1
# Laptop memanggil API lewat gateway Docker; izinkan rentang IP gateway itu (sekali saja)
answer=$(curl -s -u glpi:glpi "$BASE/apirest.php/initSession" || true)
if echo "$answer" | grep -q ERROR_NOT_ALLOWED_IP; then
  ip=$(echo "$answer" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1)
  [ -n "$ip" ] || gagal "API menolak IP laptop, tetapi IP-nya tidak terbaca. Lihat README › Bagian teknis › langkah 3."
  net=${ip%.*}
  docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null' <<SQL
INSERT INTO glpi_apiclients (entities_id,is_recursive,name,date_creation,is_active,ipv4_range_start,ipv4_range_end,dolog_method)
VALUES (0,1,'HaloSIS lokal (gateway Docker ${net}.x)',NOW(),1,INET_ATON('${net}.0'),INET_ATON('${net}.255'),0);
SQL
  echo "Rentang IP ${net}.0–${net}.255 diizinkan"
fi
curl -s -u glpi:glpi "$BASE/apirest.php/initSession" | grep -q session_token || gagal "API GLPI belum bisa dipakai (lihat README › Bagian teknis › langkah 3)."

langkah 4/8 "Memasang plugin HaloSIS & peran pengguna"
printf 'Menunggu layanan AI'
for _ in $(seq 1 60); do
  curl -s http://localhost:8001/health 2>/dev/null | grep -q '"status"' && break
  printf '.'; sleep 5
done
echo
console plugin:install halosis -u glpi --force
console plugin:activate halosis
console plugins:halosis:setup-roles

langkah 5/8 "Mengisi data contoh (tim, pengguna, tiket, artikel, SLA)"
[ -d .venv ] || "$PY_SYS" -m venv .venv
PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python   # Windows
"$PY" -m pip install -q requests
"$PY" seed_halosis.py "$BASE"
"$PY" setup_sla_alerts.py "$BASE"
"$PY" setup_pejabat_rules.py "$BASE"
"$PY" setup_list_columns.py "$BASE"

langkah 6/8 "Notifikasi & email uji (Mailpit)"
setcfg use_notifications 1
setcfg notifications_ajax 1
setcfg smtp_mode 1
setcfg smtp_host mailpit
setcfg smtp_port 1025
setcfg smtp_username ''
setcfg smtp_check_certificate 0
setcfg from_email halosis@bps.local
setcfg admin_email halosis@bps.local
setcfg notifications_mailing 1

langkah 7/8 "Tampilan HaloSIS (warna, bahasa, teks login)"
setcfg palette halosis
setcfg language id_ID
setcfg text_login '<p style="text-align:center">Selamat datang di <strong>HaloSIS</strong>, layanan TI BPS.<br>Masuk dengan akun dinas Anda.</p>'
setcfg display_login_source 0
setcfg login_remember_time 0     # bug GLPI 12.0.0 "Remember me" (README › Bagian teknis)
for pair in 6:#c92a2a 5:#e03131 4:#f76707 3:#f59f00 2:#868e96 1:#adb5bd; do setcfg "priority_${pair%%:*}" "${pair#*:}"; done
setcfg duedateok_color '#2f9e44'
setcfg duedatewarning_color '#f76707'
setcfg duedatecritical_color '#e03131'
# Container sudah menjalankan cron tiap menit → aksi otomatis mode CLI
docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "UPDATE glpi_crontasks SET mode=2 WHERE mode=1" 2>/dev/null'

langkah 8/8 "Membersihkan cache"
console cache:clear

cat <<'SELESAI'

Selesai! Buka http://localhost:8080 di browser.
  • Pegawai        : budi  / halosis   (tanya chatbot, buat laporan)
  • Operator       : rina  / halosis   (periksa saran AI)
  • Tim Teknis     : andi  / halosis   (kerjakan tiket)
  • Manajemen      : sri   / halosis   (dashboard)
  • Pengelola      : glpi  / glpi      (Super-Admin; ganti password-nya bila dipakai di jaringan)
Model AI sungguhan (opsional) dipasang terpisah: README › Untuk anggota tim › C2.
SELESAI

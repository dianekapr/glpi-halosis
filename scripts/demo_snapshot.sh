#!/usr/bin/env bash
# Snapshot kondisi demo HaloSIS: database GLPI + data Keycloak (realm, pengguna, role) + indeks AI (ai/index) ke folder
# backup/ (di-ignore git).
#
#   scripts/demo_snapshot.sh simpan              # buat snapshot baru: backup/demo-<waktu>/, lalu tandai "terakhir"
#   scripts/demo_snapshot.sh pulihkan [folder]   # kembalikan ke snapshot terakhir (atau folder yang disebut)
#
# Pulihkan TIDAK menghapus volume Docker: semua tabel DB glpi diganti isi dump (tabel yang dibuat setelah snapshot
# dibuang), lalu isi folder data Keycloak diganti arsipnya (Keycloak dihentikan sebentar karena H2 terkunci saat jalan).
# Indeks AI dipulihkan agar artikel yang diterbitkan setelah snapshot tidak lagi dikutip chatbot (halosis-ai di-restart).
# Tidak ikut: berkas lampiran GLPI (volume glpi_data).
set -euo pipefail
cd "$(dirname "$0")/.."
BACKUP_DIR=backup
mysql_in_db() { docker compose exec -T db sh -c "$1"; }
keycloak_volume() {
  docker inspect "$(docker compose ps -aq keycloak)" \
    --format '{{range .Mounts}}{{if eq .Destination "/opt/keycloak/data"}}{{.Name}}{{end}}{{end}}'
}

# Path host untuk bind mount docker: di Git Bash/MSYS pakai bentuk Windows (C:/...) dan matikan konversi path otomatis.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) host_path() { (cd "$1" && pwd -W); }; export MSYS_NO_PATHCONV=1 ;;
  *) host_path() { (cd "$1" && pwd); } ;;
esac

simpan() {
  local dir="$BACKUP_DIR/demo-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$dir"
  echo "1/4 Dump database GLPI…"
  mysql_in_db 'mysqldump --single-transaction --routines --no-tablespaces -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null' \
    | gzip > "$dir/glpi.sql.gz"
  echo "2/4 Salin indeks AI…"
  mkdir -p ai/index
  cp -R ai/index "$dir/ai-index"
  echo "3/4 Arsip data Keycloak (Keycloak berhenti ±20 detik)…"
  local vol hd; vol=$(keycloak_volume); hd=$(host_path "$dir")
  docker compose stop keycloak >/dev/null
  if ! docker run --rm -v "$vol":/data:ro -v "$hd":/backup alpine:3.22 sh -c 'tar czf /backup/keycloak-data.tgz -C /data . && test -s /backup/keycloak-data.tgz'; then
    docker compose start keycloak >/dev/null
    echo "GAGAL: arsip Keycloak tidak terbentuk (folder host tidak terbaca container: $hd). Keycloak tidak diubah." >&2
    exit 1
  fi
  docker compose start keycloak >/dev/null
  echo "4/4 Ringkasan"
  mysql_in_db 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "SELECT COUNT(*) FROM glpi_tickets" 2>/dev/null' \
    | xargs -I{} echo "tickets={}" > "$dir/ringkasan.txt"
  ln -sfn "$(basename "$dir")" "$BACKUP_DIR/terakhir"
  echo "Snapshot: $dir ($(du -sh "$dir" | cut -f1), $(cat "$dir/ringkasan.txt"))"
}

pulihkan() {
  local dir="${1:-$BACKUP_DIR/terakhir}"
  [ -f "$dir/glpi.sql.gz" ] && [ -f "$dir/keycloak-data.tgz" ] || { echo "Snapshot tidak lengkap: $dir" >&2; exit 1; }
  echo "1/5 Kosongkan tabel database GLPI (database & volume tetap)…"
  mysql_in_db 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "SELECT CONCAT(\"DROP TABLE IF EXISTS \`\", table_name, \"\`;\") FROM information_schema.tables WHERE table_schema = DATABASE()" 2>/dev/null' \
    | { echo 'SET FOREIGN_KEY_CHECKS=0;'; cat; } \
    | docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'
  echo "2/5 Muat dump…"
  gunzip -c "$dir/glpi.sql.gz" | docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'
  echo "3/5 Pulihkan data Keycloak (Keycloak berhenti ±20 detik)…"
  local vol hd; vol=$(keycloak_volume); hd=$(host_path "$dir")
  docker compose stop keycloak >/dev/null
  # Cek arsip terbaca dari DALAM container sebelum menghapus /data; bila gagal, Keycloak tidak diubah.
  if ! docker run --rm -v "$vol":/data -v "$hd":/backup:ro alpine:3.22 \
    sh -c 'test -s /backup/keycloak-data.tgz && tar tzf /backup/keycloak-data.tgz >/dev/null && find /data -mindepth 1 -delete && tar xzf /backup/keycloak-data.tgz -C /data'; then
    docker compose start keycloak >/dev/null
    echo "GAGAL: /backup/keycloak-data.tgz tidak terbaca di container (folder host: $hd). Data Keycloak tidak diubah." >&2
    exit 1
  fi
  docker compose start keycloak >/dev/null
  echo "4/5 Kosongkan cache GLPI"
  docker compose exec -T glpi php bin/console cache:clear --allow-superuser >/dev/null
  if [ -d "$dir/ai-index" ]; then
    echo "5/5 Pulihkan indeks AI & restart halosis-ai…"
    cp "$dir/ai-index/"*.parquet "$dir/ai-index/"*.npy ai/index/
    docker compose restart halosis-ai >/dev/null
  else
    echo "5/5 Snapshot lama tanpa indeks AI: indeks dibiarkan"
  fi
  echo "Dipulihkan dari $dir ($(cat "$dir/ringkasan.txt" 2>/dev/null))"
}

case "${1:-}" in
  simpan) simpan ;;
  pulihkan) pulihkan "${2:-}" ;;
  *) echo "Pakai: $0 simpan | pulihkan [folder]" >&2; exit 2 ;;
esac

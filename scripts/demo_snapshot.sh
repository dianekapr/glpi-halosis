#!/usr/bin/env bash
# Snapshot kondisi demo HaloSIS: database GLPI + data Keycloak (realm, pengguna, role) ke folder backup/ (di-ignore git).
#
#   scripts/demo_snapshot.sh simpan              # buat snapshot baru: backup/demo-<waktu>/, lalu tandai "terakhir"
#   scripts/demo_snapshot.sh pulihkan [folder]   # kembalikan ke snapshot terakhir (atau folder yang disebut)
#
# Pulihkan TIDAK menghapus volume Docker: semua tabel DB glpi diganti isi dump (tabel yang dibuat setelah snapshot
# dibuang), lalu isi folder data Keycloak diganti arsipnya (Keycloak dihentikan sebentar karena H2 terkunci saat jalan).
# Tidak ikut: berkas lampiran GLPI (volume glpi_data) dan indeks AI (ai/index), yang tidak berubah selama demo biasa.
set -euo pipefail
cd "$(dirname "$0")/.."
BACKUP_DIR=backup
mysql_in_db() { docker compose exec -T db sh -c "$1"; }
keycloak_volume() {
  docker inspect "$(docker compose ps -aq keycloak)" \
    --format '{{range .Mounts}}{{if eq .Destination "/opt/keycloak/data"}}{{.Name}}{{end}}{{end}}'
}

simpan() {
  local dir="$BACKUP_DIR/demo-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$dir"
  echo "1/3 Dump database GLPI…"
  mysql_in_db 'mysqldump --single-transaction --routines --no-tablespaces -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null' \
    | gzip > "$dir/glpi.sql.gz"
  echo "2/3 Arsip data Keycloak (Keycloak berhenti ±20 detik)…"
  local vol; vol=$(keycloak_volume)
  docker compose stop keycloak >/dev/null
  docker run --rm -v "$vol":/data:ro -v "$PWD/$dir":/backup alpine:3.22 tar czf /backup/keycloak-data.tgz -C /data .
  docker compose start keycloak >/dev/null
  echo "3/3 Ringkasan"
  mysql_in_db 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "SELECT COUNT(*) FROM glpi_tickets" 2>/dev/null' \
    | xargs -I{} echo "tickets={}" > "$dir/ringkasan.txt"
  ln -sfn "$(basename "$dir")" "$BACKUP_DIR/terakhir"
  echo "Snapshot: $dir ($(du -sh "$dir" | cut -f1), $(cat "$dir/ringkasan.txt"))"
}

pulihkan() {
  local dir="${1:-$BACKUP_DIR/terakhir}"
  [ -f "$dir/glpi.sql.gz" ] && [ -f "$dir/keycloak-data.tgz" ] || { echo "Snapshot tidak lengkap: $dir" >&2; exit 1; }
  echo "1/4 Kosongkan tabel database GLPI (database & volume tetap)…"
  mysql_in_db 'mysql -N -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "SELECT CONCAT(\"DROP TABLE IF EXISTS \`\", table_name, \"\`;\") FROM information_schema.tables WHERE table_schema = DATABASE()" 2>/dev/null' \
    | { echo 'SET FOREIGN_KEY_CHECKS=0;'; cat; } \
    | docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'
  echo "2/4 Muat dump…"
  gunzip -c "$dir/glpi.sql.gz" | docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null'
  echo "3/4 Pulihkan data Keycloak (Keycloak berhenti ±20 detik)…"
  local vol; vol=$(keycloak_volume)
  docker compose stop keycloak >/dev/null
  docker run --rm -v "$vol":/data -v "$PWD/$dir":/backup:ro alpine:3.22 \
    sh -c 'find /data -mindepth 1 -delete && tar xzf /backup/keycloak-data.tgz -C /data'
  docker compose start keycloak >/dev/null
  echo "4/4 Kosongkan cache GLPI"
  docker compose exec -T glpi php bin/console cache:clear --allow-superuser >/dev/null
  echo "Dipulihkan dari $dir ($(cat "$dir/ringkasan.txt" 2>/dev/null))"
}

case "${1:-}" in
  simpan) simpan ;;
  pulihkan) pulihkan "${2:-}" ;;
  *) echo "Pakai: $0 simpan | pulihkan [folder]" >&2; exit 2 ;;
esac

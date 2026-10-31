// Uji beban API GLPI kondisi Normal (NFR-01): initSession → buat tiket → killSession, akun lokal uji (bukan SSO).
// Tiket uji berjudul "K6UJI …" dan harus dihapus setelah uji (lihat reports/rencana_uji.md §7).
//   (klien API GLPI dibatasi IP, jadi lewat port host, bukan jaringan docker)
//   docker run --rm -i -v "$PWD/tests/load:/scripts" -e GLPI_URL=http://host.docker.internal:8080 \
//     -e GLPI_USER=glpi -e GLPI_PASSWORD=*** grafana/k6 run /scripts/glpi_api.js
import http from 'k6/http';
import encoding from 'k6/encoding';
import { check, sleep } from 'k6';

const API = (__ENV.GLPI_URL || 'http://glpi') + '/apirest.php';
const AUTH = 'Basic ' + encoding.b64encode(`${__ENV.GLPI_USER}:${__ENV.GLPI_PASSWORD}`);
const TITLES = ['printer lantai 3 macet', 'vpn putus saat rapat', 'tidak bisa login sso', 'fasih gagal sinkron'];

export const options = {
    scenarios: { normal: { executor: 'constant-vus', vus: Number(__ENV.VUS || 10), duration: __ENV.DURATION || '5m' } },
    thresholds: {
        'http_req_failed': ['rate<0.01'],
        'http_req_duration{endpoint:ticket}': ['p(95)<1000'],
    },
};

export default function () {
    const init = http.get(`${API}/initSession`, { headers: { Authorization: AUTH }, tags: { endpoint: 'session' } });
    if (!check(init, { 'initSession 200': (r) => r.status === 200 })) {
        sleep(5);
        return;
    }
    const headers = { 'Session-Token': init.json('session_token'), 'Content-Type': 'application/json' };
    const name = `K6UJI ${TITLES[Math.floor(Math.random() * TITLES.length)]}`;
    const res = http.post(`${API}/Ticket`, JSON.stringify({ input: { name, content: `${name}, mohon dibantu (uji beban)`, type: 1 } }),
        { headers, tags: { endpoint: 'ticket' } });
    check(res, { 'ticket 201': (r) => r.status === 201 });
    http.get(`${API}/killSession`, { headers, tags: { endpoint: 'session' } });
    sleep(3 + Math.random() * 5);
}

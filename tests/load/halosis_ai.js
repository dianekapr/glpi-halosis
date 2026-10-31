// Uji beban layanan AI HaloSIS (NFR-01/NFR-12): /chat & /triage langsung ke halosis-ai, kalimat buatan (tanpa data asli).
// Jalankan di jaringan docker-compose (lihat reports/rencana_uji.md §7):
//   docker run --rm -i --network glpi-halosis_default -v "$PWD/tests/load:/scripts" grafana/k6 run /scripts/halosis_ai.js
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.AI_URL || 'http://halosis-ai:8000';
const QUESTIONS = [
    'tidak bisa login sso sejak pagi',
    'aplikasi fasih gagal sinkron data',
    'vpn kantor sering terputus',
    'lampiran email lebih dari 10 MB tidak terkirim',
    'printer lantai tiga tidak bisa mencetak',
    'cara reset password akun bps',
    'laptop lambat setelah update',
    'tidak bisa masuk zoom rapat',
];

export const options = {
    scenarios: {
        normal: { executor: 'constant-vus', vus: Number(__ENV.VUS || 10), duration: __ENV.DURATION || '5m' },
    },
    thresholds: {
        'http_req_failed': ['rate<0.01'],
        'http_req_duration{endpoint:chat}': ['p(95)<1500'],
        'http_req_duration{endpoint:triage}': ['p(95)<200'],
    },
};

const pick = () => QUESTIONS[Math.floor(Math.random() * QUESTIONS.length)];
const json = { headers: { 'Content-Type': 'application/json' } };

export default function () {
    const chat = http.post(`${BASE}/chat`, JSON.stringify({ pertanyaan: pick(), riwayat: [] }), { ...json, tags: { endpoint: 'chat' } });
    check(chat, { 'chat 200': (r) => r.status === 200 });
    sleep(3 + Math.random() * 5);

    const text = pick();
    const triage = http.post(`${BASE}/triage`, JSON.stringify({ judul: text, deskripsi: `${text}, mohon dibantu`, jenis: 'INC' }),
        { ...json, tags: { endpoint: 'triage' } });
    check(triage, { 'triage 200': (r) => r.status === 200 });
    sleep(3 + Math.random() * 5);
}

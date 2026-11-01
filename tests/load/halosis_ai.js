// Uji beban layanan AI HaloSIS (NFR-01/NFR-12): /chat & /triage langsung ke halosis-ai, kalimat buatan (tanpa data asli).
// Jalankan di jaringan docker-compose (lihat reports/rencana_uji.md §7):
//   docker run --rm -i --network glpi-halosis_default -v "$PWD/tests/load:/scripts" grafana/k6 run /scripts/halosis_ai.js
//   (tambahkan -e SCENARIO=peak atau -e SCENARIO=stress)
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

// SCENARIO=normal (10 VU, 5 menit) | peak (50 VU, 5 menit) | stress (25 → 200 VU, +25 tiap 2 menit; berhenti bila galat ≥ 5%)
const SCENARIOS = {
    normal: { executor: 'constant-vus', vus: Number(__ENV.VUS || 10), duration: __ENV.DURATION || '5m' },
    peak: { executor: 'constant-vus', vus: 50, duration: '5m' },
    stress: {
        executor: 'ramping-vus', startVUs: 25,
        stages: [25, 50, 75, 100, 125, 150, 175, 200].map((target) => ({ duration: '2m', target })),
    },
};
const SCENARIO = __ENV.SCENARIO || 'normal';
const LIMITS = { normal: [1500, 200], peak: [3000, 500], stress: [60000, 60000] }[SCENARIO];

export const options = {
    scenarios: { [SCENARIO]: SCENARIOS[SCENARIO] },
    thresholds: {
        'http_req_failed': SCENARIO === 'stress'
            ? [{ threshold: 'rate<0.05', abortOnFail: true, delayAbortEval: '30s' }]
            : [SCENARIO === 'peak' ? 'rate<0.02' : 'rate<0.01'],
        'http_req_duration{endpoint:chat}': [`p(95)<${LIMITS[0]}`],
        'http_req_duration{endpoint:triage}': [`p(95)<${LIMITS[1]}`],
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

// Uji beban halaman GLPI kondisi Normal (NFR-01): form login HaloSIS (SSO Keycloak) → daftar tiket → logout.
//   docker run --rm -i -v "$PWD/tests/load:/scripts" -e GLPI_URL=http://host.docker.internal:8080 \
//     -e USERS=rina,andi,yoga,fajar,dedi,hendra,agus,rudi,wati,lina -e PASSWORD=*** grafana/k6 run /scripts/glpi_pages.js
// Satu akun per VU: login berulang dengan akun yang sama secara bersamaan dikunci sementara oleh perlindungan
// brute-force Keycloak (user_temporarily_disabled), perilaku keamanan yang memang diinginkan.
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.GLPI_URL || 'http://host.docker.internal:8080';
const SAME_ORIGIN = { Origin: BASE, 'Sec-Fetch-Site': 'same-origin' };
const USERS = (__ENV.USERS || 'rina').split(',');

export const options = {
    scenarios: { normal: { executor: 'constant-vus', vus: Number(__ENV.VUS || 10), duration: __ENV.DURATION || '5m' } },
    thresholds: {
        'http_req_failed': ['rate<0.01'],
        'http_req_duration{page:daftar}': ['p(95)<2000'],
        'http_req_duration{page:login}': ['p(95)<3000'],
    },
};

export default function () {
    http.get(`${BASE}/index.php`, { tags: { page: 'form' } });
    const login = http.post(`${BASE}/front/login.php`,
        { login_name: USERS[(__VU - 1) % USERS.length], login_password: __ENV.PASSWORD, noAUTO: '0' },
        { headers: SAME_ORIGIN, tags: { page: 'login' } });
    check(login, { 'login masuk': (r) => r.status === 200 && !r.url.includes('index.php') });
    sleep(2 + Math.random() * 3);
    const list = http.get(`${BASE}/front/ticket.php`, { tags: { page: 'daftar' } });
    check(list, { 'daftar tiket 200': (r) => r.status === 200 && r.body.includes('<title>') });
    sleep(2 + Math.random() * 3);
    http.get(`${BASE}/front/logout.php?noAUTO=1`, { tags: { page: 'logout' } });
    sleep(1);
}

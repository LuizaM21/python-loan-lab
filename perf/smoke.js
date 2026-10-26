// Smoke test: one virtual user, a few requests. Proves the API answers at all.
// Run: k6 run perf/smoke.js
// Other host: k6 run -e API_URL=http://localhost:5081 perf/smoke.js

import http from 'k6/http'
import { check, sleep } from 'k6'

const API_URL = __ENV.API_URL || 'http://localhost:5080'

export const options = {
  vus: 1,
  iterations: 10,
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
}

export default function () {
  const list = http.get(`${API_URL}/api/loans`)
  check(list, {
    'list is 200': (r) => r.status === 200,
    'list has items': (r) => Array.isArray(r.json('items')),
  })

  const quote = http.post(
    `${API_URL}/api/loans/quote`,
    JSON.stringify({ productCode: 'PERS', amount: 10000, months: 12 }),
    { headers: { 'Content-Type': 'application/json' } },
  )
  check(quote, {
    'quote is 200': (r) => r.status === 200,
    'quote payment is 878.69': (r) => r.json('monthlyPayment') === '878.69',
  })

  sleep(0.2)
}

// Lesson 07: load on the portfolio statistics endpoint.
// Start the API with volume first:
//   DEMO_LOANS=3000 flask --app loanlab.api run --port 5080
// Then: k6 run perf/stats-load.js
//
// The threshold is the target AFTER your fix. Before the fix it fails: that's the point.

import http from 'k6/http'
import { check } from 'k6'

const API_URL = __ENV.API_URL || 'http://localhost:5080'

export const options = {
  scenarios: {
    dashboard_users: {
      executor: 'constant-vus',
      vus: 5,
      duration: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{endpoint:stats}': ['p(95)<200', 'p(99)<400'],
  },
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
}

export default function () {
  const response = http.get(`${API_URL}/api/stats/portfolio`, { tags: { endpoint: 'stats' } })
  check(response, {
    'status is 200': (r) => r.status === 200,
    'has active loans': (r) => r.json('activeLoans') > 0,
  })
}

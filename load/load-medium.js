import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '5m', target: 50 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<10000'],
    http_req_failed: ['rate<0.1'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:18888';

export default function () {
  const res = http.get(`${BASE_URL}/api/v1/orderservice/order`);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has response body': (r) => r.body.length > 0,
  });

  sleep(0.1);
}
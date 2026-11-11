from extensions import client_ip, limiter


def test_uses_cloudflare_client_ip(app_ctx):
    # Cloudflare -> 시놀로지 역방향 프록시 -> Flask: remote_addr는 항상 프록시 주소다
    with app_ctx.test_request_context(
        '/api/surveys',
        headers={'CF-Connecting-IP': ' 203.0.113.7 ', 'X-Forwarded-For': '203.0.113.7, 172.68.1.1'},
        environ_base={'REMOTE_ADDR': '172.17.0.1'},
    ):
        assert client_ip() == '203.0.113.7'


def test_two_visitors_get_separate_buckets(app_ctx):
    keys = []
    for ip in ('203.0.113.7', '198.51.100.9'):
        with app_ctx.test_request_context(
            '/', headers={'CF-Connecting-IP': ip}, environ_base={'REMOTE_ADDR': '172.17.0.1'}
        ):
            keys.append(client_ip())
    assert keys[0] != keys[1]


def test_falls_back_to_remote_address_without_header(app_ctx):
    # 로컬 개발이나 Cloudflare를 거치지 않은 요청
    with app_ctx.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
        assert client_ip() == '127.0.0.1'
    with app_ctx.test_request_context(
        '/', headers={'CF-Connecting-IP': '   '}, environ_base={'REMOTE_ADDR': '127.0.0.1'}
    ):
        assert client_ip() == '127.0.0.1'


def test_limiter_is_keyed_by_client_ip():
    assert limiter._key_func is client_ip

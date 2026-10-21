import pandas as pd

from tests.helpers import login

LOG = 'data/borrow_log.xlsx'
BORROW = {'name': '홍길동', 'student_id': '20260001', 'department': '컴퓨터정보공학부',
          'phone': '010-0000-0000', 'selected_items': ['우산']}


def _rows():
    return len(pd.read_excel(LOG, dtype=str))


def _write_log_row():
    cols = ['이름', '전화번호', '학번', '학과', '대여물품', '대여담당자',
            '대여시각', '대여현황', '반납담당자', '반납시각']
    row = {c: '' for c in cols}
    row.update({'이름': '홍길동', '학번': '20260001', '대여물품': '우산',
                '대여시각': '2026-10-01 10:00:00', '대여현황': '미반납'})
    pd.DataFrame([row], columns=cols).to_excel(LOG, index=False)


def test_borrow_blocked_when_disabled(client, data_files):
    login(client, 'master')
    res = client.put('/api/admin/site-info', json={'rental.enabled': False})
    assert res.status_code == 200
    client.post('/api/admin/logout')
    res = client.post('/api/borrow', json=BORROW)
    assert res.status_code == 403
    assert res.get_json() == {'status': 'fail', 'message': '현재 대여 신청을 받지 않습니다.'}
    assert _rows() == 0


def test_borrow_allowed_when_enabled(client, data_files):
    res = client.post('/api/borrow', json=BORROW)
    assert res.status_code == 200
    assert res.get_json()['status'] == 'success'
    assert _rows() == 1


def test_check_due_date_uses_setting(client, data_files):
    _write_log_row()
    payload = {'name': '홍길동', 'student_id': '20260001'}
    assert client.post('/api/check', json=payload).get_json()['data'][0]['due_date'] == '2026-10-05'
    login(client, 'master')
    assert client.put('/api/admin/site-info', json={'rental.return_days': 7}).status_code == 200
    assert client.post('/api/check', json=payload).get_json()['data'][0]['due_date'] == '2026-10-08'

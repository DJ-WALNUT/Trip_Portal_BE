import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix='trip_test_')
os.environ['TRIP_DATABASE_URI'] = 'sqlite:///' + os.path.join(_TMP, 'test.db').replace(chr(92), '/')
os.environ['ADMIN_PASSWORD'] = 'testmaster'
os.environ['SUB_PASSWORD'] = 'testsub'
os.environ['FLASK_SECRET_KEY'] = 'test'
os.environ['RATELIMIT_ENABLED'] = 'False'

_ORIG_CWD = os.getcwd()


@pytest.fixture
def app_ctx(tmp_path):
    """임시 디렉터리로 chdir하고 빈 임시 DB를 만든 앱 컨텍스트."""
    os.chdir(str(tmp_path))
    os.makedirs('data', exist_ok=True)
    import app as app_module
    from models import db
    app_module.app.config['TESTING'] = True
    with app_module.app.app_context():
        db.drop_all()
        db.create_all()
        yield app_module.app
        db.session.remove()
    os.chdir(_ORIG_CWD)


@pytest.fixture
def client(app_ctx):
    return app_ctx.test_client()


def login(client, role='master'):
    password = 'testmaster' if role == 'master' else 'testsub'
    res = client.post('/api/admin/login', json={'password': password})
    assert res.status_code == 200
    return res


@pytest.fixture
def data_files(app_ctx):
    """임시 data/에 재고(우산 5개)와 빈 대여 기록 엑셀을 만든다."""
    import pandas as pd
    pd.DataFrame([{'물품': '우산', '재고현황': 5, '카테고리': '생활'}]).to_excel(
        os.path.join('data', 'stuff_ongoing.xlsx'), index=False)
    cols = ['이름', '전화번호', '학번', '학과', '대여물품', '대여담당자',
            '대여시각', '대여현황', '반납담당자', '반납시각']
    pd.DataFrame(columns=cols).to_excel(os.path.join('data', 'borrow_log.xlsx'), index=False)

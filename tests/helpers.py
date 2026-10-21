def login(client, role='master'):
    password = 'testmaster' if role == 'master' else 'testsub'
    res = client.post('/api/admin/login', json={'password': password})
    assert res.status_code == 200
    return res

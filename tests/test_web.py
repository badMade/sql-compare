# -*- coding: utf-8 -*-
import pytest
from sql_compare.web import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"SQL Compare" in rv.data
    assert b"SQL Statement 1" in rv.data

def test_compare_post(client):
    rv = client.post('/', data={
        'sql1': 'SELECT a FROM t',
        'sql2': 'SELECT a FROM t',
        'mode': 'both'
    })
    assert rv.status_code == 200
    # Check if report content is embedded
    assert b"SQL Compare Report" in rv.data
    # Exact token match should be YES
    assert b"Exact tokens equal: <b>YES</b>" in rv.data

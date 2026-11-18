from fastapi.testclient import TestClient
from app import main,store
from app.engine import evaluate
import pytest

def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DB_PATH',str(tmp_path/'test.sqlite'));return TestClient(main.app)
def test_api_idempotent(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);a=c.post('/api/runs',json={}).json();b=c.post('/api/runs',json={}).json();assert a['manifest']['run_id']==b['manifest']['run_id'];assert len(c.get('/api/runs').json())==1
def test_stale_review(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);a=c.post('/api/runs',json={}).json();url='/api/runs/'+a['manifest']['run_id']+'/review';assert c.post(url,json={'revision':1}).status_code==200;assert c.post(url,json={'revision':1}).status_code==409
def test_seven_entries(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch)
    for k in main.MODULES:
        assert c.post('/api/'+k,json={}).status_code==200
        assert c.get('/'+k).status_code==200
def test_bad_dataset(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);assert c.post('/api/runs',json={'dataset':'../bad'}).status_code==422
def test_missing_run(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);assert c.get('/api/runs/none').status_code==404
def test_restart_store(tmp_path,sample):
    p=str(tmp_path/'durable.sqlite');store.save(p,sample);assert store.get(p,sample['manifest']['run_id'])['manifest']['sha256']==sample['manifest']['sha256']
def test_bad_revision(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);s=c.post('/api/runs',json={}).json();assert c.post('/api/runs/'+s['manifest']['run_id']+'/review',json={'revision':0}).status_code==422

def test_clean_navigation_run_preserved(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch)
    run=c.post('/api/runs',json={'dataset':'clean'}).json()
    rid=run['manifest']['run_id']
    for k in main.MODULES:
        html=c.get('/'+k+'?run_id='+rid).text
        assert '?run_id='+rid in html
        assert rid in html
    assert c.get('/api/export/'+rid).status_code==200

def test_custom_csv_snapshot_and_navigation(tmp_path,monkeypatch):
    from app.config import ROOT
    c=client(tmp_path,monkeypatch)
    original=(ROOT/'sample_data/clean.csv').read_text()
    # 改成独立于所有仓内样例的证据编号，追踪其跨页与重跑行为。
    first=original.splitlines()[1].split(',')[0]
    custom=original.replace(first,first+'-CUSTOM')
    result=c.post('/api/runs',json={'csv_text':custom}).json()
    rid=result['manifest']['run_id']
    assert '-CUSTOM' in str(result['records']) or '-CUSTOM' in str(result['quarantine'])
    for key in main.MODULES:
        response=c.get('/'+key+'?run_id='+rid)
        assert response.status_code==200
        assert '?run_id='+rid in response.text
    repeated=c.post('/api/runs/'+rid+'/rerun',json={})
    assert repeated.status_code==200
    assert repeated.json()['manifest']['run_id']==rid
    assert repeated.json()['manifest']['sha256']==result['manifest']['sha256']

def test_conflict_scenario_pages_and_rerun(tmp_path,monkeypatch,conflict_csv):
    import io,json,zipfile
    c=client(tmp_path,monkeypatch)
    run=c.post('/api/runs',json={'csv_text':conflict_csv}).json()
    rid=run['manifest']['run_id']
    final=next(r for r in run['selected_results'] if r['primary_id']=='00001-V1')
    assert final['id']=='00001-R8' and final['value_mg_dl']=='125'
    assert run['balance']['status']=='可锁库' and run['archive']['status']=='可冻结'
    html=c.get('/retest?run_id='+rid).text
    assert '未采用候选' in html and '00001-R9' in html and 'RETEST_SUPERSEDED' in html
    assert '锁库依据' in c.get('/locking?run_id='+rid).text
    archive_html=c.get('/archive?run_id='+rid).text
    assert '冻结凭证' in archive_html and run['archive']['seal'] in archive_html
    again=c.post('/api/runs/'+rid+'/rerun',json={}).json()
    assert again['manifest']['run_id']==rid and again['archive']['seal']==run['archive']['seal']
    assert next(r for r in again['selected_results'] if r['primary_id']=='00001-V1')['id']=='00001-R8'
    z=zipfile.ZipFile(io.BytesIO(c.get('/api/export/'+rid).content))
    evidence=json.loads(z.read('evidence.json'))
    assert any(r['id']=='00001-R9' for r in evidence['superseded'])
    assert json.loads(z.read('manifest.json'))['seal']==run['archive']['seal']

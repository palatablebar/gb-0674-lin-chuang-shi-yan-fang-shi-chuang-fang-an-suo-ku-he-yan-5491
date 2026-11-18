from app.modules.archive.rules import freeze
from app.archive import serialize
from copy import deepcopy
import zipfile,io,json

def test_clean_frozen(clean):
    assert clean['archive']['status']=='可冻结'
def test_dirty_not_frozen(sample):
    assert sample['archive']['status']=='待处理'
def test_subject_count(clean):
    assert clean['archive']['subjects']==20;assert clean['archive']['results']==40
def test_locked_state_propagates(clean):
    s=deepcopy(clean);s['balance']['status']='待处理';assert freeze(s)['status']=='待处理'
def test_seal_covers_results(clean):
    s=deepcopy(clean);s['selected_results'][0]['value_mg_dl']='999';assert freeze(s)['seal']!=clean['archive']['seal']
def test_seal_covers_superseded(conflict):
    s=deepcopy(conflict);s['retest_superseded'][0]['value_mg_dl']='999';assert freeze(s)['seal']!=conflict['archive']['seal']
def test_certificate_lists_superseded(conflict):
    certificate={row['item']:row['value'] for row in conflict['views']['archive']['certificate']}
    assert certificate['未采用候选']==1 and certificate['采信结果']==40 and certificate['冻结状态']=='可冻结'
    assert certificate['凭证指纹']==conflict['archive']['seal']
def test_bundle_preserves_superseded(conflict):
    z=zipfile.ZipFile(io.BytesIO(serialize(conflict)));evidence=json.loads(z.read('evidence.json'))
    assert any(r['id']=='00001-R9' and r['code']=='RETEST_SUPERSEDED' for r in evidence['superseded'])
    assert any(row['item']=='未采用候选' for row in evidence['lock_basis'])
    assert json.loads(z.read('manifest.json'))['seal']==conflict['archive']['seal']
def test_bundle_has_evidence(sample):
    z=zipfile.ZipFile(io.BytesIO(serialize(sample)));d=json.loads(z.read('evidence.json'));assert len(d['quarantine'])==3
def test_manifest_digest(clean):
    z=zipfile.ZipFile(io.BytesIO(serialize(clean)));assert json.loads(z.read('manifest.json'))['sha256']==clean['manifest']['sha256']

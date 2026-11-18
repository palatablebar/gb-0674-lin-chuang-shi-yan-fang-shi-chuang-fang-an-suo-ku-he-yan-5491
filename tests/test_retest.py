from app.modules.retest.rules import adjudicate
from app.engine import evaluate
from copy import deepcopy

def test_retest_selected_real(clean):
    row=next(r for r in clean['selected_results'] if r['primary_id']=='00001-V1');assert row['id']=='00001-R1';assert row['value_mg_dl']=='118'
def test_orphan_retest_real(sample):
    assert next(r for r in sample['retest_issues'] if r['id']=='ORPHAN')['code']=='RETEST_REFERENCE'
def test_retest_before_primary_real(sample):
    assert next(r for r in sample['retest_issues'] if r['id']=='00001-R1')['code']=='RETEST_WINDOW'
def test_retest_cannot_repair_deviation(sample):
    assert any(r['code']=='WINDOW_LATE' for r in sample['deviations']);assert sample['balance']['status']=='待处理'
def test_same_version_conflict(clean):
    rows=[dict(r) for r in clean['records']];rows.append(dict(next(r for r in rows if r['id']=='00001-R1'),id='R-DUP'));selected,issues,superseded=adjudicate(rows,clean['context']);assert issues[0]['code']=='RETEST_VERSION_CONFLICT'
def test_other_subject_reference(clean):
    rows=[dict(r) for r in clean['records']];row=next(r for r in rows if r['id']=='00001-R1');row['parent']='00002-V1';_,issues,_=adjudicate(rows,clean['context']);assert issues[0]['code']=='RETEST_REFERENCE'
def test_retest_max_72_hours_inclusive(clean):
    rows=[dict(r) for r in clean['records']];row=next(r for r in rows if r['id']=='00001-R1');row['at']='2026-10-11T00:00:00+00:00';selected,issues,_=adjudicate(rows,clean['context']);assert not issues;assert next(r for r in selected if r['primary_id']=='00001-V1')['id']=='00001-R1'

def test_later_observation_loses_to_higher_revision(conflict):
    final=next(r for r in conflict['selected_results'] if r['primary_id']=='00001-V1')
    assert final['id']=='00001-R8' and final['value_mg_dl']=='125' and final['revision']==3 and final['code']=='RETEST_SELECTED'
    assert conflict['retest_issues']==[]
def test_superseded_candidate_recorded_not_lost(conflict):
    held=next(r for r in conflict['retest_superseded'] if r['id']=='00001-R9')
    assert held['code']=='RETEST_SUPERSEDED' and held['value_mg_dl']=='130' and held['revision']==2 and held['primary_id']=='00001-V1'
    assert any(r['id']=='00001-R9' for r in conflict['records'])
def test_superseded_does_not_block(conflict):
    assert conflict['balance']['blocked']==0 and conflict['balance']['status']=='可锁库'
def test_lock_and_freeze_share_same_choice(conflict):
    final=next(r for r in conflict['selected_results'] if r['primary_id']=='00001-V1')
    frozen=next(r for r in conflict['views']['archive']['rows'] if r['primary_id']=='00001-V1')
    assert frozen['id']==final['id']=='00001-R8' and frozen['value_mg_dl']==final['value_mg_dl']=='125'
    assert conflict['archive']['status']=='可冻结'
def test_rerun_same_batch_keeps_frozen_value(conflict_csv):
    a=evaluate({'csv_text':conflict_csv});b=evaluate({'csv_text':conflict_csv})
    assert a['manifest']['run_id']==b['manifest']['run_id']
    assert a['selected_results']==b['selected_results'] and a['archive']['seal']==b['archive']['seal']
def test_adjudication_independent_of_row_order(conflict_csv):
    lines=conflict_csv.splitlines();shuffled='\n'.join([lines[0]]+list(reversed(lines[1:])))+'\n'
    a=evaluate({'csv_text':conflict_csv});b=evaluate({'csv_text':shuffled})
    pick=lambda s:next(r for r in s['selected_results'] if r['primary_id']=='00001-V1')
    assert pick(a)==pick(b) and a['retest_superseded']==b['retest_superseded']
def test_version_tie_still_blocks_and_holds_candidates(clean):
    rows=[dict(r) for r in clean['records']]
    rows.append(dict(next(r for r in rows if r['id']=='00001-R1'),id='00001-R7',value_mg_dl='131'))
    selected,issues,superseded=adjudicate(rows,clean['context'])
    conflict_issue=next(i for i in issues if i['code']=='RETEST_VERSION_CONFLICT')
    assert conflict_issue['id']=='00001-V1' and set(conflict_issue['candidates'].split(','))=={'00001-R1','00001-R7'}
    final=next(r for r in selected if r['primary_id']=='00001-V1');assert final['id']=='00001-V1' and final['code']=='PRIMARY_SELECTED'
    held={r['id'] for r in superseded if r['code']=='RETEST_CONFLICT_HELD'};assert held=={'00001-R1','00001-R7'}
def test_version_tie_blocks_locking(conflict_csv):
    lines=conflict_csv.splitlines()
    lines.append('00001-R7,00001,V1,2026-10-09T18:00:00+08:00,2026-10-01T00:00:00+08:00,RETEST,00001-V1,131,mg/dL,auto,3')
    state=evaluate({'csv_text':'\n'.join(lines)+'\n'})
    assert any(i['code']=='RETEST_VERSION_CONFLICT' for i in state['retest_issues'])
    assert state['balance']['status']=='待处理' and state['archive']['status']=='待处理'

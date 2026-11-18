from app.config import RULE_VERSION

def decide(state):
    c=state['counts'];explained=len(state['records'])+len(state['quarantine'])+c['blank']+c['duplicate']+c['repeated_header'];blocked=len(state['deviations'])+len(state['retest_issues'])+len(state['quarantine'])
    return {'input':c['input'],'accepted':len(state['records']),'quarantined':len(state['quarantine']),'row_balanced':c['input']==explained,'completed':len(state['completed']),'expected':len(state['context']['subjects'])*len(state['context']['required_visits']),'deviations':len(state['deviations']),'retest_issues':len(state['retest_issues']),'blocked':blocked,'status':'可锁库' if not blocked and c['input']==explained else '待处理'}
def apply(state):
    state['balance']=decide(state);b=state['balance']
    state['lock_basis']=[{'item':'规则版本','value':RULE_VERSION},{'item':'行守恒','value':'通过' if b['row_balanced'] else '失衡'},{'item':'完成访视','value':f"{b['completed']}/{b['expected']}"},{'item':'正式采信值','value':len(state['selected_results'])},{'item':'采用复检','value':sum(r['code']=='RETEST_SELECTED' for r in state['selected_results'])},{'item':'未采用候选','value':len(state['retest_superseded'])},{'item':'阻断项','value':b['blocked']},{'item':'锁库状态','value':b['status']}]
    state['views']['locking']={'title':'锁库闸门','rows':[b],'basis':state['lock_basis'],'metrics':{'应访视':b['expected'],'已完成':b['completed'],'阻断项':b['blocked']}}

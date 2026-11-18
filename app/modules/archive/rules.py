import hashlib,json

def freeze(state):
    basis={'selected':state['selected_results'],'superseded':state['retest_superseded'],'windows':state['windows'],'deviations':state['deviations']}
    return {'status':'可冻结' if state['balance']['status']=='可锁库' else '待处理','seal':hashlib.sha256(json.dumps(basis,sort_keys=True).encode()).hexdigest(),'subjects':len(state['context']['subjects']),'results':len(state['selected_results'])}
def apply(state):
    state['archive']=freeze(state);a=state['archive']
    certificate=[{'item':'冻结状态','value':a['status']},{'item':'凭证指纹','value':a['seal']},{'item':'采信结果','value':a['results']},{'item':'未采用候选','value':len(state['retest_superseded'])}]
    state['views']['archive']={'title':'冻结清单','rows':state['selected_results'],'certificate':certificate,'metrics':{'受试者':a['subjects'],'结果':a['results'],'状态':a['status']}}

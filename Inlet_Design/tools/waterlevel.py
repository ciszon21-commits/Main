import math
from scipy.optimize import brentq
def all_result(choose_tunnel_type,lweir,Q,No,Sta,Ogee_crest_elv,Ogee_height,Z,S):
    
    if No<5:
        b=lweir*3
    elif No==6:
        b=lweir*2
    else:
        b=(2-(No-5)/5)*(lweir)
    

    return{
        'No':No,
        'sta':Sta,
        'type':'river',
        'Q':Q,
        'b':b,
        'L':5,
        'n':0.025,
        'Z': Z,
        'S':0.01,
        'yc':0.705,
        'A':2395.8,
        'T':372,
        'P':384.88,
        'R':6.225,
        'v':0.288,
        'Sf':0.0000045,
        'speeding_head':0.004,
        'hf':0.00002,
        'hce':0.00002,
        'he':0.000042,
        'E':27.84,
        'Control':0,
        'Water_depth':6.44,
        'Fr':0.036,
        'Water_level':27.84,
        'Tunnel_height':None,
        'full':None
    }
def waterlevel_data(choose_tunnel_type,lweir,Q,Ogee_crest_elv,Ogee_height):
    No=9
    No_=No
    S=0.01
    result=[]
    for i in range(9): 
        Sta=(i+1)*-5
        if No==9:
            Z=round(Ogee_crest_elv-Ogee_height,2)
        else:
            Z=round(Z+5*S,2)
        data=all_result(choose_tunnel_type,lweir,Q,No,Sta,Ogee_crest_elv,Ogee_height,Z,S)
        result.append(data)
        No=No-1

    data_ogee={
        'No':No_+1,
        'sta':0,
        'type':'Yc, ogee',
        'Q':Q,
        'b':lweir,
        'L':None,
        'n':None,
        'Z':Ogee_crest_elv,
        'S':None,
        'yc':0.705,
        'A':2395.8,
        'T':372,
        'P':384.88,
        'R':6.225,
        'v':0.288,
        'Sf':0.0000045,
        'speeding_head':0.004,
        'hf':0.00002,
        'hce':0.00002,
        'he':0.000042,
        'E':27.84,
        'Control':0,
        'Water_depth':6.44,
        'Fr':0.036,
        'Water_level':27.84,
        'Tunnel_height':None,
        'full':None
    }
    
    result.append(data_ogee)
    sorted_data = sorted(result, key=lambda x: x['sta'])
    return sorted_data
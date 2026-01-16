import math
from scipy.optimize import brentq
from .round_tool import count_A,count_P,count_T,findy_,next_result,control_is_zero,findy__,next_result_,critical_cal,control_is_zero_
def round_data(param):
    (R,Q_tunnel,n,Z,S,yc_value,Critical_depth)=param
    No=0
    Sta=0
    Q_output=Q_tunnel
    b_output=R*2
    L=''
    y=yc_value*Critical_depth/100
    A=count_A(y,R)
    if isinstance(A, str):
        return {"error A":A}
    T=count_T(y,R)
    if isinstance(T,str):
        return{"error T":T}
    
    P=count_P(y,R)
    if isinstance(P,str):
        return{"error P":P}	
    R_h=A/P	
    v=Q_output/A
    Sf=(v**2)*(n**2)/(R**(4/3))
    speed_head=(v**2)/(2*9.81)	
    hf=''
    hce=''
    he=0
    E=Z+speed_head+y
    control=''
    Fr=v/math.sqrt(9.81*A/T)	
    Water_level=y+Z
    Full=y/b_output*100
    output={
        'No':No,
        'sta_output':Sta,
        'Q_output':Q_output,
        'b_output':b_output,
        'L_output':L,
        'n_output':n,
        'Z_output':Z,
        'S_output':S,
        'yc_output':yc_value,
        'A_output':A,
        'T_output':T,
        'P_output':P,
        'R_output':R_h,
        'V_output':v,
        'Sf_output':Sf,
        'speed_head_output':speed_head,
        'hf_output':hf,
        'hce_output':hce,
        'he_output':he,
        'E_output':E,
        'Control_output':control,
        'y_output':y,
        'Fr_output':Fr,
        'Water_level_output':Water_level,
        'Full_output':Full
        }
    return output


def supercritical_round_data(para):
    (R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,data0)=para
    times=Tunnel_length//Interval
    b_output=round(R,1)
    result=[]
    for i in range(int(times)):
        No=i+1
        sta=(i+1)*Interval
        Z=Z-Interval*S/100
        Sf0=data0['Sf_output']
        speed_head0=data0['speed_head_output']
        E0=data0['E_output']
        para_for_supercritical=(R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)
        
        ymax,ymin=findy_(int(yc_value),0,para_for_supercritical)
        
        try:
            para_for_supercritical=(R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)
            y_star =  brentq(control_is_zero,ymax,ymin, args=(para_for_supercritical,) ,xtol=1e-5)
            if y_star<0:
                y_star = None
                return result,False
            para_for_supercritical_=(No,sta,y_star,R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)
            data1=next_result(para_for_supercritical_)
            result.append(data1)
            data0=data1
        except ValueError as e:
            y_star = None
            return result,False
    if Tunnel_length%Interval >0:
        No=int(times)+1
        Interval=Tunnel_length%Interval
        Z=round(Z-Interval*S/100,3)
        sta=Tunnel_length
        Sf0=data0['Sf_output']
        speed_head0=data0['speed_head_output']
        E0=data0['E_output']
        
        para_for_supercritical=(R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)
        ymax,ymin=findy_(int(yc_value),0,para_for_supercritical)
        
        try:
            y_star =  brentq(control_is_zero,ymax,ymin, args=(para_for_supercritical,) ,xtol=1e-4)
            para_for_supercritical_=(No,sta,y_star,R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)
            data1=next_result(para_for_supercritical_)
            result.append(data1)
        except ValueError :
            y_star = None
            return result,False
        return result,True

def subcritical_round_data(para):
    (R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion,data0)=para
    times=Tunnel_length//Interval
    b_output=round(R*2,1)
    result=[data0]
    Sf0=data0['Sf_output']
    speed_head0=data0['speed_head_output']
    E0=data0['E_output']
    Interval0=data0['L_output']
    Z0=data0['Z_output']
    if Tunnel_length%Interval==0:
        times=times-1
    for i in range(int(times),-1,-1):
        no=i
        sta=i*Interval
        Z=Z0+Interval0*S/100
        para_for_subcritical=(R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion,Sf0,speed_head0,E0)
        ymax,ymin=findy__(1000,int(yc_value),para_for_subcritical)
        try:
            y_star =  brentq(control_is_zero_,ymax,ymin, args=(para_for_subcritical,) ,xtol=1e-4)
        except ValueError:
            y_star = None
            return result,False
        params_r=(no,sta,y_star,R,Q_tunnel,n,Z,S,yc_value,Critical_depth,
        Tunnel_length,Interval,Exspansion,Sf0,speed_head0,E0)
        data1=next_result_(params_r)
        result.append(data1)
        data0=data1
        Sf0=data0['Sf_output']
        speed_head0=data0['speed_head_output']
        E0=data0['E_output']
        Interval0=data0['L_output']
        Z0=data0['Z_output']
    return result,True 
def critical_round_data(para):
    (R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion)=para
    y_star=critical_cal(para)
    No=math.ceil(Tunnel_length/Interval)
    sta=Tunnel_length
    y=y_star
    A = count_A(y,R)
    T = count_T(y,R)
    P = count_P(y,R)
    R_h=A/P
    v=Q_tunnel/A
    Sf=(v**2)*(n**2)/(R_h**(4/3))
    speed_head=(v**2)/(2*9.81)	
    E=Z+speed_head+y
    Fr=v/math.sqrt(9.81*A/T)	
    Water_level=y+Z
    Full=y/(R*2)*100
    if Tunnel_length%Interval>0:
        Interval=Tunnel_length%Interval
    data1={
        'No':No,
        'sta_output':sta,
        'Q_output':Q_tunnel,
        'b_output':round(R*2,1),
        'L_output':Interval,
        'n_output':n,
        'Z_output':round(Z,3),
        'S_output':S,
        'yc_output':yc_value,
        'A_output':round(A,3),
        'T_output':round(T,3),
        'P_output':round(P,3),
        'R_output':round(R_h,3),
        'V_output':round(v,3),
        'Sf_output':round(Sf,3),
        'speed_head_output':round(speed_head,3),
        'hf_output':0,
        'hce_output':0,
        'he_output':0,
        'E_output':round(E,3),
        'Control_output':0,
        'y_output':round(y,3),
        'Fr_output':round(Fr,3),
        'Water_level_output':round(Water_level,3),
        'Full_output':round(Full,2)
    }
    return data1
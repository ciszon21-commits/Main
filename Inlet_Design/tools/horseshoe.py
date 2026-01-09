import math
from scipy.optimize import brentq
from .horseshoe_tools import count_A,count_P,count_T,froude_minus_one,findy,control_is_zero,findy_,next_result,critical_cal,findy__,control_is_zero_,next_result_
def horseshoe_data(R,Q_tunnel,B1,B2,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth):
    No=0
    Sta=0
    Q_output=Q_tunnel
    b_output=R
    L=''
    y=yc_value*Critical_depth/100
    A=count_A(y,yt1max,yt2max,R,y2max,ninety_minus_beta2,t1max,a1max,a2max)
    if isinstance(A, str):
        return {"error A":A}
    T=count_T(y,yt1max,yt2max,R,y2max,)
    if isinstance(T,str):
        return{"error T":T}
    
    P=count_P(y,yt1max,yt2max,R,y2max,b_output,ninety_minus_beta2,p1max,p2max)
    if isinstance(P,str):
        return{"error P":P}	
    R=A/P	
    v=Q_output/A
    Sf=(v**2)*(n**2)/(R**(4/3))
    speed_head=(v**2)/(2*9.81)	
    hf=''
    hce=''
    he=0
    E=Z+speed_head+y
    Control=''
    Fr=v/math.sqrt(9.81*A/T)	
    Water_level=y+Z
    Full=y/b_output*100
    output={
        'No':No,
        'sta_output':Sta,
        'Q_output':Q_output,
        'b_output':round(b_output,1),
        'L_output':L,
        'n_output':n,
        'Z_output':Z,
        'S_output':S,
        'yc_output':yc_value,
        'A_output':A,
        'T_output':T,
        'P_output':P,
        'R_output':R,
        'V_output':v,
        'Sf_output':Sf,
        'speed_head_output':speed_head,
        'hf_output':hf,
        'hce_output':hce,
        'he_output':he,
        'E_output':E,
        'Control_output':Control,
        'y_output':y,
        'Fr_output':Fr,
        'Water_level_output':Water_level,
        'Full_output':Full
        }
    return output



def supercritical_data(para):
    (R,Q_tunnel,B1,B2,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,data0)=para
    times=Tunnel_length//Interval
    b_output=round(R,1)
    result=[]
    for i in range(int(times)):
        no=i+1
        sta=(i+1)*Interval
        Z=round(Z-Interval*S/100,3)
        Sf0=data0['Sf_output']
        speed_head0=data0['speed_head_output']
        E0=data0['E_output']
        para_for_supercritical=(R,Q_tunnel,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)
        ymax,ymin=findy_(int(yc_value),0,para_for_supercritical)
        try:
            y_star =  brentq(control_is_zero,ymax,ymin, args=(para_for_supercritical,) ,xtol=1e-4)
            params_r = (no,sta,y_star,yt1max, yt2max, R, y2max, b_output,
            ninety_minus_beta2, p1max, p2max,Q_tunnel, n, Z, S,yc_value,t1max, a1max, 
            a2max,Interval,Contraction,Sf0,speed_head0,E0)
            data1=next_result(params_r)
            result.append(data1)
            data0=data1
        except ValueError:
            y_star = None
            return result,False
    if Tunnel_length%Interval >0:
        no=int(times)+1
        Z=round(Z-(Tunnel_length-(times)*Interval)*S/100,3)
        sta=Tunnel_length
        Sf0=data0['Sf_output']
        speed_head0=data0['speed_head_output']
        E0=data0['E_output']
        Interval=Tunnel_length%Interval
        para_for_supercritical=(R,Q_tunnel,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)
        ymax,ymin=findy_(int(yc_value),0,para_for_supercritical)
        try:
            y_star =  brentq(control_is_zero,ymax,ymin, args=(para_for_supercritical,) ,xtol=1e-4)
            params_r = (no,sta,y_star,yt1max, yt2max, R, y2max, b_output,
            ninety_minus_beta2, p1max, p2max,Q_tunnel, n, Z, S,yc_value,t1max, a1max, 
            a2max,Interval,Contraction,Sf0,speed_head0,E0)
            data1=next_result(params_r)
            result.append(data1)
        except ValueError:
            y_star = None
            return result,False
    return result,True
def critical_data(para):
    (R,Q_tunnel,B1,B2,ninety_minus_beta2,
            yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,
            y2max,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction)=para
    param=(yt1max, yt2max, R, y2max, R,
         ninety_minus_beta2, p1max, p2max,
         Q_tunnel, n, Z, t1max, a1max, a2max)
    y_star=critical_cal(param)
    No=math.ceil(Tunnel_length/Interval)
    sta=Tunnel_length
    y=y_star
    A = count_A(y, yt1max, yt2max, R, y2max, ninety_minus_beta2, t1max, a1max, a2max)
    T = count_T(y, yt1max, yt2max, R, y2max)
    P = count_P(y, yt1max, yt2max, R, y2max, R, ninety_minus_beta2, p1max, p2max)
    R_h=A/P
    v=Q_tunnel/A
    Sf=(v**2)*(n**2)/(R_h**(4/3))
    speed_head=(v**2)/(2*9.81)	
    E=Z+speed_head+y
    Fr=v/math.sqrt(9.81*A/T)	
    Water_level=y+Z
    Full=y/R*100
    if Tunnel_length%Interval>0:
        Interval=Tunnel_length%Interval
    data1={
        'No':No,
        'sta_output':sta,
        'Q_output':Q_tunnel,
        'b_output':round(R,1),
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
  
def subcritical_data(para):
    (R,Q_tunnel,B1,B2,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion,data0)=para
    times=Tunnel_length//Interval
    b_output=round(R,1)
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
        para_for_subcritical=(R,Q_tunnel,ninety_minus_beta2,yt1max,
        t1max,p1max,a1max,yt2max,p2max,a2max,y2max,n,Z,S,yc_value,
        Critical_depth,Tunnel_length,Interval,Exspansion,Sf0,speed_head0,E0)
        ymax,ymin=findy__(1000,int(yc_value),para_for_subcritical)
        try:
            y_star =  brentq(control_is_zero_,ymax,ymin, args=(para_for_subcritical,) ,xtol=1e-4)
        except ValueError:
            y_star = None
            return result,False
        params_r=(no,sta,y_star,yt1max, yt2max, R, y2max, b_output,
            ninety_minus_beta2, p1max, p2max,Q_tunnel, n, Z, S,yc_value,t1max, a1max, 
            a2max,Interval,Exspansion,Sf0,speed_head0,E0)
        data1=next_result_(params_r)
        result.append(data1)
        data0=data1
        Sf0=data0['Sf_output']
        speed_head0=data0['speed_head_output']
        E0=data0['E_output']
        Interval0=data0['L_output']
        Z0=data0['Z_output']
    return result,True        


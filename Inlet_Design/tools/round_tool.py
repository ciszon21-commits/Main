import math
from scipy.optimize import brentq
#-----------------------------------計算-------------------------------------------
def count_A(y: float, R: float) -> float:
    try:
        if y <= R:
            angle_rad = math.acos((R - y) / R)
            A1 = (angle_rad * 2) / (2 * math.pi) * math.pi  
            A2 = math.sin(angle_rad) * math.cos(angle_rad)
            A = R ** 2 * (A1 - A2)
        else:
            angle_rad = math.acos((y - R) / R)
            A1 = (angle_rad * 2) / (2 * math.pi) * math.pi  
            A2 = math.sin(angle_rad) * math.cos(angle_rad)
            A = R ** 2 * (math.pi - (A1 - A2))
        return A
    except ValueError as e:
        # print(f"[錯誤] 輸入數據錯誤: {e}")
        return 0  # 或 return 0、或 raise Exception 視需求
    except Exception as e:
        # print(f"[錯誤] 未預期錯誤: {e}")
        return 0

def count_P(y: float, R: float) -> float:
    try:
        if y <= R:
            angle = 2 * math.acos((R - y) / R)  
            return angle * R
        else:
            angle = 2 * math.acos((y - R) / R)  
            return (2 * math.pi - angle) * R

    except ValueError as e:
        # print(f"[錯誤] 輸入數據錯誤: {e}")
        return 0  # 或 return 0、或 raise Exception 視需求
    except Exception as e:
        # print(f"[錯誤] 未預期錯誤: {e}")
        return 0
    

def count_T(y: float, R: float) -> float:
    try:
        angle_rad = (
            math.acos((R - y) / R) if y <= R else math.acos((y - R) / R)
        )
        return 2 * R * math.sin(angle_rad)
    except ValueError as e:
        # print(f"[錯誤] 輸入數據錯誤: {e}")
        return 0  # 或 return 0、或 raise Exception 視需求
    except Exception as e:
        # print(f"[錯誤] 未預期錯誤: {e}")
        return 0

def findy_(ymax,ymin,params):
    control_max=control_is_zero(ymax, params)
    control_min=control_is_zero(ymin, params)
    print(control_max,control_min)
    for _ in range(int(ymax*100)):
        control_max=control_is_zero(ymax, params)
        if control_max!=999999:
            break
        else:
            ymax=ymax-ymax/100
    for _ in range(ymax*100):
        control_min=control_is_zero(ymin, params)
        if control_min!=999999:
            break
        else:
            ymin=ymin+ymax/100
    
    if control_max*control_min>0:
        delta=ymax-ymin
        step=delta/1000
        ymax_,ymin_=ymax,ymin
        control_max_,control_min_=control_max,control_min
        for _ in range(500):
            control_max = control_is_zero(ymax, params)
            control_min=control_is_zero(ymin, params)
            # print(ymax,ymin,control_max,control_min)
            if control_max != 999999 and control_max * control_min < 0:
                return ymin, ymax
            ymax -= step
            ymin += step
        for _ in range(500):
            # print(ymax_,ymin_,control_max_,control_min_)
            control_max_ = control_is_zero(ymax_, params)
            control_min_=control_is_zero(ymin_, params)
            if control_max_ != 999999 and control_max_ * control_min_ < 0:
                return ymin_, ymax_
            ymax_ += 0.01
            ymin_ -= 0.01

    return ymax,ymin

def control_is_zero(y, params):
    (R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)=params
    A = count_A(y,  R)
    if isinstance(A, str):
        A=0
    T = count_T(y, R)
    if isinstance(T, str):
        T=0
    P = count_P(y,R)
    if isinstance(P, str):
        P=0
    if A*P*T==0 or A<0:
        control=999999
        return control
    else:
        R_h=A/P	
        v = Q_tunnel / A
        Sf=(v**2)*(n**2)/(R_h**(4/3))
        speed_head=(v**2)/(2*9.81)	
        E=Z+speed_head+y
        Fr = v / math.sqrt(9.81 * A / T)
        if Fr<1:
            control=999999
            return control
        else:
            hf=Interval*(Sf+Sf0)/2
            hce=Contraction*abs(speed_head0-speed_head)
            he=hf+hce
            control=E0-E-he
            return control
def next_result(params):
    (No,sta,y,R,Q_output,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)= params
    A = count_A(y, R)
    T = count_T(y, R)
    P = count_P(y, R)
    R_h=A/P	
    v=Q_output/A
    Sf=(v**2)*(n**2)/(R_h**(4/3))
    speed_head=(v**2)/(2*9.81)	
    E=Z+speed_head+y
    Fr=v/math.sqrt(9.81*A/T)	
    Water_level=y+Z
    Full=y/R/2*100
    hf=Interval*(Sf+Sf0)/2
    hce=Contraction*abs(speed_head0-speed_head)
    he=hf+hce
    control=E0-E-he
    data1={
        'No':No,
        'sta_output':sta,
        'Q_output':Q_output,
        'b_output':R*2,
        'L_output':Interval,
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
    return data1
#-----------------------------------subcritical start--------------------------------------------
def control_is_zero_(y, params):
    (R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion,Sf0,speed_head0,E0)=params
    A = count_A(y,  R)
    if isinstance(A, str):
        A=0
    T = count_T(y, R)
    if isinstance(T, str):
        T=0
    P = count_P(y,R)
    if isinstance(P, str):
        P=0
    if A*P*T==0 or A<0:
        control=999999
        return control
    else:
        R_h=A/P	
        v = Q_tunnel / A
        Sf=(v**2)*(n**2)/(R_h**(4/3))
        speed_head=(v**2)/(2*9.81)	
        E=Z+speed_head+y
        Fr = v / math.sqrt(9.81 * A / T)
        
        if Fr>1:
            control=999999
            return control
        else:
            hf=Interval*(Sf+Sf0)/2
            hce=Exspansion*abs(speed_head0-speed_head)
            he=hf+hce
            control=E0-E+he
            return control
def findy__(ymax,ymin,params):
    for _ in range(ymax):
        control_max=control_is_zero_(ymax, params)
        if control_max!=999999:
            break
        else:
            ymax=ymax-1
    for _ in range(500):
        control_min=control_is_zero_(ymin, params)

        if control_min!=999999:
            break
        else:
            ymin=ymin+0.1
    
    if control_max*control_min>0:
        delta=ymax-ymin
        step=delta/1000
        for _ in range(500):
            # print(control_max*control_min,ymax,ymin)
            control_max = control_is_zero_(ymax, params)
            control_min=control_is_zero_(ymin, params)
            if control_max != 999999 and control_max * control_min < 0:
                return ymin, ymax
            ymax -= step
            ymin += step
    return ymax,ymin
def next_result_(params):
    (No,sta,y,R,Q_output,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion,Sf0,speed_head0,E0) = params
    
    A = count_A(y,R)
    T = count_T(y,R)
    P = count_P(y,R)
    R_h=A/P	
    v=Q_output/A
    Sf=(v**2)*(n**2)/(R_h**(4/3))
    speed_head=(v**2)/(2*9.81)	
    E=Z+speed_head+y
    Fr=v/math.sqrt(9.81*A/T)	
    Water_level=y+Z
    Full=y/R/2*100
    hf=Interval*(Sf+Sf0)/2
    hce=Exspansion*abs(speed_head0-speed_head)
    he=hf+hce
    control=E0-E+he
    data1={
        'No':No,
        'sta_output':sta,
        'Q_output':Q_output,
        'b_output':R*2,
        'L_output':Interval,
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
    return data1
#-----------------------------------critical start----------------------------------------------
def froude_minus_one(y,param):
    (R,Q_output,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion)= param
    A = count_A(y, R)
    if isinstance(A, str):
        A=0
    
    T = count_T(y, R)
    if isinstance(T, str):
        T=0
    
    P = count_P(y, R)
    if isinstance(y, str):
        P=0
    if A*P*T==0:
        Fr=9999
    else:
        v = Q_output / A
        Fr = v / math.sqrt(9.81 * A / T)
    
    return Fr - 1.0
def findy(ymax,ymin,params):
    for _ in range(ymax):
        fr_max=froude_minus_one(ymax, params)
        if fr_max!=9998:
            break
        else:
            ymax=ymax-1
    for _ in range(ymin):
        fr_min=froude_minus_one(ymin, params)
        if fr_min!=9998:
            break
        else:
            ymin=ymin-1
    return ymax,ymin
def critical_cal(param):
    ymax,ymin=findy(1000,0,param)
    y_star =  brentq(froude_minus_one,ymax,ymin, args=(param,) ,xtol=1e-4)
    return y_star
# ----------------------------------critical end-------------------------------------------------
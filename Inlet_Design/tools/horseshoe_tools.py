import math
from scipy.optimize import brentq
#-----------------------------------計算-------------------------------------------
def count_A(y,yt1max,yt2max,R,y2max,ninety_minus_beta2,t1max,a1max,a2max):
    try:
        # ===== 1) y <= yt1max =====
        if y <= yt1max:
            alpha = math.acos((R - y) / R)             
            A = (R**2) * (alpha - math.sin(alpha) * math.cos(alpha))
            return A

        # ===== 2) yt1max < y <= yt2max =====
        elif y <= yt2max:
            fraction = (y2max - (y - yt1max)) / R
            gamma_deg = math.degrees(math.acos(fraction)) - ninety_minus_beta2   # γ (deg)

            # 1) sector − triangle，整個再 ×2
            sector   = gamma_deg / 360 * math.pi * R**2                 # 扇形面積
            triangle = math.sin(math.radians(gamma_deg/2)) * \
                    math.cos(math.radians(gamma_deg/2)) * R**2       # 直角三角形面積
            part12   = 2 * (sector - triangle)                          # <-- 多乘這個 2
            # 2) 梯形 + a1max
            length = y2max - (y - yt1max)          # = len
            theta  = math.acos(length / R)         # 弧度
            # 如果 radd3 本來就等於 R/2，可直接用 R/2；否則請使用 radd3
            third  = ((length * math.tan(theta) - R/2) * 2 + t1max) * (y - yt1max) / 2 + a1max
            return part12 + third

        # ===== 3) y > yt2max =====
        else:
            alpha = math.acos((y - yt2max) / (R / 2))
            part1 = (R**2) / 4 * math.cos(alpha) * math.sin(alpha)
            part2 = (90 - math.degrees(alpha)) / 360 * math.pi * R**2 / 4 * 2
            return part1 + part2 + a2max
    except ValueError as e:
        # print(f"[錯誤] 輸入數據錯誤: {e}")
        return 0  # 或 return 0、或 raise Exception 視需求

    except Exception as e:
        # print(f"[錯誤] 未預期錯誤: {e}")
        return 0
def count_T(y,yt1max,yt2max,R,y2max):
    try:
        if (y<=yt1max):
            fraction=(R-y)/R
            fraction_acos=math.acos(fraction)
            T=2*R*math.sin(fraction_acos)
        elif(y>yt1max and y<=yt2max):
            delta=(y2max-(y-yt1max))
            fraction_acos=math.acos(delta/R)
            T=(delta*math.tan(fraction_acos)-(R/2))*2
        else:
            fraction_acos=math.acos((y-yt2max)/(R/2))
            T=R*math.sin(fraction_acos)
        return T
    except ValueError as e:
        # print(f"[錯誤] 輸入數據錯誤: {e}")
        return 0  # 或 return 0、或 raise Exception 視需求

    except Exception as e:
        # print(f"[錯誤] 未預期錯誤: {e}")
        return 0
def count_P(y,yt1max,yt2max,R,y2max,b_output,ninety_minus_beta2,p1max,p2max):
    try:
        if (y<=yt1max):
            fraction=math.acos((b_output-y)/b_output)
            P=2*math.degrees(fraction)/180*math.pi*b_output
        elif(y>yt1max and y<=yt2max):
            fraction=math.acos((y2max-(y-yt1max))/b_output)
            P=(math.degrees(fraction)-ninety_minus_beta2)/180*2*math.pi*b_output+p1max
        else:
            fraction_acos=math.acos((y-yt2max)/(b_output/2))
            P=(90-math.degrees(fraction_acos))/180*math.pi*b_output+p2max
        return P
    except ValueError as e:
        # print(f"[錯誤] 輸入數據錯誤: {e}")
        return 0  # 或 return 0、或 raise Exception 視需求

    except Exception as e:
        # print(f"[錯誤] 未預期錯誤: {e}")
        return 0
#-----------------------------------critical-------------------------------------------
def froude_minus_one(y, params):
    (yt1max, yt2max, R, y2max, b_output,
     ninety_minus_beta2, p1max, p2max,
     Q_output, n, Z, t1max, a1max, a2max) = params
    
    A = count_A(y, yt1max, yt2max, R, y2max, ninety_minus_beta2, t1max, a1max, a2max)
    if isinstance(A, str):
        raise ValueError(f"A error: {A}")
    
    T = count_T(y, yt1max, yt2max, R, y2max)
    if isinstance(T, str):
        raise ValueError(f"T error: {T}")
    
    P = count_P(y, yt1max, yt2max, R, y2max, b_output, ninety_minus_beta2, p1max, p2max)
    if isinstance(P, str):
        raise ValueError(f"P error: {P}")
    if A*P*T==0:
        Fr=9999
    else:
        v = Q_output / A
        Fr = v / math.sqrt(9.81 * A / T)
    
    return Fr - 1.0
def findy(ymax,ymin,params):
    for i in range(ymax):
        fr_max=froude_minus_one(ymax, params)
        if fr_max!=9998:
            break
        else:
            ymax=ymax-1
    for i in range(ymin):
        fr_min=froude_minus_one(ymin, params)
        if fr_min!=9998:
            break
        else:
            ymin=ymin+1
    return ymax,ymin
#-----------------------------------critical end-------------------------------------------
#-----------------------------------supercritical-------------------------------------------
def findy_(ymax,ymin,params):
    for _ in range(ymax):
        control_max=control_is_zero(ymax, params)
        if control_max!=999999:
            break
        else:
            ymax=ymax-1
    for _ in range(ymax):
        control_min=control_is_zero(ymin, params)
        if control_min!=999999:
            break
        else:
            ymin=ymin+1
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
    return ymax,ymin

def control_is_zero(y, params):
    (R,Q_tunnel,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,Sf0,speed_head0,E0)=params
    A = count_A(y, yt1max, yt2max, R, y2max, ninety_minus_beta2, t1max, a1max, a2max)
    if isinstance(A, str):
        A=0
    T = count_T(y, yt1max, yt2max, R, y2max)
    if isinstance(T, str):
        T=0
    P = count_P(y, yt1max, yt2max, R, y2max,R, ninety_minus_beta2, p1max, p2max)
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
        # print(A,T)
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
    (No,sta,y,yt1max, yt2max, R, y2max, b_output,
    ninety_minus_beta2, p1max, p2max,
    Q_output, n, Z, S,yc_value,t1max, a1max, a2max,Interval,Contraction,Sf0,speed_head0,E0) = params
    
    A = count_A(y, yt1max, yt2max, R, y2max, ninety_minus_beta2, t1max, a1max, a2max)
    T = count_T(y, yt1max, yt2max, R, y2max)
    P = count_P(y, yt1max, yt2max, R, y2max, b_output, ninety_minus_beta2, p1max, p2max)
    R_h=A/P	
    v=Q_output/A
    Sf=(v**2)*(n**2)/(R_h**(4/3))
    speed_head=(v**2)/(2*9.81)	
    E=Z+speed_head+y
    Fr=v/math.sqrt(9.81*A/T)	
    Water_level=y+Z
    Full=y/b_output*100
    hf=Interval*(Sf+Sf0)/2
    hce=Contraction*abs(speed_head0-speed_head)
    he=hf+hce
    control=E0-E-he
    data1={
        'No':No,
        'sta_output':sta,
        'Q_output':Q_output,
        'b_output':b_output,
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
#-----------------------------------supercritical end-------------------------------------------
#-----------------------------------critical start----------------------------------------------
def critical_cal(param):
    (yt1max, yt2max, R, y2max, R,
         ninety_minus_beta2, p1max, p2max,
         Q_tunnel, n, Z, t1max, a1max, a2max)=param
    ymax,ymin=findy(1000,0,param)
    y_star =  brentq(froude_minus_one,ymax,ymin, args=(param,) ,xtol=1e-4)
    return y_star
# ----------------------------------critical end-------------------------------------------------
#-----------------------------------subcritical start--------------------------------------------
def control_is_zero_(y, params):
    (R,Q_tunnel,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion,Sf0,speed_head0,E0)=params
    A = count_A(y, yt1max, yt2max, R, y2max, ninety_minus_beta2, t1max, a1max, a2max)
    if isinstance(A, str):
        A=0
    T = count_T(y, yt1max, yt2max, R, y2max)
    if isinstance(T, str):
        T=0
    P = count_P(y, yt1max, yt2max, R, y2max,R, ninety_minus_beta2, p1max, p2max)
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
            # print(y,Fr,control)
            return control
def findy__(ymax,ymin,params):
    
    for _ in range(ymax):
        control_max=control_is_zero_(ymax, params)
        if control_max!=999999:
            break
        else:
            ymax=ymax-1
    for _ in range(ymax):
        control_min=control_is_zero_(ymin, params)
        if control_min!=999999:
            break
        else:
            ymin=ymin+1
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
def next_result_(params):
    (No,sta,y,yt1max, yt2max, R, y2max, b_output,
    ninety_minus_beta2, p1max, p2max,
    Q_output, n, Z, S,yc_value,t1max, a1max, a2max,Interval,Exspansion,Sf0,speed_head0,E0) = params
    
    A = count_A(y, yt1max, yt2max, R, y2max, ninety_minus_beta2, t1max, a1max, a2max)
    T = count_T(y, yt1max, yt2max, R, y2max)
    P = count_P(y, yt1max, yt2max, R, y2max, b_output, ninety_minus_beta2, p1max, p2max)
    R_h=A/P	
    v=Q_output/A
    Sf=(v**2)*(n**2)/(R_h**(4/3))
    speed_head=(v**2)/(2*9.81)	
    E=Z+speed_head+y
    Fr=v/math.sqrt(9.81*A/T)	
    Water_level=y+Z
    Full=y/b_output*100
    hf=Interval*(Sf+Sf0)/2
    hce=Exspansion*abs(speed_head0-speed_head)
    he=hf+hce
    control=E0-E+he
    data1={
        'No':No,
        'sta_output':sta,
        'Q_output':Q_output,
        'b_output':b_output,
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
#-----------------------------------subcritical end----------------------------------------------
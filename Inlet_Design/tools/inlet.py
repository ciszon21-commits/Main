
from scipy.optimize import brentq
import math
def result_cal(L,paras):
    (Z1, y1, S1, Q, b1, b2, n, D_over_S_BC, Contraction_coef)=paras
    Z2=Z1-L*S1
    deltaZ=Z1-Z2
    yc1=(Q**2/(9.81*b1**2))**(1/3)
    A1=b1*y1
    P1=b1+2*y1
    R1=A1/P1
    V1=Q/A1
    Sf1=V1**2*n**2/(R1**(4/3))
    speeding_head1=V1**2/(2*9.81)
    E1=Z1+y1+speeding_head1
    yc2=(Q**2/(9.81*b2**2))**(1/3)
    y2= D_over_S_BC*yc2/100
    A2=b2*y2
    P2=2*y2+b2
    R2=A2/P2
    V2=Q/A2
    Sf2=((V2**2)*(n**2))/(R2**(4/3))
    speeding_head2=V2**2/(2*9.81)
    E2=y2+speeding_head2+deltaZ
    hf=(Sf1+Sf2)*L/2
    hce=Contraction_coef*abs(speeding_head1-speeding_head2)
    he=hf+hce
    E=y2+speeding_head2+Z2+he
    control=E1-E
    FR1=V1/(9.81*A1/b1)**0.5
    FR2=V2/(9.81*A2/b2)**0.5
    result=(Q,S1,Z1,Z2,deltaZ,b1,b2,L,n,y1,yc1,A1,P1,R1,V1,Sf1,speeding_head1,E1,y2,yc2,A2,P2,R2,V2,Sf2,speeding_head2,E2,hf,hce,he,E,control,FR1,FR2)
    return result
def result_cal_initial(y1_initial, paras):
    (
        Z1_initial, Z2_initial, L, Q,
        b0_initial, b1_initial, n,
        Contraction_coef
    ) = paras

    deltaZ_initial = Z1_initial - Z2_initial

    # Section 0
    y0_initial = ((Q ** 2) / (9.81 * b0_initial ** 2)) ** (1 / 3)
    yc0_initial = y0_initial
    A0_initial = b0_initial * y0_initial
    P0_initial = b0_initial + 2 * y0_initial
    R0_initial = A0_initial / P0_initial
    V0_initial = Q / A0_initial
    Sf0_initial = V0_initial ** 2 * n ** 2 / (R0_initial ** (4 / 3))
    speeding_head0_initial = V0_initial ** 2 / (2 * 9.81)
    E0_initial = Z1_initial + y0_initial + speeding_head0_initial

    # Section 1
    A1_initial = b1_initial * y1_initial
    P1_initial = b1_initial + 2 * y1_initial
    R1_initial = A1_initial / P1_initial
    V1_initial = Q / A1_initial
    Sf1_initial = V1_initial ** 2 * n ** 2 / (R1_initial ** (4 / 3))
    speeding_head1_initial = V1_initial ** 2 / (2 * 9.81)
    E1_initial = deltaZ_initial + y1_initial + speeding_head1_initial
    yc1_initial=(Q ** 2  / (9.81*b1_initial ** 2))**(1/3)

    # 損失計算
    hf_initial = (Sf0_initial + Sf1_initial) * L / 2
    hce_initial = Contraction_coef * abs(speeding_head0_initial - speeding_head1_initial)
    he_initial = hf_initial + hce_initial

    E_initial = Z2_initial + y1_initial + speeding_head1_initial + he_initial
    control_initial = E0_initial - E_initial
    FR1_initial=V0_initial/(9.81*A0_initial/b0_initial)**0.5
    FR2_initial=V1_initial/(9.81*A1_initial/b1_initial)**0.5
    result=(Q,Z1_initial, Z2_initial,deltaZ_initial,b0_initial, b1_initial,L,n,y0_initial,yc0_initial,A0_initial,P0_initial,R0_initial,
    V0_initial,Sf0_initial,speeding_head0_initial,E0_initial,y1_initial,yc1_initial,A1_initial,P1_initial,R1_initial,V1_initial,Sf1_initial,
    speeding_head1_initial,E1_initial,hf_initial,hce_initial,he_initial,E_initial,control_initial,FR1_initial,FR2_initial)
    return result
def control_is_zero(L,paras):
    result=result_cal(L,paras)
    (Q,S1,Z1,Z2,deltaZ,b1,b2,L,n,y1,yc1,A1,P1,R1,V1,Sf1,speeding_head1,E1,y2,yc2,A2,P2,R2,V2,Sf2,speeding_head2,E2,hf,hce,he,E,control,FR1,FR2)=result
    return control
def control_is_zero_initial(y1_initial, paras):
    (
        Z1_initial, Z2_initial, L, Q,
        b0_initial, b1_initial, n,
        Contraction_coef
    ) = paras

    deltaZ_initial = Z1_initial - Z2_initial

    # Section 0
    y0_initial = ((Q ** 2) / (9.81 * b0_initial ** 2)) ** (1 / 3)
    yc0_initial = y0_initial
    A0_initial = b0_initial * y0_initial
    P0_initial = b0_initial + 2 * y0_initial
    R0_initial = A0_initial / P0_initial
    V0_initial = Q / A0_initial
    Sf0_initial = V0_initial ** 2 * n ** 2 / (R0_initial ** (4 / 3))
    speeding_head0_initial = V0_initial ** 2 / (2 * 9.81)
    E0_initial = Z1_initial + y0_initial + speeding_head0_initial

    # Section 1
    A1_initial = b1_initial * y1_initial
    P1_initial = b1_initial + 2 * y1_initial
    R1_initial = A1_initial / P1_initial
    V1_initial = Q / A1_initial
    Sf1_initial = V1_initial ** 2 * n ** 2 / (R1_initial ** (4 / 3))
    speeding_head1_initial = V1_initial ** 2 / (2 * 9.81)
    E1_initial = deltaZ_initial + y1_initial + speeding_head1_initial

    # 損失計算
    hf_initial = (Sf0_initial + Sf1_initial) * L / 2
    hce_initial = Contraction_coef * abs(speeding_head0_initial - speeding_head1_initial)
    he_initial = hf_initial + hce_initial

    E_initial = Z2_initial + y1_initial + speeding_head1_initial + he_initial

    control_initial = E0_initial - E_initial
    FR2_initial=V1_initial/(9.81*A1_initial/b1_initial)**0.5
    if FR2_initial<1:
        control_initial=9999
        return control_initial
    return control_initial
def find_initial_y(ymax,ymin,paras):
    
    control_max =  control_is_zero_initial(ymax, paras)
    control_min =  control_is_zero_initial(ymin, paras)
    if control_max*control_min>0:
        delta=ymax-ymin
        step=0.01
        for _ in range(2500):
            ymin=ymin+step
            control_max =  control_is_zero_initial(ymax, paras)
            control_min =  control_is_zero_initial(ymin, paras)
            if control_max*control_min<0:
                return ymax,ymin
    else:
        return ymax,ymin

# Q=690 #input
# S1=0.2 #input
# Z1=21 #input
# b1=52.532 #input
# b2=12.5 #input
# n=0.018 #input
# D_over_S_BC=0.75#input
# Contraction_coef=0.12#input
# Ogee_crest_elv=24#input
# L_weir=62#input
# X_og=14#input
def inlet_table(Q,S1,Z1,b1,b2,n,D_over_S_BC,Contraction_coef,Ogee_crest_elv,L_weir,X_og):
    try:
        # print("==============先找初始值=============")
        Z1_initial=Ogee_crest_elv
        Z2_initial=Z1
        L=X_og
        b0_initial=L_weir
        b1_initial=b1
        para_initial=( Z1_initial, Z2_initial, L, Q,
                b0_initial, b1_initial, n,
                Contraction_coef)
        ymax,ymin=find_initial_y(0.1,100,para_initial)
        y_star =  brentq(control_is_zero_initial,ymax,ymin, args=(para_initial,) ,xtol=1e-4)
        all_result=[]
        y1=y_star#unknown
        # print(f"======初始值y1={y1}==============")
        No=1
        for _ in range(20):
            paras=(Z1, y1, S1, Q, b1, b2, n, D_over_S_BC, Contraction_coef)
            L_star=brentq(control_is_zero,-1e5, 1e6, args=(paras,) ,xtol=1e-4)
            L=L_star
            result=result_cal(L,paras)
            (Q,S1,Z1,Z2,deltaZ,b1,b2,L,n,y1,yc1,A1,P1,R1,V1,Sf1,speeding_head1,E1,y2,yc2,A2,P2,R2,V2,Sf2,speeding_head2,E2,hf,hce,he,E,control,FR1,FR2)=result
            data={"No": No,"Q": Q, "S1": S1, "Z1": Z1, "Z2": Z2, "deltaZ": deltaZ,"b1": b1, "b2": b2, "L": L, "n": n, "y1": y1, "yc1": yc1,"A1": A1, "P1": P1, "R1": R1, "V1": V1, "Sf1": Sf1,"speeding_head1": speeding_head1, "E1": E1, "y2": y2,"yc2": yc2, "A2": A2, "P2": P2, "R2": R2, "V2": V2,"Sf2": Sf2, "speeding_head2": speeding_head2, "E2": E2,"hf": hf, "hce": hce, "he": he, "E": E, "control": control,"FR1": FR1, "FR2": FR2}
            all_result.append(data)
            S1=(S1*100-1)/100
            No+=1
        return all_result,True
    except ValueError :
        return all_result,False
def inlet_initial_table(Q,S1,Z1,b1,b2,n,D_over_S_BC,Contraction_coef,Ogee_crest_elv,L_weir,X_og):
    try:
        # print("==============先找初始值=============")
        Z1_initial=Ogee_crest_elv
        Z2_initial=Z1
        L=X_og
        b0_initial=L_weir
        b1_initial=b1
        para_initial=( Z1_initial, Z2_initial, L, Q,
                b0_initial, b1_initial, n,
                Contraction_coef)
        ymax,ymin=find_initial_y(0.1,100,para_initial)
        y_star =  brentq(control_is_zero_initial,ymax,ymin, args=(para_initial,) ,xtol=1e-4)
        y1=y_star#unknown
        all_result=[]
        print(f"======初始值y1={y1}==============")
        paras=(Z1_initial, Z2_initial, L, Q,b0_initial, b1_initial, n,Contraction_coef)
        result=result_cal_initial(y1, paras)
        (Q,Z1_initial, Z2_initial,deltaZ_initial,b0_initial, b1_initial,L,n,y0_initial,yc0_initial,A0_initial,P0_initial,R0_initial,
    V0_initial,Sf0_initial,speeding_head0_initial,E0_initial,y1_initial,yc1_initial,A1_initial,P1_initial,R1_initial,V1_initial,Sf1_initial,
    speeding_head1_initial,E1_initial,hf_initial,hce_initial,he_initial,E_initial,control_initial,FR1_initial,FR2_initial)=result
        data={"Q": Q, "Z1": Z1_initial, "Z2": Z2_initial, "deltaZ": deltaZ_initial,"b0": b0_initial, "b1": b1_initial, "L": L, "n": n, "y0": y0_initial, "yc0": yc0_initial,
        "A0": A0_initial, "P0": P0_initial, "R0": R0_initial, "V0": V0_initial, "Sf0": Sf0_initial,"speeding_head0": speeding_head0_initial, 
        "E0": E0_initial, "y1": y1_initial,"yc1": yc1_initial, "A1": A1_initial, "P": P1_initial, "R1": R1_initial, "V1": V1_initial,"Sf1": Sf1_initial
        , "speeding_head1": speeding_head1_initial, "E1": E1_initial,"hf": hf_initial, "hce": hce_initial, "he": he_initial, "E": E_initial, "control": control_initial,"FR1": FR1_initial, "FR2": FR2_initial}
        all_result.append(data)
        return all_result,True
    except ValueError :
        return all_result,False

def draw_inlet(ty,l_total,rwx,inlet_alpha2,R_wall,R_center):
    try:
        wall_curve=draw_wall_curve(ty,l_total,rwx,inlet_alpha2,R_wall,R_center)
        all_result=wall_curve
        return all_result,True
    except ValueError as error:
        return {"error":error},False
def draw_wall_curve(ty,l_total,rwx,inlet_alpha2,R_wall,R_center):
    wall_curve_left=[[l_total,ty],[rwx,ty]]
    wall_curve_right=[[l_total,ty*-1],[rwx,ty*-1]]
    for i in range(100):
        percentage=i/100
        x=rwx-R_wall*math.sin(math.radians(inlet_alpha2*percentage))
        y=(ty*-1)-(R_wall-R_wall*math.cos(math.radians(inlet_alpha2*percentage)))
        wall_curve_left.append([x,y*-1])
        wall_curve_right.append([x,y])
    left_zero=[0,R_center*math.tan(math.radians(inlet_alpha2))]
    right_zero=[0,-1*R_center*math.tan(math.radians(inlet_alpha2))]
    wall_curve_left.append(left_zero)
    wall_curve_right.append(right_zero)
    return {"wall_curve_left":wall_curve_left,"wall_curve_right":wall_curve_right}
def draw_toe_curve(Ogee_length,R_ds,inlet_alpha2):
    data=[]
    for i in range(100):
        percentage=1-i/100
        x=Ogee_length+(R_ds-R_ds*math.cos(math.radians(inlet_alpha2*percentage)))
        y=0+R_ds*math.sin(math.radians(inlet_alpha2*percentage))
        data.append([x,y])
    for i in range(100):
        percentage=i/100
        x=Ogee_length+(R_ds-R_ds*math.cos(math.radians(inlet_alpha2*percentage)))
        y=0-R_ds*math.sin(math.radians(inlet_alpha2*percentage))
        data.append([x,y])
    return data
def draw_US_curve(X_upstream,R_us,inlet_alpha2):
    data=[]
    
    for i in range(100):
        percentage=1-i/100
        x=-1*X_upstream+(R_us-R_us*math.cos(math.radians(inlet_alpha2*percentage)))
        y=0+R_us*math.sin(math.radians(inlet_alpha2*percentage))
        data.append([x,y])
    for i in range(100):
        percentage=i/100
        x=-1*X_upstream+(R_us-R_us*math.cos(math.radians(inlet_alpha2*percentage)))
        y=0-R_us*math.sin(math.radians(inlet_alpha2*percentage))
        data.append([x,y])
    return data
def draw_center_curve(R_center,inlet_alpha2):
    data=[]
    for i in range(100):
        percentage=1-i/100
        x=0+(R_center-R_center*math.cos(math.radians(inlet_alpha2*percentage)))
        y=0+R_center*math.sin(math.radians(inlet_alpha2*percentage))
        data.append([x,y])
    for i in range(100):
        percentage=i/100
        x=0+(R_center-R_center*math.cos(math.radians(inlet_alpha2*percentage)))
        y=0-R_center*math.sin(math.radians(inlet_alpha2*percentage))
        data.append([x,y])
    return data
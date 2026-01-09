import math
from scipy.optimize import brentq

def  transition_shape_circle(para):
    (Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type)=para
    Trial=0
    result=[]
    for _ in range(20):
        
        Trial=Trial+1
        para=(Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type)
        Lmax,Lmin=findL(1000000,2,para)
        L_star =  brentq(control_is_zero,Lmax,Lmin, args=(para,) ,xtol=1e-5)
        para_=(Trial,Q,L_star,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type)
        data=result_all(para_)
        result.append(data)
        S1=int(S1*100-1)/100
    return result
def transition_shape_horseshoe(para):
    (Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type,yt1max,yt2max,y2max,B3,t1max,a1max,a2max,p1max,p2max)=para
    Trial=0
    result=[]
    for _ in range(20):
        
        Trial=Trial+1
        para=(Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type,yt1max,yt2max,y2max,B3,t1max,a1max,a2max,p1max,p2max)
        Lmax,Lmin=findL(1000000,2,para)
        L_star =  brentq(control_is_zero,Lmax,Lmin, args=(para,) ,xtol=1e-5)
        para_=(Trial,Q,L_star,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type,yt1max,yt2max,y2max,B3,t1max,a1max,a2max,p1max,p2max)
        data=result_all(para_)
        result.append(data)
        S1=int(S1*100-1)/100
    return result

def findL(Lmax,Lmin,params):
    control_max=control_is_zero(Lmax, params)
    control_min=control_is_zero(Lmin, params)
    
    if  control_max*control_min>0:
        if control_max>0:
            times=5
            Lmax_=Lmax
            for _ in range(times):
                Lmax_=Lmax_*10
                control_max=control_is_zero(Lmax_, params)
                if control_max * control_min < 0:
                    Lmax=Lmax_
                    return Lmax_, Lmin
        if control_min<0:
            times=5
            Lmin_=Lmin
            for _ in range(times):
                Lmin_=Lmin_-100
                control_min=control_is_zero(Lmin_, params)
                print(control_max,control_min)
                if control_max * control_min < 0:
                    return Lmax, Lmin_
    return Lmax, Lmin
def control_is_zero(L, para):
    if 'horseshoe'  in  para:
        (Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type,yt1max,yt2max,y2max,B3,t1max,a1max,a2max,p1max,p2max)=para
        param=(0,Q,L,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type,yt1max,yt2max,y2max,B3,t1max,a1max,a2max,p1max,p2max)
        data=result_all(param)
        control=data['control']
    elif 'circle' in para:
        (Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type)=para
        param=(0,Q,L,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type)
        data=result_all(param)
        control=data['control']
    return control
def result_all(para):
    if 'horseshoe'in  para:
        (Trial,Q,L,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type,yt1max,yt2max,y2max,B3,t1max,a1max,a2max,p1max,p2max)=para
        Z3=Z2-S1*L
        deltaZ=Z2-Z3
        yc2=((Q**2)/(9.81*(b2**2)))**(1/3)
        A2=b2*y2
        P2=y2*2+b2
        R2=A2/P2
        V2=Q/A2
        SF2=(V2**2)*(n**2)/(R2**(4/3))
        speed_head2=(V2**2)/(2*9.81)
        E1=Z2+y2+speed_head2
        radd3=b3/2
        raddi=b3
        beta3=B3
        A3, P3=calculate_area_and_perimeter_hs(y3,yt1max,yt2max,y2max,raddi,radd3,t1max,a1max,a2max,beta3,p1max,p2max)
        R3=A3/P3
        T3=calculate_top_width(y3,yt1max,yt2max,y2max,raddi,radd3)
        V3=Q/A3
        SF3=(V3**2)*(n**2)/(R3**(4/3))
        speed_head3=(V3**2)/(2*9.81)
        E3=Z3+y3+speed_head3
        hf=((SF2+SF3)/2)*L
        hce=C*abs( speed_head2- speed_head3)
        he=hf+hce
        E3_=speed_head3+Z3+he+y3
        control = E3_-E1
        Fr2 = V2 / math.sqrt(9.81 * A2 / b2)
        Fr3 = V3 / math.sqrt(9.81 * A3 / T3)
        data={
            'Trial':Trial,
            'Q':Q,
            'S':S1,
            'Z2':Z2,
            'Z3':Z3,
            'deltaZ':deltaZ,
            'b2':b2,
            'b3':b3,
            'L':L,
            'n':n,
            'y2':y2,
            'yc2':yc2,
            'A2':A2,
            'P2':P2,
            'R2':R2,
            'V2':V2,
            'SF2':SF2,
            'speeding_head2':speed_head2,
            'E1':E1,
            'y3':y3,
            'yc3':yc3,
            'A3':A3,
            'P3':P3,
            'R3':R3,
            'T3':T3,
            'V3':V3,
            'SF3':SF3,
            'speeding_head3':speed_head3,
            'E3':E3,
            'hf':hf,
            'hce':hce,
            'he':he,
            'E3_':E3_,
            'control':control,
            'FR2':Fr2,
            'FR3':Fr3,
        }
    elif 'circle' in para:
        (Trial,Q,L,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_typ)=para
        Z3=Z2-S1*L
        deltaZ=Z2-Z3
        yc2=((Q**2)/(9.81*(b2**2)))**(1/3)
        A2=b2*y2
        P2=y2*2+b2
        R2=A2/P2
        V2=Q/A2
        SF2=(V2**2)*(n**2)/(R2**(4/3))
        speed_head2=(V2**2)/(2*9.81)
        E1=Z2+y2+speed_head2
        A3=circular_section_area(y3, b3)
        P3=circular_section_perimeter(y3, b3)
        R3=A3/P3
        T3=circular_top_width(y3, b3)
        V3=Q/A3
        SF3=(V3**2)*(n**2)/(R3**(4/3))
        speed_head3=(V3**2)/(2*9.81)
        E3=Z3+y3+speed_head3
        hf=((SF2+SF3)/2)*L
        hce=C*abs( speed_head2- speed_head3)
        he=hf+hce
        E3_=speed_head3+Z3+he+y3
        control = E3_-E1
        Fr2 = V2 / math.sqrt(9.81 * A2 / b2)
        Fr3 = V3 / math.sqrt(9.81 * A3 / T3)
        data={
            'Trial':Trial,
            'Q':Q,
            'S':S1,
            'Z2':Z2,
            'Z3':Z3,
            'deltaZ':deltaZ,
            'b2':b2,
            'b3':b3*2,
            'L':L,
            'n':n,
            'y2':y2,
            'yc2':yc2,
            'A2':A2,
            'P2':P2,
            'R2':R2,
            'V2':V2,
            'SF2':SF2,
            'speeding_head2':speed_head2,
            'E1':E1,
            'y3':y3,
            'yc3':yc3,
            'A3':A3,
            'P3':P3,
            'R3':R3,
            'T3':T3,
            'V3':V3,
            'SF3':SF3,
            'speeding_head3':speed_head3,
            'E3':E3,
            'hf':hf,
            'hce':hce,
            'he':he,
            'E3_':E3_,
            'control':control,
            'FR2':Fr2,
            'FR3':Fr3,
        }
    return data
def calculate_area_and_perimeter_hs(
    y3,
    yt1max,
    yt2max,
    y2max,
    raddi,
    radd3,
    t1max,
    a1max,
    a2max,
    beta3,
    p1max,
    p2max):
    """
    根據水位 y3 計算斷面積 A3 與濕周長 P3（適用於三段式圓/馬蹄/拱形通道）
    """

    if y3 <= yt1max:
        # === 第一段：圓弧段 ===
        theta = math.acos((raddi - y3) / raddi)

        A3 = raddi**2 * (
            2 * math.degrees(theta) / 360 * math.pi
            - math.sin(theta) * math.cos(theta)
        )

        P3 = 2 * math.degrees(theta) / 180 * math.pi * raddi

    elif y3 <= yt2max:
        # === 第二段：馬蹄形段 ===
        theta = math.acos((y2max - (y3 - yt1max)) / raddi)
        angle_deg = math.degrees(theta)
        delta_angle = angle_deg - beta3

        area_arc = delta_angle / 360 * math.pi * raddi**2
        area_triangle = math.sin(math.radians(delta_angle / 2)) * math.cos(math.radians(delta_angle / 2)) * raddi**2
        extra = (((y2max - (y3 - yt1max)) * math.tan(math.radians(angle_deg)) - radd3) * 2 + t1max) * (y3 - yt1max) / 2

        A3 = (area_arc - area_triangle) * 2 + extra + a1max
        P3 = delta_angle / 180 * 2 * math.pi * raddi + p1max

    else:
        # === 第三段：拱形上段 ===
        theta = math.acos((y3 - yt2max) / (raddi / 2))

        A3 = (
            (raddi**2 / 4) * math.cos(theta) * math.sin(theta)
            + (90 - math.degrees(theta)) / 360 * math.pi * raddi**2 / 4 * 2
            + a2max
        )

        P3 = (90 - math.degrees(theta)) / 180 * math.pi * raddi + p2max

    return A3, P3
def calculate_top_width(y3,yt1max,yt2max,y2max,raddi,radd3):
    """
    根據水位 y3 計算對應的水面寬度（Top Width）
    """

    if y3 <= yt1max:
        # 第一段：圓弧段
        theta = math.acos((raddi - y3) / raddi)
        top_width = 2 * raddi * math.sin(theta)

    elif y3 <= yt2max:
        # 第二段：馬蹄形中段
        theta = math.acos((y2max - (y3 - yt1max)) / raddi)
        top_width = ((y2max - (y3 - yt1max)) * math.tan(theta) - radd3) * 2

    else:
        # 第三段：上拱段
        theta = math.acos((y3 - yt2max) / (raddi / 2))
        top_width = raddi * math.sin(theta)

    return top_width    

def circular_section_area(T32, radcircle):
    """
    計算 T32 水深於圓形斷面通道內的實際流通面積
    T32: 水深
    radcircle: 圓半徑
    """
    if T32 <= radcircle:
        theta = math.acos((radcircle - T32) / radcircle)
        area = radcircle**2 * (
            2 * math.degrees(theta) / 360 * math.pi
            - math.sin(theta) * math.cos(theta)
        )
    else:
        theta = math.acos((T32 - radcircle) / radcircle)
        area = radcircle**2 * (
            math.pi
            - 2 * math.degrees(theta) / 360 * math.pi
            + math.sin(theta) * math.cos(theta)
        )

    return area
def circular_section_perimeter(T32, radcircle):
    """
    計算圓形斷面通道在水深 T32 下的濕周長（Wet Perimeter）

    T32: 水深
    radcircle: 圓半徑
    """
    if T32 <= radcircle:
        theta = math.acos((radcircle - T32) / radcircle)
        perimeter = 2 * math.degrees(theta) / 180 * math.pi * radcircle
    else:
        theta = math.acos((T32 - radcircle) / radcircle)
        perimeter = math.pi * radcircle * (2 - 2 * math.degrees(theta) / 180)

    return perimeter
def circular_top_width(T32, radcircle):
    """
    計算圓形斷面在水深 T32 下的水面寬度（Top Width）

    T32: 水深
    radcircle: 圓半徑
    """
    if T32 <= radcircle:
        theta = math.acos((radcircle - T32) / radcircle)
    else:
        theta = math.acos((T32 - radcircle) / radcircle)

    width = 2 * radcircle * math.sin(theta)
    return width

def transition_data(B2,Z2,Z3,B3,choose_tunnel_type,stastart,ltotal,l2,beta1,beta2,yt2max):
    points=1000
    x0,y0=-1*B2/2,Z2
    x1,y1=B2/2,Z2+B2
    rectangle=[[x0,y0]]
    
    for i in range(points):
        data=[x0,y0+(y1-y0)*i/points]
        rectangle.append(data)
    rectangle.append([x0,y1])
    for i in range(points):
        data=[x0+(x1-x0)*i/points,y1]
        rectangle.append(data)
    rectangle.append([x1,y1])
    for i in range(points):
        data=[x1,y1-(y1-y0)*i/points]
        rectangle.append(data)
    rectangle.append([x1,y0])
    for i in range(points):
        data=[x1-(x1-x0)*i/points,y0]
        rectangle.append(data)
    circle_or_horseshoe=[]
    if choose_tunnel_type=='circle':
        for i in range(points):
            angle_deg = 360 * i / points
            angle_rad = math.radians(angle_deg)
            x = B3/2 * math.cos(angle_rad)
            y = B3/2 * math.sin(angle_rad)
            data=[x,y+B3/2+Z3]
            circle_or_horseshoe.append(data)
    elif choose_tunnel_type=='horseshoe':
        add_y=+B3/2+Z3
        #第一象限
        for i in range(points):
            angle_deg = 90 * i / points
            angle_rad = math.radians(angle_deg)
            x = B3/2 * math.cos(angle_rad)
            y = B3/2 * math.sin(angle_rad)
            data=[x,y+add_y]
            circle_or_horseshoe.append(data)
        #第二象限
        for i in range(points):
            angle_deg = 90 * i / points
            angle_rad = math.radians(angle_deg)
            x = -B3/2 * math.cos(angle_rad)
            y = B3/2 * math.sin(angle_rad)
            data=[x,y+add_y]
            circle_or_horseshoe.append(data)
        #第三象限A
        points_=int(points/2)
        for i in range(points_):
            angle_deg = beta2 * i / points_
            angle_rad = math.radians(angle_deg)
            x = B3/2- B3* math.cos(angle_rad)
            y = -1*B3 * math.sin(angle_rad)
            data=[x,y+add_y]
            circle_or_horseshoe.append(data)
        #第三象限B
        for i in range(points_):
            angle_deg = (beta1/2) * i / points_
            angle_rad = math.radians(angle_deg)
            x = -1*B3*math.sin(angle_rad)
            y = (B3 -1*B3* math.cos(angle_rad))-yt2max
            data=[x,y+add_y]
            circle_or_horseshoe.append(data)
        #第四象限A
        points_=int(points/2)
        for i in range(points_):
            angle_deg = beta2 * i / points_
            angle_rad = math.radians(angle_deg)
            x = -1*B3/2+ B3* math.cos(angle_rad)
            y = -1*B3 * math.sin(angle_rad)
            data=[x,y+add_y]
            circle_or_horseshoe.append(data)
        #第四象限B
        for i in range(points_):
            angle_deg = (beta1/2) * i / points_
            angle_rad = math.radians(angle_deg)
            x = B3*math.sin(angle_rad)
            y = (B3 -1*B3* math.cos(angle_rad))-yt2max
            data=[x,y+add_y]
            circle_or_horseshoe.append(data)

    left_wall=[[stastart+ltotal,B2/2],[stastart+ltotal+l2,B3/2]]
    right_wall=[[stastart+ltotal,-1*B2/2],[stastart+ltotal+l2,-1*B3/2]]
    upstream=[[stastart+ltotal,B2/2],[stastart+ltotal,-1*B2/2]]
    downstream=[[stastart+ltotal+l2,B3/2],[stastart+ltotal+l2,-1*B3/2]]
    top1=[[stastart+ltotal,Z2+B2+1],[stastart+ltotal+l2,Z2+B2+1]]
    top2=[[stastart+ltotal,Z2+B2],[stastart+ltotal+l2,Z3+B3]]
    bottom=[[stastart+ltotal,Z2],[stastart+ltotal+l2,Z3]]
    transition_layout_xmax=int(downstream[1][0])+2
    transition_layout_xmin=((upstream[0][0]//5)-1)*5
    transition_layout_ymax=int(upstream[0][1])+2
    transition_layout_ymin=int(upstream[1][1])-2
    transition_profile_ymax=(top1[0][1]//5+1)*5


    return{
        'rectangle':rectangle,
        'circle_or_horseshoe':circle_or_horseshoe,
        'left_wall':left_wall,
        'right_wall':right_wall,
        'upstream':upstream,
        'downstream':downstream,
        'top1':top1,
        'top2':top2,
        'bottom':bottom,
        'transition_layout_xmax':transition_layout_xmax,
        'transition_layout_xmin':transition_layout_xmin,
        'transition_layout_ymax':transition_layout_ymax,
        'transition_layout_ymin':transition_layout_ymin,
        'transition_profile_ymax':transition_profile_ymax
    }

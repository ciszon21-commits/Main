import numpy as np
import math

def find_circle_intersections(x1, y1, r1, x2, y2, r2):
    # 計算兩圓心之間的距離
    d = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    # 檢查是否有交點
    if d > r1 + r2 or d < abs(r1 - r2) or d == 0:
        return np.nan,np.nan  # 無交點或無法確定
    
    # 計算交點的參數
    a = (r1**2 - r2**2 + d**2) / (2 * d)
    h = math.sqrt(abs(r1**2 - a**2))
    
    # 計算圓心之間的向量
    x0 = x1 + a * (x2 - x1) / d
    y0 = y1 + a * (y2 - y1) / d
    
    # 計算交點
    x3_1 = x0 + h * (y2 - y1) / d
    y3_1 = y0 - h * (x2 - x1) / d
    x3_2 = x0 - h * (y2 - y1) / d
    y3_2 = y0 + h * (x2 - x1) / d
    
    if y3_2>y3_1:
        return x3_2,y3_2
    else:
        return x3_1,y3_1
def circle_data(xc,yc,r,step):
    points=1000
    data=[]
    
    for i in range(points):
        if i%50>step:
            angle=2*np.pi*i/points
            x=xc+np.sin(angle)*r
            y=yc+np.cos(angle)*r
            data.append([x,y])
        else:
            continue
    return data
def circle_data_cal(xc,yc,r):
    points=1000
    data=[]
    for i in range(points):
        angle=2*np.pi*i/points
        x=xc+np.sin(angle)*r
        y=yc+np.cos(angle)*r
        if  y>yc:
            data.append([x,y])
        else:
            continue
    return data
def equation(ho,n,k,x_):
    R=1.5*ho
    data=[]

    for i in  range(120):
        x=i/10
        y=-1*ho*k*(x/ho)**n
        if y<ho*-0.5:
            break
        else:
            data.append([x,y])
    #Curve transition---------------------------------------------
    y_at_half=-0.5*ho
    x_at_half = ho * (abs(y_at_half) / (ho * k)) ** (1 / n)
    data.append([x_at_half,y_at_half])
    y_bot=-1*np.tan(np.deg2rad(45))*(ho-abs(y_at_half))
    x_bot=x_at_half+abs(y_at_half)
    aplha=67.5
    y_bot2=-1*ho
    x_bot2=R/np.tan(np.deg2rad(aplha))+x_bot

    percentage_list=[i/100 for i in range(0,102,2)]
    for p in percentage_list:
        angle_deg = 45*(1-p)
        angle_rad = np.deg2rad(angle_deg) 
        x=x_bot2-(R*np.sin(angle_rad))
        y=y_bot2+(R-R*np.cos(angle_rad))
        data.append([x,y])

    #flat------------------------------------------------------------
    for _ in range(1):
        x=int(x)+1
        y=-1*ho
        data.append([x,y])
    
        
    return data,x_bot2,y_bot2
def ogee_data_process(circle_r1_,circle_r3_,p,xc,yc,x4,n,k,ho,x):
    p_level=-1*p
    xc_place=-1*xc
    yc_place=-1*yc
    flat=[[int(xc_place)-5,p_level],[int(xc_place)-4,p_level],[int(xc_place)-3,p_level],[int(xc_place)-2,p_level],[xc_place,p_level],[xc_place,(p_level+yc_place)/2],[xc_place,yc_place]]
    circle_r3_list=[item for item in circle_r3_ if (item[0] >= xc_place and item[0] <= x4)]
    circle_r1_list=[item for item in circle_r1_ if (item[0] >= x4 and item[0] <= 0)]
    equation_list,x_bot2,y_bot2=equation(ho,n,k,x)
    merge=flat+circle_r3_list+circle_r1_list+equation_list
    return merge,x_bot2,y_bot2
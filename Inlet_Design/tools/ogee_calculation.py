from .circle import circle_data,find_circle_intersections,circle_data_cal,ogee_data_process
def ogee_data(r1,r2,p,Hd,hd,d,x,xc,yc,n,k):
    circle_r1=circle_data(0,-1*r1,r1,20)
    circle_r2=circle_data(-1*xc,-1*yc,r2,20)
    circle_r1_minus_r2=circle_data(0,-1*r1,r1-r2,20)
    x3,y3=find_circle_intersections(0,-1*r1,r1-r2,-1*xc,-1*yc,r2)
    circle_r3=circle_data(x3,y3,r2,20)
    x4,y4=find_circle_intersections(x3,y3,r2,0,-1*r1,r1)
    circle_r1_=circle_data_cal(0,-1*r1,r1)
    circle_r3_=circle_data_cal(x3,y3,r2)
    ogee_result,x_bot2,y_bot2=ogee_data_process(circle_r1_,circle_r3_,p,xc,yc,x4,n,k,Hd,x)
    return {
            "circle_r1":circle_r1,
            "circle_r2":circle_r2,
            "circle_r1_minus_r2":circle_r1_minus_r2,
            "circle_r3":circle_r3,
            "ogee_result":ogee_result,
            "x_bot2":x_bot2,
            "y_bot2":y_bot2
    }
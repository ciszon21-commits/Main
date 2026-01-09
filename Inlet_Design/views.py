from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
import math
from .tools.step1_calculation import step1_cal
from .tools.ogee_calculation import ogee_data
from .tools.horseshoe import horseshoe_data,supercritical_data,subcritical_data,critical_data
from .tools.round import round_data,supercritical_round_data,subcritical_round_data,critical_round_data
from .tools.inlet import inlet_table,inlet_initial_table,draw_inlet,draw_toe_curve,draw_US_curve,draw_center_curve
from .tools.transition import transition_shape_circle,transition_shape_horseshoe,transition_data
from .tools.waterlevel import waterlevel_data

# Create your views here.
def inlet_design(request):
    return render(request, 'Inlet_Design/home.html')
@csrf_exempt  # If you want to disable CSRF protection for testing (not recommended in production)
def calculate_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            he = float(data.get('He', 0))
            P = float(data.get('P', 0))
            L = float(data.get('L', 0))
            X = float(data.get('X', 0))
            c_assump = float(data.get('C-assump', 2.15))
            n = float(data.get('n', 0.015))
            result=step1_cal(he,P,L,X,c_assump,n)
            # Perform your calculation logic here
            # result = {"status": "success", "message": "Calculation complete", "He": He, "P": P, "L": L, "X": X}

            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
@csrf_exempt  # If you want to disable CSRF protection for testing (not recommended in production)
def ogee(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            r1 = float(data.get('r1', 0))
            r2 = float(data.get('r2', 0))
            p = float(data.get('p', 0))
            Hd = float(data.get('Hd', 0))
            hd = float(data.get('hd', 0))
            d = float(data.get('d', 0))
            x = float(data.get('x', 0))
            xc = float(data.get('xc', 0))
            yc = float(data.get('yc', 0))
            n = float(data.get('n', 0))
            k=float(data.get('k', 0))
            result=ogee_data(r1,r2,p,Hd,hd,d,x,xc,yc,n,k)
            # Perform your calculation logic here
            # result = {"status": "success", "message": "Calculation complete", "He": He, "P": P, "L": L, "X": X}

            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@csrf_exempt
def horseshoe(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            R= float(data.get("R",0))
            Q_tunnel=float(data.get("Q_tunnel",0))
            B2= float(data.get("B2",0))
            B1= float(data.get("B1",0))
            ninety_minus_beta2= float(data.get("ninety_minus_beta2",0))
            yt1max= float(data.get("yt1max",0))
            t1max= float(data.get("t1max",0))
            p1max= float(data.get("p1max",0))
            a1max= float(data.get("a1max",0))
            yt2max= float(data.get("yt2max",0))
            t2max= float(data.get("t2max",0))
            p2max= float(data.get("p2max",0))
            a2max= float(data.get("a2max",0))
            y2max= float(data.get("y2max",0))
            n = float(data.get("n_tunnel",0))
            Z = float(data.get("Z_tunnel",0))
            S=float(data.get("S_tunnel",0))
            yc_value=float(data.get("yc_value",0))
            Critical_depth=float(data.get("Critical_depth",0))
            data1=horseshoe_data(R,Q_tunnel,B1,B2,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth)
            return JsonResponse(data1)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@csrf_exempt
def horseshoe_supercritical_table(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            R= float(data.get("R",0))
            Q_tunnel=float(data.get("Q_tunnel",0))
            B2= float(data.get("B2",0))
            B1= float(data.get("B1",0))
            ninety_minus_beta2= float(data.get("ninety_minus_beta2",0))
            yt1max= float(data.get("yt1max",0))
            t1max= float(data.get("t1max",0))
            p1max= float(data.get("p1max",0))
            a1max= float(data.get("a1max",0))
            yt2max= float(data.get("yt2max",0))
            t2max= float(data.get("t2max",0))
            p2max= float(data.get("p2max",0))
            a2max= float(data.get("a2max",0))
            y2max= float(data.get("y2max",0))
            n = float(data.get("n_tunnel",0))
            Z = float(data.get("Z_tunnel",0))
            S=float(data.get("S_tunnel",0))
            yc_value=float(data.get("yc_value",0))
            Critical_depth=float(data.get("Critical_depth",0))
            Tunnel_length=float(data.get("Tunnel_length",0))
            Interval=float(data.get("Interval",0))
            Contraction=float(data.get("Contraction",0))
            data1=horseshoe_data(R,Q_tunnel,B1,B2,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth)
            para_for_supercritical=(R,Q_tunnel,B1,B2,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,data1)
            data2,status=supercritical_data(para_for_supercritical)
            data3={'data':data2,'status':status}
            return JsonResponse(data3)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
@csrf_exempt
def horseshoe_subcritical_table(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            R= float(data.get("R",0))
            Q_tunnel=float(data.get("Q_tunnel",0))
            B2= float(data.get("B2",0))
            B1= float(data.get("B1",0))
            ninety_minus_beta2= float(data.get("ninety_minus_beta2",0))
            yt1max= float(data.get("yt1max",0))
            t1max= float(data.get("t1max",0))
            p1max= float(data.get("p1max",0))
            a1max= float(data.get("a1max",0))
            yt2max= float(data.get("yt2max",0))
            t2max= float(data.get("t2max",0))
            p2max= float(data.get("p2max",0))
            a2max= float(data.get("a2max",0))
            y2max= float(data.get("y2max",0))
            n = float(data.get("n_tunnel",0))
            Z = float(data.get("Z_tunnel",0))
            S=float(data.get("S_tunnel",0))
            yc_value=float(data.get("yc_value",0))
            Critical_depth=float(data.get("Critical_depth",0))
            Tunnel_length=float(data.get("Tunnel_length",0))
            Interval=float(data.get("Interval",0))
            Contraction=float(data.get("Contraction",0))
            Exspansion=float(data.get("Exspansion",0))
            data1=horseshoe_data(R,Q_tunnel,B1,B2,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth)
            Z_critical=Z-Tunnel_length*S/100
            critical_para=(R,Q_tunnel,B1,B2,ninety_minus_beta2,
            yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,
            y2max,n,Z_critical,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction)
            critical_data_=critical_data(critical_para)
            para_for_subcritical=(R,Q_tunnel,B1,B2,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion,critical_data_)
            data2,status=subcritical_data(para_for_subcritical)
            sorted_data = sorted(data2, key=lambda x: x['No'])
            sorted_data[-1]['hf_output']='-'
            sorted_data[-1]['hce_output']='-'
            sorted_data[-1]['h_output']='-'
            data3={'data':sorted_data,'status':status}
            return JsonResponse(data3)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@csrf_exempt
def round(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            R= float(data.get("R",0))
            Q_tunnel=float(data.get("Q_tunnel",0))
            n = float(data.get("n_tunnel",0))
            Z = float(data.get("Z_tunnel",0))
            S=float(data.get("S_tunnel",0))
            yc_value=float(data.get("yc_value",0))
            Critical_depth=float(data.get("Critical_depth",0))
            Tunnel_length=float(data.get("Tunnel_length",0))
            Interval=float(data.get("Interval",0))
            Contraction=float(data.get("Contraction",0))
            Exspansion=float(data.get("Exspansion",0))
            param=(R,Q_tunnel,n,Z,S,yc_value,Critical_depth)

            data1=round_data(param)
            return JsonResponse(data1)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
@csrf_exempt
def round_supercritical_table(request):
    if request.method =="POST":
        try:
            data = json.loads(request.body)
            R= float(data.get("R",0))
            Q_tunnel=float(data.get("Q_tunnel",0))
            n = float(data.get("n_tunnel",0))
            Z = float(data.get("Z_tunnel",0))
            S=float(data.get("S_tunnel",0))
            yc_value=float(data.get("yc_value",0))
            Critical_depth=float(data.get("Critical_depth",0))
            Tunnel_length=float(data.get("Tunnel_length",0))
            Interval=float(data.get("Interval",0))
            Contraction=float(data.get("Contraction",0))
            Exspansion=float(data.get("Exspansion",0))
            param=(R,Q_tunnel,n,Z,S,yc_value,Critical_depth)
            data1=round_data(param)
            para_for_supercritical=(R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Contraction,data1)
            data2,status=supercritical_round_data(para_for_supercritical)
            data3={'data':data2,'status':status}
            return JsonResponse(data3)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@csrf_exempt
def round_subcritical_table(request):
    if request.method =="POST":
        try:
            data = json.loads(request.body)
            R= float(data.get("R",0))
            Q_tunnel=float(data.get("Q_tunnel",0))
            n = float(data.get("n_tunnel",0))
            Z = float(data.get("Z_tunnel",0))
            S=float(data.get("S_tunnel",0))
            yc_value=float(data.get("yc_value",0))
            Critical_depth=float(data.get("Critical_depth",0))
            Tunnel_length=float(data.get("Tunnel_length",0))
            Interval=float(data.get("Interval",0))
            Contraction=float(data.get("Contraction",0))
            Exspansion=float(data.get("Exspansion",0))
            Z_critical=Z-Tunnel_length*S/100
            critical_round_para=(R,Q_tunnel,n,Z_critical,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion)
            critical_data_=critical_round_data(critical_round_para)
            para_for_subcritical=(R,Q_tunnel,n,Z,S,yc_value,Critical_depth,Tunnel_length,Interval,Exspansion,critical_data_)
            data2,status=subcritical_round_data(para_for_subcritical)
            sorted_data = sorted(data2, key=lambda x: x['No'])
            sorted_data[-1]['hf_output']='-'
            sorted_data[-1]['hce_output']='-'
            sorted_data[-1]['h_output']='-'
            data3={'data':sorted_data,'status':status}
            return JsonResponse(data3)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
@csrf_exempt
def inlet_transition_table(request):
    if request.method =="POST":
        try:
            data = json.loads(request.body)
            Q= float(data.get("Q",0))
            S1=float(data.get("S1",0))
            Z1 = float(data.get("Z1",0))
            b1 = float(data.get("b1",0))
            b2=float(data.get("b2",0))
            n=float(data.get("n",0))
            D_over_S_BC=float(data.get("D_over_S_BC",0))
            Contraction_coef=float(data.get("Contraction_coef",0))
            Ogee_crest_elv=float(data.get("Ogee_crest_elv",0))
            L_weir=float(data.get("L_weir",0))
            X_og=float(data.get("X_og",0))
            data2,status=inlet_table(Q,S1,Z1,b1,b2,n,D_over_S_BC,Contraction_coef,Ogee_crest_elv,L_weir,X_og)
            sorted_data = sorted(data2, key=lambda x: x['No'])
            data3={'data':sorted_data,'status':status}
            return JsonResponse(data3)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
@csrf_exempt
def inlet_transition_initial_table(request):
    if request.method =="POST":
        try:
            data = json.loads(request.body)
            Q= float(data.get("Q",0))
            S1=float(data.get("S1",0))
            Z1 = float(data.get("Z1",0))
            b1 = float(data.get("b1",0))
            b2=float(data.get("b2",0))
            n=float(data.get("n",0))
            D_over_S_BC=float(data.get("D_over_S_BC",0))
            Contraction_coef=float(data.get("Contraction_coef",0))
            Ogee_crest_elv=float(data.get("Ogee_crest_elv",0))
            L_weir=float(data.get("L_weir",0))
            X_og=float(data.get("X_og",0))
            data2,status=inlet_initial_table(Q,S1,Z1,b1,b2,n,D_over_S_BC,Contraction_coef,Ogee_crest_elv,L_weir,X_og)
            data3={'data':data2,'status':status}
            return JsonResponse(data3)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@csrf_exempt
def inlet_diagram(request):
    if request.method =="POST":
        try:
            data = json.loads(request.body)
            ty= float(data.get("ty",0))
            l_total=float(data.get("l_total",0))
            rwx = float(data.get("rwx",0))
            inlet_alpha=float(data.get("inlet_alpha",0))
            R_wall=float(data.get("R_wall",0))
            R_center=float(data.get("R_center",0))
            b2=float(data.get("b2",0))
            b1=float(data.get("b1",0))
            X_og=float(data.get("X_og",0))
            Ogee_length=float(data.get("Ogee_length",0))
            R_ds=float(data.get("R_ds",0))
            X_upstream=float(data.get("X_upstream",0))
            inlet_alpha2=inlet_alpha/2
            data2,status=draw_inlet(ty,l_total,rwx,inlet_alpha2,R_wall,R_center)
            toe_curve=draw_toe_curve(Ogee_length,R_ds,inlet_alpha2)
            R_us=R_center+X_upstream
            US_curve=draw_US_curve(X_upstream,R_us,inlet_alpha2)
            center_curve=draw_center_curve(R_center,inlet_alpha2)
            data2['greenline']=[[l_total,b2/2],[l_total,-1*b2/2]]
            
            data2['vertical_black']=[[X_og,b1/2],[X_og,-1*b1/2]]
            
            data2['toe_curve_black']=toe_curve
            data2['US_curve_black']=US_curve
            data2['center_curve_red']=center_curve
            data2['left_curve_red']=[[0,R_center*math.tan(math.radians(inlet_alpha2))],[R_center,0]]
            data2['right_curve_red']=[[0,R_center*math.tan(math.radians(inlet_alpha2))*-1],[R_center,0]]
            data2['x_max']=((l_total // 10) + 2) * 10
            
            
            data3={'data':data2,'status':status}
            return JsonResponse(data3)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
@csrf_exempt
def transition_shape(request):
    if request.method =="POST":
        try:
            data = json.loads(request.body)
            Q=float(data.get("Q",0))
            S1=float(data.get("S1",0))
            Z2=float(data.get("Z2",0))
            b2=float(data.get("b2",0))
            n=float(data.get("n",0))
            C=float(data.get("C",0))
            b3=float(data.get("b3",0))
            yc3=float(data.get("yc3",0))
            y2=float(data.get("y2",0))
            y3=float(data.get("y3",0))
            choose_tunnel_type=data.get("choose_tunnel_type",None)
            
            if choose_tunnel_type =='circle':
                para=(Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type)
                data=transition_shape_circle(para)
            elif choose_tunnel_type =='horseshoe':
                yt1max=float(data.get("yt1max",0))
                yt2max=float(data.get("yt2max",0))
                y2max=float(data.get("y2max",0))
                B3=float(data.get("B3",0))
                t1max=float(data.get("t1max",0))
                a1max=float(data.get("a1max",0))
                a2max=float(data.get("a2max",0))
                p1max=float(data.get("p1max",0))
                p2max=float(data.get("p2max",0))
                para=(Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type,yt1max,yt2max,y2max,B3,t1max,a1max,a2max,p1max,p2max)
                
                data=transition_shape_horseshoe(para)
                
            
            
            data3={'data':data,'status':True}
            return JsonResponse(data3)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
@csrf_exempt
def transition_figure(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            B2 = float(data.get('B2', 0))
            Z2 = float(data.get('Z2', 0))
            Z3 = float(data.get('Z3', 0))
            B3 = float(data.get('B3', 0))
            stastart=float(data.get("stastart",0))
            ltotal=float(data.get("ltotal",0))
            l2=float(data.get("l2",0))
            beta2=float(data.get("beta2",0))
            beta1=float(data.get("beta1",0))
            yt2max=float(data.get('yt2max',0))
            choose_tunnel_type=data.get('choose_tunnel_type',None)
            result=transition_data(B2,Z2,Z3,B3,choose_tunnel_type,stastart,ltotal,l2,beta1,beta2,yt2max)
            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

@csrf_exempt
def water_level(request):
    if request.method=='POST':
        try:
            data=json.loads(request.body)
            choose_tunnel_type=data.get('choose_tunnel_type',None)
            Q=float(data.get("Q",0))
            lweir = float(data.get('lweir', 0))
            Ogee_crest_elv=float(data.get('Ogee_crest_elv',0))
            Ogee_height=float(data.get('Ogee_height',0))
            result=waterlevel_data(choose_tunnel_type,lweir,Q,Ogee_crest_elv,Ogee_height)
            data3={'data':result,'status':True}
            return JsonResponse(data3)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
from .figure import fig_9_26,fig_9_23,fig_9_27,fig_9_21_a,fig_9_21_b,fig_9_21_c,fig_9_21_d,fig_9_21_e1,fig_9_21_e2
def step1_cal(he, P, L, X, c_assump, n):
    q = c_assump * (he ** 1.5)  # 單寬流量
    va = q / (he + P)  # 堰前流速
    ha = (q ** 2) / (2 * 9.81 * (he + P) ** 2)  # 堰前動能水頭
    he_add_p = he + P  # 設計水頭 + 上游側堰高
    sn = (va * n / ( he_add_p ** (2 / 3))) ** 2  # 曼寧公式的斜度
    hf = L * sn  # 水力損失
    ha_01 = 0.1 * ha  # 動能水頭的10%
    head_loss = hf + ha_01  # 總水頭損失
    heff = he - head_loss  # 堰下水頭
    P_over_heff = P / heff  # 比值 P/ho
    hd_add_d = he + X  # ho 加上 X
    hd_add_d_over_heff = hd_add_d / heff  # 比值 (hd+d)/heff

    if hd_add_d_over_heff<1 or hd_add_d_over_heff > 2.08:
        return {'error':'out of range','parameter':'hd+d/heff'}
    hd_over_heff = fig_9_26(hd_add_d_over_heff)  # 查表數值
    
    hd = hd_over_heff * heff  # 堰下水深
    d = hd_add_d - hd  # 深度 d
    v = q / d  # 流速
    hv = (v ** 2) / (2 * 9.81)  # 流速水頭
    hd_minus_hv = hd - hv  # 堰下水深 - 流速水頭
    error=hd_minus_hv/hv
  
    # if P_over_heff<3.08 :
    #     return {'error':'out of range','parameter':'P/heff'}
  
    co_ip = fig_9_23(P_over_heff)
    cs_over_co=fig_9_27(hd_add_d_over_heff)
    cs=cs_over_co*co_ip/1.811
    q2=cs*he**1.5
    va2=q2/(P+he)
    ha_over_ho=ha/he
    k=fig_9_21_a(ha_over_ho)
    n2=fig_9_21_b(ha_over_ho)

    xc_over_ho=fig_9_21_c(ha_over_ho)
    xc=xc_over_ho*he
    yc_over_ho=fig_9_21_d(ha_over_ho)
    yc=yc_over_ho*he
    r1_over_ho=fig_9_21_e1(ha_over_ho)
    r1=r1_over_ho*he
    r2_over_ho=fig_9_21_e2(ha_over_ho)
    r2=r2_over_ho*he
    r1_minus_r2=r1-r2
    return {
        "he":he,                     #設計水頭
        "P1":P,                       #堰前深度
        "q": q,                      # 單寬流量
        "va": va,                    # 堰前流速
        "ha": ha,                    # 堰前動能水頭
        "he_add_p":he_add_p,         # 設計水頭 + 上游側堰高
        "sn": sn,                    # 曼寧公式的斜度
        "hf": hf,                    # 水力損失
        "ha_01": ha_01,              # 動能水頭的10%
        "head_loss": head_loss,      # 總水頭損失
        "heff": heff,                # 堰下有效水頭
        "P_over_heff": P_over_heff,      # 比值 P/ho
        "hd_add_d": hd_add_d,        # ho 加上 1.85
        "hd_add_d_over_heff": hd_add_d_over_heff,  # 比值 (hd+d)/heff
        "hd_over_heff":hd_over_heff,
        "hd": hd,                    # 堰下水深
        "d": d,                      # 深度 d
        "v": v,                      # 流速
        "hv": hv,                    # 流速水頭
        "hd_minus_hv": hd_minus_hv,   # 堰下水深 - 流速水頭
        "error":error,
        "co_ip":co_ip,
        "co_si":co_ip/1.811,
        "cs_over_co":cs_over_co,
        "cs":cs,
        "ogee_h":hd+d-heff,
        'ha_over_ho':ha_over_ho,
        'q2':q2,
        'va2':va2,
        'k':k,
        'n2':n2,
        'xc_over_ho':xc_over_ho,
        'Xc':xc,
        'yc_over_ho':yc_over_ho,
        'yc':yc,
        'r1_over_ho':r1_over_ho,
        'r1':r1,
        'r2_over_ho':r2_over_ho,
        'r2':r2,
        'r1_minus_r2':r1_minus_r2


    }
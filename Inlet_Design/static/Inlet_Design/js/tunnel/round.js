async function updateRoundQ(){
    const R = parseFloat(document.getElementById("R_round_tunnel").value);
    const Q=parseFloat(document.getElementById("Q_round_tunnel").value);
    const ac=document.getElementById('ac_round_value');
    const tc =document.getElementById('tc_round_value');
    const pc =document.getElementById('pc_round_value');
    const vc =document.getElementById('vc_round_value');
    const fr =document.getElementById('fr_round_value');
    const atotal = document.getElementById('atotal_round_value');
    const ymax=document.getElementById('ymax_round_value')
    const yc_v=document.getElementById('yc_round_value')
    const b_over_r=document.getElementById('b_over_r_round_value');
    const Q_inlet=document.getElementById('Q_inlet')
    
    if(!isNaN(R)&&!isNaN(Q)){
        b_over_r.textContent=R
        let yc= await findYForFr1_round(Q)
        let ac_=calculate_round_Ac(yc)
        let tc_=calculate_round_Tc(yc)
        let pc_=calculate_round_Pc(yc)
        let vc_=Q/ac_
        let fr_=vc_/(9.81*ac_/tc_)**0.5
        let atotal_=R**2*Math.PI
        let ymax_=R*2
        ac.textContent=ac_.toFixed(5)
        tc.textContent=tc_.toFixed(5)
        pc.textContent=pc_.toFixed(5)
        vc.textContent=vc_.toFixed(5)
        fr.textContent=(fr_).toFixed(3)
        ymax.textContent=(ymax_).toFixed(3)
        yc_v.textContent=(yc).toFixed(3)
        atotal.textContent=(atotal_).toFixed(3)
        atotal.style.fontSize = "25px";
        yc_v.style.fontSize = "25px";
        ymax.style.fontSize = "25px";
        ////////////更新進水口資料////////////////////////////////
        Q_inlet.textContent=(Q)
        
    }
}
async function findYForFr1_round(Q, yStart = 0.01, tolerance = 0.00001, maxIter = 10000000){
    let y = yStart;
    let iter = 0;
    let fr_ = 0;
    
    while (iter < maxIter) {
      let ac_ = calculate_round_Ac(y);
      let tc_ = calculate_round_Tc(y);
      
      if (ac_ === 0 || tc_ === 0) break; // 避免除以零
      
      let vc_ = Q / ac_;
      fr_ = vc_ / Math.sqrt(9.81 * ac_ / tc_);
      
      const diff = fr_ - 1;
      if (Math.abs(diff) < tolerance) {
        console.log(`迭代次數: ${iter}`);
        return y;
      }
      if (!diff) {
        console.log(`迭代次數: ${iter}`);
        return y;
      }
      if (diff<0){
        if (diff<-1 ){
            y = y-0.001;
        }else if(diff<-0.1){
            y = y-0.001;
        }else if(diff<-0.01){
            y = y-0.0001;
        }else if(diff<-0.001){
            y = y-0.00001;
        }else{
            console.log(`迭代次數: ${iter}`);
            return y;
        }
        }
      if (diff>10){
        // 根據差異調整 y 的方向與幅度
        y = y+0.5;  // 可微調 0.01 為更精準/更快收斂
      }else if(diff>1 ){
        y = y+0.01;
      }else if(diff>0.01 ){
        y = y+0.0001;
      }else if(diff>0.001 ){
        y = y+0.00001;
      }else{
        // 根據差異調整 y 的方向與幅度
        y = y+0.000001;  // 可微調 0.01 為更精準/更快收斂
      }
      iter++;

    }
    console.warn("未在最大迴圈內收斂到 fr_ = 1");
    return y;
}
function calculate_round_Ac(y){
    const R = parseFloat(document.getElementById("R_round_tunnel").value);
    if(y<=R){
        const angleRad=Math.acos((R-y)/R)
        const angleDeg=angleRad*(180/Math.PI)
        const A1=(angleDeg*2)/360*Math.PI
        const A2=Math.sin(angleRad)*Math.cos(angleRad)
        const A=R**2*(A1-A2)
        return A
    }else{
        const angleRad=Math.acos((y-R)/R)
        const angleDeg=angleRad*(180/Math.PI)
        const A1=(angleDeg*2)/360*Math.PI
        const A2=Math.sin(angleRad)*Math.cos(angleRad)
        const A=R**2*(Math.PI-(A1-A2))
        return A
    }
}
function calculate_round_Pc(y){
    const R = parseFloat(document.getElementById("R_round_tunnel").value);
    if (y <= R) {
      const angle = 2 * Math.acos((R - y) / R); // radians
      return angle * R;
    } else {
      const angle = 2 * Math.acos((y - R) / R); // radians
      return (2 * Math.PI - angle) * R;
    }
}

function calculate_round_Tc(y) {
    const R = parseFloat(document.getElementById("R_round_tunnel").value);
    const angleRad = (y <= R)
      ? Math.acos((R - y) / R)
      : Math.acos((y - R) / R);
    const T = 2 * R * Math.sin(angleRad);
    return T;
  }
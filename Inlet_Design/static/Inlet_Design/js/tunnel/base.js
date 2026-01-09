let choose_tunnel_type
let yc_for_transition
function choose_horseshoe(){
    console.log('選擇馬蹄型隧道')
    const div = document.getElementById('horseshoe');
    div.style.display = 'flex';  // 顯示
    const divtable = document.getElementById('calculation-table-main');
    divtable.style.display='flex'
    const divchoose =document.getElementById('choosing-btn')
    divchoose.style.display='none'
    choose_tunnel_type='horseshoe'
}
function choose_round(){
    console.log('選擇圓型隧道')
    const div = document.getElementById('round');
    div.style.display = 'flex';  // 顯示
    const divtable = document.getElementById('calculation-table-main');
    divtable.style.display='flex'
    const divchoose =document.getElementById('choosing-btn')
    divchoose.style.display='none'
    choose_tunnel_type='circle'
}
function updateR3() {
    const R = parseFloat(document.getElementById("R_tunnel").value);
    const B1=parseFloat(document.getElementById("beta1_tunnel").value);
    const B2=parseFloat(document.getElementById("beta2_tunnel").value);
    const R3_value = document.getElementById("R3_value");
    const t2max=document.getElementById("t2max_value");
    const yt1max=document.getElementById("yt1max_value");
    const t1max=document.getElementById("t1max_value");
    const p1max=document.getElementById("p1max_value");
    const a1max=document.getElementById('a1max_value');
    const yt2max=document.getElementById('yt2max_value')
    const p2max=document.getElementById('p2max_value');
    const a2max=document.getElementById('a2max_value');
    const y2max=document.getElementById('y2max_value');
    const b_over_r=document.getElementById('b_over_r_value');
    const Q=parseFloat(document.getElementById("Q_tunnel").value);
    if (!isNaN(R)) {
        R3_value.textContent = (R / 2).toFixed(2); // R3 = R/2，保留2位小數
        t2max.textContent=R
        b_over_r.textContent=R
    } else {
        R3_value.textContent = "--"; 
        t2max.textContent= "--"; 
        b_over_r.textContent="--";
    }
    if (!isNaN(B1)&&!isNaN(R)) {
        yt1max.textContent = (R*(1-Math.cos((B1/2)*(Math.PI/180)))).toFixed(5); 
        t1max.textContent = (2*R*(Math.sin((B1/2)*(Math.PI/180)))).toFixed(5); 
        p1max.textContent = (B1*Math.PI*R/180).toFixed(5); 
        a1max.textContent = ((R**2)*(Math.PI*B1/360-Math.sin(B1/2*(Math.PI/180))*Math.cos(B1/2*(Math.PI/180)))).toFixed(5); 
    } else {
        yt1max.textContent = "--"; 
        t1max.textContent ="--"
        p1max.textContent ="--"
        a1max.textContent ="--"
    }
    if (!isNaN(B1)&&!isNaN(R)&&!isNaN(B2)) {
        const yt2max_=((R*(Math.sin((B1/2)*(Math.PI/180))))+R/2)/Math.tan((90-B2)*(Math.PI/180))+(R*(1-Math.cos((B1/2)*(Math.PI/180)))); 
        yt2max.textContent =yt2max_.toFixed(5); 
        p2max.textContent =(2*Math.PI*B2*R/180+B1*Math.PI*R/180).toFixed(5)
        const t1_=(2*R*(Math.sin((B1/2)*(Math.PI/180))))
        const t2_=R
        const yt1_=R*(1-Math.cos((B1/2)*(Math.PI/180)))
        const y2max_=yt2max_-yt1_
        y2max.textContent =y2max_.toFixed(5);
        const a1max_=(R**2)*(Math.PI*B1/360-Math.sin(B1/2*(Math.PI/180))*Math.cos(B1/2*(Math.PI/180))); 
        a2max.textContent =(((B2/360)*Math.PI*R**2-R**2*Math.sin((B2/2)*(Math.PI/180))*Math.cos((B2/2)*(Math.PI/180)))*2+(t1_+t2_)*y2max_/2+a1max_).toFixed(5)
        if (!isNaN(Q)){
            updateQ()
        }
    } else {
        yt2max.textContent ="--"
        p2max.textContent ="--"
        a2max.textContent ="--"
        y2max.textContent ="--"
    }
}
function updateB1(){
    const R = parseFloat(document.getElementById("R_tunnel").value);
    const B2=parseFloat(document.getElementById("beta2_tunnel").value);
    const B1=parseFloat(document.getElementById("beta1_tunnel").value);
    const yt1max=document.getElementById("yt1max_value");
    const t1max=document.getElementById("t1max_value");
    const p1max=document.getElementById("p1max_value");
    const a1max=document.getElementById('a1max_value');
    const yt2max=document.getElementById('yt2max_value');
    const p2max=document.getElementById('p2max_value');
    const y2max=document.getElementById('y2max_value');
    const a2max=document.getElementById('a2max_value');
    if (!isNaN(B1)&&!isNaN(R)) {
        const yt1max_=(R*(1-Math.cos((B1/2)*(Math.PI/180)))).toFixed(5);
        const t1max_=(2*R*(Math.sin((B1/2)*(Math.PI/180)))).toFixed(5);
        const p1max_=(B1*Math.PI*R/180).toFixed(5);
        const a1max_=((R**2)*(Math.PI*B1/360-Math.sin(B1/2*(Math.PI/180))*Math.cos(B1/2*(Math.PI/180)))).toFixed(5); 
        yt1max.textContent = yt1max_; 
        t1max.textContent = t1max_; 
        p1max.textContent = p1max_;
        a1max.textContent = a1max_;
        
    } else {
        yt1max.textContent = "--"; 
        t1max.textContent ="--"
        p1max.textContent ="--"
        a1max.textContent ="--"
    }
    if (!isNaN(B1)&&!isNaN(R)&&!isNaN(B2)) {
        const yt2max_=((R*(Math.sin((B1/2)*(Math.PI/180))))+R/2)/Math.tan((90-B2)*(Math.PI/180))+(R*(1-Math.cos((B1/2)*(Math.PI/180)))); 
        yt2max.textContent =yt2max_.toFixed(5); 
        p2max.textContent =(2*Math.PI*B2*R/180+B1*Math.PI*R/180).toFixed(5)
        const t1_=(2*R*(Math.sin((B1/2)*(Math.PI/180))))
        const t2_=R
        const yt1_=R*(1-Math.cos((B1/2)*(Math.PI/180)))
        const y2max_=yt2max_-yt1_
        y2max.textContent =y2max_.toFixed(5);
        const a1max_=(R**2)*(Math.PI*B1/360-Math.sin(B1/2*(Math.PI/180))*Math.cos(B1/2*(Math.PI/180))); 
        a2max.textContent =(((B2/360)*Math.PI*R**2-R**2*Math.sin((B2/2)*(Math.PI/180))*Math.cos((B2/2)*(Math.PI/180)))*2+(t1_+t2_)*y2max_/2+a1max_).toFixed(5)
    } else {
        yt2max.textContent ="--"
        p2max.textContent ="--"
        a2max.textContent ="--"
        y2max.textContent ="--"
    }
}
function updateB2(){
    const R = parseFloat(document.getElementById("R_tunnel").value);
    const B2=parseFloat(document.getElementById("beta2_tunnel").value);
    const B1=parseFloat(document.getElementById("beta1_tunnel").value);
    const ninety_minus_beta2 = document.getElementById("ninety_minus_beta2_value");
    const yt2max=document.getElementById('yt2max_value');
    const p2max=document.getElementById('p2max_value');
    const a2max=document.getElementById('a2max_value');
    const y2max=document.getElementById('y2max_value')
    if (!isNaN(B2)) {
        ninety_minus_beta2.textContent = (90-B2).toFixed(5); 
    } else {
        ninety_minus_beta2.textContent = "--"; // 如果輸入無效，顯示0
    }
    if (!isNaN(B1)&&!isNaN(R)&&!isNaN(B2)) {
        const yt2max_=((R*(Math.sin((B1/2)*(Math.PI/180))))+R/2)/Math.tan((90-B2)*(Math.PI/180))+(R*(1-Math.cos((B1/2)*(Math.PI/180)))); 
        yt2max.textContent =yt2max_.toFixed(5); 
        p2max.textContent =(2*Math.PI*B2*R/180+B1*Math.PI*R/180).toFixed(5)
        const t1_=(2*R*(Math.sin((B1/2)*(Math.PI/180))))
        const t2_=R
        const yt1_=R*(1-Math.cos((B1/2)*(Math.PI/180)))
        const y2max_=yt2max_-yt1_
        y2max.textContent =y2max_.toFixed(5);
        const a1max_=(R**2)*(Math.PI*B1/360-Math.sin(B1/2*(Math.PI/180))*Math.cos(B1/2*(Math.PI/180))); 
        a2max.textContent =(((B2/360)*Math.PI*R**2-R**2*Math.sin((B2/2)*(Math.PI/180))*Math.cos((B2/2)*(Math.PI/180)))*2+(t1_+t2_)*y2max_/2+a1max_).toFixed(5)
    } else {
        yt2max.textContent ="--"
        p2max.textContent ="--"
        a2max.textContent ="--"
        y2max.textContent ="--"
    }
}
async function updateQ(){
    const R = parseFloat(document.getElementById("R_tunnel").value);
    const B2=parseFloat(document.getElementById("beta2_tunnel").value);
    const B1=parseFloat(document.getElementById("beta1_tunnel").value);
    const Q=parseFloat(document.getElementById("Q_tunnel").value);
    const a2max=parseFloat(document.getElementById("a2max_value").textContent);
    const yt2max=parseFloat(document.getElementById("yt2max_value").textContent);
    const yc=document.getElementById('y_value');
    const ac=document.getElementById('ac_value');
    const tc =document.getElementById('tc_value');
    const pc =document.getElementById('pc_value');
    const vc =document.getElementById('vc_value');
    const fr =document.getElementById('fr_value');
    const atotal = document.getElementById('atotal_value');
    const ymax=document.getElementById('ymax_value')
    const yc_v=document.getElementById('yc_value')
    const Q_inlet=document.getElementById('Q_inlet')
    if (!isNaN(B1)&&!isNaN(R)&&!isNaN(B2)&&!isNaN(Q)) {
        const y=await findYForFr1(Q)
        let ac_=calculate_Ac(y)
        let  tc_=calculate_Tc(y)
        let pc_=calculate_Pc(y)
        let vc_=Q/ac_
        let fr_=vc_/(9.81*ac_/tc_)**0.5
        let atotal_=Math.PI*(((R/2)**2)/2)+a2max
        let ymax_=yt2max+R/2
        ac.textContent=ac_.toFixed(5)
        tc.textContent=tc_.toFixed(5)
        pc.textContent=pc_.toFixed(5)
        vc.textContent=vc_.toFixed(5)
        fr.textContent=(fr_).toFixed(3)
        yc.textContent=(y).toFixed(3)
        atotal.textContent=(atotal_).toFixed(2)
        ymax.textContent=(ymax_).toFixed(2)
        yc_v.textContent=(y).toFixed(3)
        atotal.style.fontSize = "25px";
        yc_v.style.fontSize = "25px";
        ymax.style.fontSize = "25px";
        ////////////更新進水口資料////////////////////////////////
        Q_inlet.textContent=(Q)
    }
}
window.onload = function() {
    updateB2();
};
function calculate_Ac(y){
    const R = parseFloat(document.getElementById("R_tunnel").value);
    const B2=parseFloat(document.getElementById("beta2_tunnel").value);
    const B1=parseFloat(document.getElementById("beta1_tunnel").value);
    const ninety_minus_beta2=parseFloat(document.getElementById("ninety_minus_beta2_value").textContent);
    const yt1max=parseFloat(document.getElementById("yt1max_value").textContent);
    const t1max=parseFloat(document.getElementById("t1max_value").textContent);
    const p1max=parseFloat(document.getElementById("p1max_value").textContent);
    const a1max=parseFloat(document.getElementById("a1max_value").textContent);
    const yt2max=parseFloat(document.getElementById("yt2max_value").textContent);
    const t2max=parseFloat(document.getElementById("t2max_value").textContent);
    const p2max=parseFloat(document.getElementById("p2max_value").textContent);
    const a2max=parseFloat(document.getElementById("a2max_value").textContent);
    const y2max=parseFloat(document.getElementById("y2max_value").textContent);
    let ac= null
    if (y<=yt1max){
        const angleRad = Math.acos((R - y) / R); // 角度 (radian)
        const sectorArea = R * R * angleRad; // 扇形面積
        const triangleArea = R * R * Math.sin(angleRad) * Math.cos(angleRad); // 三角形面積
        ac = sectorArea - triangleArea;
        return ac;
    }else if( yt1max<y && y<=yt2max){
        const deltaY = y2max - (y - yt1max);
        const cosValue = deltaY / R;
        const angleRad = Math.acos(cosValue);        // 弧度
        const angleDeg = angleRad * (180 / Math.PI); // 角度
      
        const angle1 = angleDeg - ninety_minus_beta2;
        const angle1Rad = angle1 * (Math.PI / 180);
      
        const A1 = (angle1 / 360) * Math.PI * Math.pow(R, 2);
        const A2 = Math.sin(angle1Rad / 2) * Math.cos(angle1Rad / 2) * Math.pow(R, 2);
        const sectorMinusTriangle = (A1 - A2) * 2;
      
        const tanAngle = Math.tan(angleRad);
        const A3 = (((deltaY * tanAngle) - R/2) * 2 + t1max) * ((y - yt1max) / 2);
      
        ac = sectorMinusTriangle + A3 + a1max;
        return ac;
    }else{
        const ratio = (y - yt2max) / (R / 2);
        const acosDegrees = Math.acos(ratio) * (180 / Math.PI);  // 弧度轉角度
        const acosRadians = Math.acos(ratio);                    // 原本是弧度
        // 第一部分
        const part1 = (Math.pow(R, 2) / 4) *Math.cos(acosRadians) *Math.sin(acosRadians);

        // 第二部分
        const part2 = ((90 - acosDegrees) / 360) *Math.PI *(Math.pow(R, 2) / 4) *2;

        // 總和
        ac = part1 + part2 + a2max;
        return ac
    }


}
function calculate_Tc(y){
    const R = parseFloat(document.getElementById("R_tunnel").value);
    const yt1max=parseFloat(document.getElementById("yt1max_value").textContent);
    const yt2max=parseFloat(document.getElementById("yt2max_value").textContent);
    const y2max=parseFloat(document.getElementById("y2max_value").textContent);
    let tc=null
    if (y<=yt1max){
        const ratio = (R-y) / R;
        const acosRadians = Math.acos(ratio);// 弧度
        tc=2*R*Math.sin(acosRadians)
        return tc
    }else if( yt1max<y && y<=yt2max){
        const deltaY = y2max - (y - yt1max);
        const ratio = (y2max-(y-yt1max))/R
        const acosRadians = Math.acos(ratio);// 弧度
        const tanRadians= Math.tan(acosRadians)
        tc=(deltaY*tanRadians-R/2)*2
        return tc
    }else{
        const ratio = (y-yt2max)/(R/2)
        const acosRadians = Math.acos(ratio);// 弧度
        tc=R*Math.sin(acosRadians)
        return tc
    }
}
function calculate_Pc(y){
    const R = parseFloat(document.getElementById("R_tunnel").value);
    const B2=parseFloat(document.getElementById("beta2_tunnel").value);
    const B1=parseFloat(document.getElementById("beta1_tunnel").value);
    const ninety_minus_beta2=parseFloat(document.getElementById("ninety_minus_beta2_value").textContent);
    const yt1max=parseFloat(document.getElementById("yt1max_value").textContent);
    const p1max=parseFloat(document.getElementById("p1max_value").textContent);
    const yt2max=parseFloat(document.getElementById("yt2max_value").textContent);
    const p2max=parseFloat(document.getElementById("p2max_value").textContent);
    const y2max=parseFloat(document.getElementById("y2max_value").textContent);
    let pc=null
    if (y<=yt1max){
        const ratio=(R-y)/R
        const acosDegrees = Math.acos(ratio)*( 180/ Math.PI);// 角度
        pc=2*acosDegrees*R*Math.PI/180
        return pc
    }else if( yt1max<y && y<=yt2max){
        const ratio=(y2max-(y-yt1max))/R
        const acosDegrees = Math.acos(ratio)*( 180/ Math.PI);// 角度
        const Angle = acosDegrees-ninety_minus_beta2
        pc=Angle*Math.PI*2*R/180+p1max
        return pc
    }else{
        const ratio=(y-yt2max)/(R/2)
        const acosDegrees = Math.acos(ratio)*( 180/ Math.PI);// 角度
        pc=(90-acosDegrees)*Math.PI*R/180+p2max
        return pc
    }
}
async function findYForFr1(Q, yStart = 0.01, tolerance = 0.0004, maxIter = 10000000) {
    let y = yStart;
    let iter = 0;
    let fr_ = 0;
    
    while (iter < maxIter) {
      let ac_ = calculate_Ac(y);
      let tc_ = calculate_Tc(y);
      
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

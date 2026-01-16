function updateLmin(){
    const Q_inlet=document.getElementById('Q_inlet').innerText.trim()
    const He_inlet=document.getElementById('He_inlet').innerText.trim()
    const Cd_inlet=document.getElementById('Cd_inlet').innerText.trim()
    const isNumber = !isNaN(Q_inlet) && Q_inlet !== '' && !isNaN(He_inlet) && He_inlet !== '' && !isNaN(Cd_inlet) && Cd_inlet !== '';
    const L_min=document.getElementById('L_min')
    const L_weir=document.getElementById('L_weir')
    
    if (isNumber){
        L_min.textContent=(Q_inlet/(Cd_inlet*He_inlet**1.5)).toFixed(2)
        L_weir.textContent=(Q_inlet/(Cd_inlet*He_inlet**1.5)).toFixed(0)
       
    }

}
function updateAlpha() {
    const L_weir = document.getElementById('L_weir').innerText.trim();
    const inlet_alpha_el = document.getElementById('inlet_alpha');
    const inlet_alpha_half_el = document.getElementById('inlet_alpha_half');
    const isNumber = !isNaN(L_weir) && L_weir !== '';
  
    const R_center = parseFloat(document.getElementById('R_center').value);
    const R_ds_el = document.getElementById('R_ds');
    const Ogee_length = parseFloat(document.getElementById('Ogee_length').innerText.trim());
    const y_og = parseFloat(document.getElementById("y_og").innerText.trim());
    const X_og_el = document.getElementById('X_og');
    const B1 = document.getElementById('B1_inlet');
    
  
    if (isNumber && !isNaN(R_center) && !isNaN(Ogee_length) && !isNaN(y_og)) {
      const inlet_alpha_val = (180 / (Math.PI * R_center)) * parseFloat(L_weir);
      inlet_alpha_el.textContent = inlet_alpha_val.toFixed(3);
  
      inlet_alpha_half_el.textContent = (inlet_alpha_val / 2).toFixed(3);
  
      const R_ds_value = R_center - Ogee_length;
      R_ds_el.textContent = R_ds_value.toFixed(2);
  
      const angle_rad = (inlet_alpha_val / 2) * (Math.PI / 180); // 轉成弧度
      const X_og_value = R_ds_value - R_ds_value * Math.cos(angle_rad) + y_og;
      X_og_el.textContent = X_og_value.toFixed(0);
      const B1_value = (R_center-X_og_value.toFixed(0))*Math.tan((inlet_alpha_val / 2)* (Math.PI / 180))*2
      B1.textContent=B1_value.toFixed(2);

    }
  }
function updateDsg_Water(){
    
    const Dsg_Water = document.getElementById('Dsg_Water').value;
    const isNumber = !isNaN(Dsg_Water) && Dsg_Water !== '';
    const He_inlet= document.getElementById('He_inlet').innerText.trim()
    const Ogee_crest_elv = document.getElementById('Ogee_crest_elv')
    const Toe_Elevation = document.getElementById('Toe_Elevation')
    const Ogee_height=document.getElementById('Ogee_height').innerText.trim();
    if (isNumber) {
        Ogee_crest_elv.textContent=(Dsg_Water-He_inlet).toFixed(2)
        Toe_Elevation.textContent=(Dsg_Water-He_inlet-Ogee_height).toFixed(2)

    }

}
function ceilToMultiple(value, multiple) {
    return Math.ceil(value / multiple) * multiple;
  }
var inlet_draw_parameter
function update_selection(){
    const selectedValue = document.getElementById("selection").value;
    console.log(`選了 ${selectedValue} 號`);
    const X_og = document.getElementById('X_og').innerText.trim()
    const y_og = document.getElementById('y_og').innerText.trim()
    const R_ds = document.getElementById('R_ds').innerText.trim()
    const R_center = document.getElementById('R_center').value
    const R_wall = document.getElementById('R_wall').value
    const inlet_alpha=document.getElementById('inlet_alpha').innerText.trim()
    const Z1=document.getElementById('Toe_Elevation').innerText.trim()
    const selection_xog=document.getElementById('selection_xog')
    const selection_yog=document.getElementById('selection_yog')
    const selection_Rds=document.getElementById('selection_Rds')
    const selection_Rcenter=document.getElementById('selection_Rcenter')
    const selection_Rwall=document.getElementById('selection_Rwall')
    const selection_alpha=document.getElementById('selection_alpha')
    const selection_b1=document.getElementById('selection_b1')
    const selection_b2=document.getElementById('selection_b2')
    const selection_Z1=document.getElementById('selection_Z1')
    const selection_Z2=document.getElementById('selection_Z2')
    const selection_y1=document.getElementById('selection_y1')
    const selection_y2=document.getElementById('selection_y2')
    const selection_S1=document.getElementById('selection_S1')
    const selection_L1=document.getElementById('selection_L1')
    const selection_Ltotal=document.getElementById('selection_Ltotal')
    const selection_Lr=document.getElementById('selection_Lr')
    const y2_transition=document.getElementById('y2_transition')
    const y2_transition_h=document.getElementById('y2_transition_h')
    const Z2_transition=document.getElementById('Z2_transition')
    const Z2_transition_h=document.getElementById('Z2_transition_h')
    const B1_transition=document.getElementById('B1_transition');
    const B1_transition_h=document.getElementById('B1_transition_h');
    selection_xog.textContent=X_og
    selection_yog.textContent=y_og
    selection_Rds.textContent=R_ds
    selection_Rcenter.textContent=R_center
    selection_Rwall.textContent=R_wall
    selection_alpha.textContent=inlet_alpha
    selection_Z1.textContent=Z1
    if (inlet_result === undefined) {
      alert("請填完所有輸入值");
    return;
  }
    const result = inlet_result.find(item => item.No === parseInt(selectedValue));
    selection_y1.textContent=(result.y1).toFixed(2)
    selection_y2.textContent=(result.y2).toFixed(2)
    y2_transition.textContent=(result.y2).toFixed(2)
    y2_transition_h.textContent=(result.y2).toFixed(2)
    
    
    selection_S1.textContent=(result.S1 * 100).toFixed(0) + '%';
    selection_b1.textContent=(result.b1).toFixed(2)
    selection_b2.textContent=(result.b2).toFixed(2)
    selection_L1.textContent=ceilToMultiple(result.L, 5)
    const l_total=ceilToMultiple(result.L, 5)+parseFloat(X_og)
    selection_Ltotal.textContent=l_total
    selection_Z2.textContent=(result.Z1-ceilToMultiple(result.L, 5)*result.S1).toFixed(2)
    Z2_transition.textContent=(result.Z1-ceilToMultiple(result.L, 5)*result.S1).toFixed(2)
    Z2_transition_h.textContent=(result.Z1-ceilToMultiple(result.L, 5)*result.S1).toFixed(2)
    /////FOR transition
    B1_transition.textContent=result.b2.toFixed(2);
    B1_transition_h.textContent=result.b2.toFixed(2);
    ////too many parameter for Lr!!!
    const x=result.b2/2*Math.tan((90-inlet_alpha/2)* (Math.PI / 180))
    const tx=Math.abs(x - (parseFloat(R_center) - l_total));
    const ty=result.b2/2
    const x_=parseFloat(R_wall)/Math.tan((180-inlet_alpha/2)/2* (Math.PI / 180))
    const rwx=l_total-tx+x_
    selection_Lr.textContent=(l_total-rwx).toFixed(2)
    const b2=result.b2
    const b1=result.b1
    const Ogee_length=parseFloat(document.getElementById('Ogee_length').innerText.trim())
    const X_upstream=parseFloat(document.getElementById('Xc').innerText.trim())
    inlet_draw_parameter={ty,l_total,rwx,inlet_alpha,R_wall,R_center,b2,b1,X_og,Ogee_length,R_ds,X_upstream}
    //////////判斷selection
    const user_selection=document.getElementById("user_selection")
    if ((l_total-rwx)<0){
      user_selection.textContent="Not applicable"
      user_selection.style.color = "red";
      selection_Lr.style.color = "red";
    }else if( (l_total-rwx)>result.b2){
      user_selection.innerHTML = `
      <span style="color: #FF9900;">Not Recommanded</span><br>
      This causes a sudden contraction, which can generate a larger crosswave. Such behavior can disrupt flow stability; need to consider 2D or 3D numerical modelling.
    `;
      selection_b2.style.color = "red";
      selection_Lr.style.color = "red";
      user_selection.style.color = "red";
      
    }else{
      user_selection.textContent='ok'
      user_selection.style.color = "green";
      selection_Lr.style.color = "green";
      selection_b2.style.color = "green";
    }
    //////改動step 1
    const condition_R_center=document.getElementById('condition_R_center')
    const checked_R_center=document.getElementById('checked_R_center')
    const condition_R_wall=document.getElementById('condition_R_wall')
    const checked_R_wall=document.getElementById('checked_R_wall')
    const L_weir=parseFloat(document.getElementById('L_weir').textContent)
    let max = Math.max(L_weir, l_total);
    let min = Math.min(L_weir, l_total);
    condition_R_center.textContent=`${min} ≤ R ≤ ${max}`
    let length=tx*Math.tan((180-inlet_alpha/2)/2* (Math.PI / 180))
    condition_R_wall.textContent=` R < ${parseInt(length)}`
    if((R_center>max) || (R_center<min)){
      checked_R_center.textContent="CHANGE!!"
      checked_R_center.style.color = "red";
    }else{
      checked_R_center.textContent="OK"
      checked_R_center.style.color = "black";
    }
    if((R_wall>length) ){
      checked_R_wall.textContent="CHANGE!!"
      checked_R_wall.style.color = "red";
    }else{
      checked_R_wall.textContent="OK"
      checked_R_wall.style.color = "black";
    }
    
}
let inlet_result
async function inlet_table(){
    console.log('計算進水口漸變段')
    const Q=parseFloat(document.getElementById("Q_inlet").textContent);
    const S1=0.2;
    const Z1=parseFloat(document.getElementById("Toe_Elevation").textContent);
    const b1=parseFloat(document.getElementById("B1_inlet").textContent);
    const b2=parseFloat(document.getElementById("B2_trial").value);
    const n=parseFloat(document.getElementById("n_Manning").value);
    const D_over_S_BC=parseFloat(document.getElementById("D_over_S_BC").value);
    const Contraction_coef=parseFloat(document.getElementById("Contraction_coef").value);
    const Ogee_crest_elv=parseFloat(document.getElementById("Ogee_crest_elv").textContent);
    const L_weir=parseFloat(document.getElementById("L_weir").textContent);
    const X_og=parseFloat(document.getElementById("X_og").textContent);
    const check={Q,S1,Z1,b1,b2,n,D_over_S_BC,Contraction_coef,Ogee_crest_elv,L_weir,X_og}
    for (const [key, value] of Object.entries(check)) {
        if (value === undefined || isNaN(value)) {
            console.log(key, value)
            alert("請填完所有輸入值");
          return;
        } 
    }
    const response_initial = await fetch(window.djangoUrls.inlet_transition_initial_table, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", // 確保這是 Django 中由模板引擎插入的
        },
        body: JSON.stringify(check),
    });
    if (!response_initial.ok) {
        console.error("API 請求失敗", response_initial.status);
        return;
    }
    const data_initial = await response_initial.json();
    const tableBody_initial = document.querySelector("#calculation-inlet-initial-table tbody");
    if (tableBody_initial) {
        tableBody_initial.innerHTML = ""; // 清空所有 <tr>
      }
    const table_initial=data_initial.data
    
    table_initial.forEach(row => {
        const tr_initial = document.createElement("tr");
        tr_initial.innerHTML = `
        <td>${row.Q}</td>
        <td>${row.Z1.toFixed(2)}</td>
        <td>${row.Z2.toFixed(2)}</td>
        <td>${row.deltaZ.toFixed(1)}</td>
        <td>${row.b0.toFixed(2)}</td> <!-- from b1 -->
        <td>${row.b1.toFixed(1)}</td> <!-- from b2 -->
        <td>${row.L.toFixed(2)}</td>
        <td>${row.n.toFixed(3)}</td>
        <td>${row.y0.toFixed(2)}</td> <!-- from y1 -->
        <td>${row.yc0.toFixed(2)}</td> <!-- from yc1 -->
        <td>${row.A0.toFixed(2)}</td> <!-- from A1 -->
        <td>${row.P0.toFixed(2)}</td> <!-- from P1 -->
        <td>${row.R0.toFixed(2)}</td> <!-- from R1 -->
        <td>${row.V0.toFixed(2)}</td> <!-- from V1 -->
        <td>${row.Sf0.toFixed(4)}</td> <!-- from Sf1 -->
        <td>${row.speeding_head0.toFixed(2)}</td> <!-- from speeding_head1 -->
        <td>${row.E0.toFixed(2)}</td> <!-- from E1 -->
        <td style="background-color:#BF8F00">${row.y1.toFixed(2)}</td> <!-- from y2 -->
        <td>${row.yc1.toFixed(2)}</td> <!-- from yc2 -->
        <td>${row.A1.toFixed(2)}</td> <!-- from A2 -->
        <td>${row.P.toFixed(2)}</td>  <!-- from P2 -->
        <td>${row.R1.toFixed(2)}</td> <!-- from R2 -->
        <td>${row.V1.toFixed(2)}</td> <!-- from V2 -->
        <td>${row.Sf1.toFixed(4)}</td> <!-- from Sf2 -->
        <td>${row.speeding_head1.toFixed(3)}</td> <!-- from speeding_head2 -->
        <td>${row.E1.toFixed(2)}</td> <!-- from E2 -->
        <td>${row.hf.toFixed(3)}</td>
        <td>${row.hce.toFixed(3)}</td>
        <td>${row.he.toFixed(3)}</td>
        <td>${row.E.toFixed(2)}</td>
        <td>${row.control.toFixed(3)}</td>
        <td>${row.FR1.toFixed(2)}</td>
        <td>${row.FR2.toFixed(2)}</td>
        
        `;
            tableBody_initial.appendChild(tr_initial);
        });
    const response = await fetch(window.djangoUrls.inlet_transition_table, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", // 確保這是 Django 中由模板引擎插入的
        },
        body: JSON.stringify(check),
    });
    if (!response.ok) {
        console.error("API 請求失敗", response.status);
        return;
    }
    const data = await response.json();
    const tableBody = document.querySelector("#calculation-inlet-table tbody");
    if (tableBody) {
        tableBody.innerHTML = ""; // 清空所有 <tr>
      }
    
    const table=data.data
    inlet_result=table
    table.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${row.No}</td>
            <td>${row.Q}</td>
            <td style="background-color: #FFFF00;color:#FF0000">${(row.S1*100).toFixed(0)}%</td>
            <td style="background-color: #808080;color:#FFC000">${row.Z1.toFixed(2)}</td>
            <td style="background-color: #808080;color:#FFC000">${row.Z2.toFixed(2)}</td>
            <td>${row.deltaZ.toFixed(1)}</td>
            <td style="background-color:#F8CBAD;color:#FF0000">${row.b1.toFixed(2)}</td>
            <td style="background-color:#F8CBAD;color:#FF0000">${row.b2.toFixed(1)}</td>
            <td style="background-color:#F2F2F2;color:#00B050">${row.L.toFixed(2)}</td>
            <td>${row.n.toFixed(3)}</td>
            <td style="${row.No === 1 ? 'background-color:#BF8F00' : ''}">${row.y1.toFixed(2)}</td>
            <td>${row.yc1.toFixed(2)}</td>
            <td>${row.A1.toFixed(2)}</td>
            <td>${row.P1.toFixed(2)}</td>
            <td>${row.R1.toFixed(2)}</td>
            <td>${row.V1.toFixed(2)}</td>
            <td>${row.Sf1.toFixed(4)}</td>
            <td>${row.speeding_head1.toFixed(2)}</td>
            <td>${row.E1.toFixed(2)}</td>
            <td>${row.y2.toFixed(2)}</td>
            <td>${row.yc2.toFixed(2)}</td>
            <td>${row.A2.toFixed(2)}</td>
            <td>${row.P2.toFixed(2)}</td>
            <td>${row.R2.toFixed(2)}</td>
            <td>${row.V2.toFixed(2)}</td>
            <td>${row.Sf2.toFixed(4)}</td>
            <td>${row.speeding_head2.toFixed(3)}</td>
            <td>${row.E2.toFixed(2)}</td>
            <td>${row.hf.toFixed(3)}</td>
            <td>${row.hce.toFixed(3)}</td>
            <td>${row.he.toFixed(3)}</td>
            <td>${row.E.toFixed(2)}</td>
            <td>${row.control.toFixed(3)}</td>
            <td>${row.FR1.toFixed(2)}</td>
            <td>${row.FR2.toFixed(2)}</td>
        `;
            tableBody.appendChild(tr);
        });
    if (all_step<=3){
        all_step=3
    }

}
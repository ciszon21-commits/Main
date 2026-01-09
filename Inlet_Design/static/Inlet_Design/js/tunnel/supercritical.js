async function supercritical_cal(){
    console.log('計算超臨界流')
    const R = parseFloat(document.getElementById("R_tunnel").value);
    const Q_tunnel=parseFloat(document.getElementById("Q_tunnel").value);
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
    const n_tunnel=parseFloat(document.getElementById("n_tunnel").value);
    const Z_tunnel=parseFloat(document.getElementById("Z_tunnel").value);
    const S_tunnel=parseFloat(document.getElementById("S_tunnel").value);
    const Critical_depth=parseFloat(document.getElementById("Critical_depth").value)
    const yc_value=parseFloat(document.getElementById("yc_value").textContent)
    const Tunnel_length=parseFloat(document.getElementById("Tunnel_length").value)
    const Interval=parseFloat(document.getElementById("Interval").value)
    const Contraction=parseFloat(document.getElementById("Contraction").value)
    const Exspansion=parseFloat(document.getElementById("Exspansion").value)
    const jsondata = {R,Q_tunnel,B2,B1,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n_tunnel,Z_tunnel,S_tunnel,Critical_depth,yc_value,Tunnel_length,Interval,Contraction};
    const check={R,Q_tunnel,B2,B1,n_tunnel,Z_tunnel,S_tunnel,Critical_depth,Tunnel_length,Interval,Exspansion,Contraction}
    for (const [key, value] of Object.entries(check)) {
        if (value === undefined||isNaN(value)) {
            alert("請填完所有輸入值");
          return;
        } 
      }

    const response = await fetch(window.djangoUrls.horseshoe, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", 
        },
        body: JSON.stringify(jsondata),
    });
    
    if (!response.ok) {
        console.error("API 請求失敗", response.status);
        return;
    }
    
    const data = await response.json(); // <--- 解析 JSON 回傳資料
    
    const tableBody = document.querySelector("#calculation-table tbody");
    if (tableBody) {
        tableBody.innerHTML = ""; // 清空所有 <tr>
      }
    const tr = document.createElement("tr");
    tr.style.backgroundColor = "#FFC000";
    
    tr.innerHTML = `
        <td>${data.No}</td>
        <td>${data.sta_output}</td>
        <td>${data.Q_output}</td>
        <td>${data.b_output.toFixed(1)}</td>
        <td>${data.L_output}</td>
        <td>${data.n_output}</td>
        <td>${data.Z_output.toFixed(3)}</td>
        <td>${data.S_output}</td>
        <td>${data.yc_output}</td>
        <td>${data.A_output.toFixed(3)}</td>
        <td>${data.T_output.toFixed(3)}</td>
        <td>${data.P_output.toFixed(3)}</td>
        <td>${data.R_output.toFixed(3)}</td>
        <td>${data.V_output.toFixed(3)}</td>
        <td>${data.Sf_output.toFixed(3)}</td>
        <td>${data.speed_head_output.toFixed(3)}</td>
        <td>${data.hf_output}</td>
        <td>${data.hce_output}</td>
        <td>${data.he_output.toFixed(3)}</td>
        <td>${data.E_output.toFixed(3)}</td>
        <td></td>
        <td>${data.Control_output}</td>
        <td>${data.y_output.toFixed(3)}</td>
        <td>${data.Fr_output.toFixed(3)}</td>
        <td>${data.Water_level_output.toFixed(3)}</td>
        <td>${data.Full_output.toFixed(2)}</td>
    `;
    yc_for_transition=data.y_output
    tableBody.appendChild(tr);
    if (data.Fr_output<=1){
        alert(`起始值Fr為${data.Fr_output}，非超臨界流況，請重新輸入數據計算`)
        return
    }
    /////////////////////////////以上是table第一行//////////////////////////////////////////////////
    const response_super = await fetch(window.djangoUrls.horseshoe_supercritical_table, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", 
        },
        body: JSON.stringify(jsondata),
    });
    
    if (!response.ok) {
        console.error("API 請求失敗", response.status);
        return;
    }
    
    const data_super = await response_super.json(); 
    tunnel_table=data_super
    if(!data_super.status){
        alert("本渠段在所給條件下無法形成完整的超臨界流況解，可能因初始條件或邊界條件不符。\nUnder the given conditions, a complete supercritical flow solution cannot be established for this channel reach, possibly due to inconsistent initial or boundary conditions.")
    }
    let last_no = Math.ceil(Tunnel_length / Interval)-1;
    critical_end=document.getElementById('start_one')
    critical_end.textContent=last_no
    data_super.data.forEach(row => {
        const tr = document.createElement("tr");
    
        tr.innerHTML = `
        <td>${row.No}</td>
        <td>${row.sta_output}</td>
        <td style='background-color:#757171;color:white'>${row.Q_output}</td>
        <td style='background-color:#757171;color:white'>${row.b_output.toFixed(1)}</td>
        <td style='background-color:#757171;color:white'>${row.L_output.toFixed(3)}</td>
        <td style='background-color:#757171;color:white'>${row.n_output.toFixed(3)}</td>
        <td style='background-color:#757171;color:white'>${row.Z_output.toFixed(3)}</td>
        <td>${row.S_output.toFixed(3)}</td>
        <td>${row.yc_output.toFixed(3)}</td>
        <td>${row.A_output.toFixed(3)}</td>
        <td>${row.T_output.toFixed(3)}</td>
        <td>${row.P_output.toFixed(3)}</td>
        <td>${row.R_output.toFixed(3)}</td>
        <td>${row.V_output.toFixed(3)}</td>
        <td>${row.Sf_output.toFixed(3)}</td>
        <td>${row.speed_head_output.toFixed(3)}</td>
        <td style="color:#0070C0">${row.hf_output.toFixed(3)}</td>
        <td style="color:#0070C0">${row.hce_output.toFixed(3)}</td>
        <td>${row.he_output.toFixed(3)}</td>
        <td>${row.E_output.toFixed(3)}</td>
        <td></td>
        <td style="color:#0070C0">${row.Control_output.toFixed(3)}</td>
        <td style="background-color: #aef;">${row.y_output.toFixed(3)}</td>
        <td class="box" style="background-color: ${
            row.Fr_output == 1 ? '#2460A5' :      // 藍色
            row.Fr_output < 1 ? '#FFFF00' :       // 黃色
            row.Fr_output <= 1.6 ? '#942F50' :     //紫色
            row.Fr_output <= 1.75 ? '#CE1625' :     //紫色
            row.Fr_output <= 1.85 ? '#EF070C' :     //紫色
            '#FF0000'                             // 紅色
          }; color: ${
            row.Fr_output == 1 || row.Fr_output < 1 ? 'white' : 'black'
          }"><b>${row.Fr_output.toFixed(3)}</b></td>
        <td>${row.Water_level_output.toFixed(3)}</td>
        <td>${row.Full_output.toFixed(2)}</td>
        `;
    
        tableBody.appendChild(tr);
      });
      if (all_step<=1){
        all_step=1
    }
}
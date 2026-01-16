async function subcritical_round_cal(){
    console.log('計算亞臨界流')
    const R = parseFloat(document.getElementById("R_round_tunnel").value);
    const Q_tunnel=parseFloat(document.getElementById("Q_round_tunnel").value);
    const n_tunnel=parseFloat(document.getElementById("n_round_tunnel").value);
    const Z_tunnel=parseFloat(document.getElementById("Z_round_tunnel").value);
    const S_tunnel=parseFloat(document.getElementById("S_round_tunnel").value);
    const Critical_depth=parseFloat(document.getElementById("Critical_depth_round").value)
    const yc_value=parseFloat(document.getElementById("yc_round_value").textContent)
    const Tunnel_length=parseFloat(document.getElementById("Tunnel_length_round").value)
    const Interval=parseFloat(document.getElementById("Interval_round").value)
    const Contraction=parseFloat(document.getElementById("Contraction_round").value)
    const Exspansion=parseFloat(document.getElementById("Exspansion_round").value)
    const jsondata = {R,Q_tunnel,n_tunnel,Z_tunnel,S_tunnel,Critical_depth,yc_value,Tunnel_length,Interval,Exspansion};
    const check={R,Q_tunnel,n_tunnel,Z_tunnel,S_tunnel,Critical_depth,Tunnel_length,Interval,Exspansion,Contraction}
    for (const [key, value] of Object.entries(check)) {
        if (value === undefined) {
            alert("請填完所有輸入值");
          return;
        } else if (isNaN(value)) {
            alert("請填完所有輸入值");
          return;
        }
      }
    const tableBody = document.querySelector("#calculation-table tbody");
    if (tableBody) {
        tableBody.innerHTML = ""; // 清空所有 <tr>
      }
    const tr = document.createElement("tr");
    /////////////////////////////以上是清空table//////////////////////////////////////////////////
    const response_sub = await fetch(window.djangoUrls.round_subcritical_table, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", 
        },
        body: JSON.stringify(jsondata),
    });
    if (!response_sub.ok) {
        console.error("API 請求失敗", response_sub.status);
        return;
    }
    
    const data_sub = await response_sub.json(); 
    tunnel_table=data_sub
    data_sub.data.forEach(row => {
      const tr = document.createElement("tr");
      const fmt = (v, d) => typeof v === 'number' ? v.toFixed(d) : v ?? '';
      tr.innerHTML = `
      <td>${row.No}</td>
      <td>${row.sta_output}</td>
      <td style='background-color:#757171;color:white'>${row.Q_output}</td>
      <td style='background-color:#757171;color:white'>${row.b_output.toFixed(1)}</td>
      <td style='background-color:#757171;color:white'>${row.L_output}</td>
      <td style='background-color:#757171;color:white'>${row.n_output.toFixed(3)}</td>
      <td style='background-color:#757171;color:white'>${row.Z_output.toFixed(4)}</td>
      <td>${row.S_output.toFixed(2)}</td>
      <td>${row.yc_output.toFixed(3)}</td>
      <td>${row.A_output.toFixed(3)}</td>
      <td>${row.T_output.toFixed(3)}</td>
      <td>${row.P_output.toFixed(3)}</td>
      <td>${row.R_output.toFixed(3)}</td>
      <td>${row.V_output.toFixed(3)}</td>
      <td>${row.Sf_output.toFixed(3)}</td>
      <td>${row.speed_head_output.toFixed(3)}</td>
      <td style="color:#0070C0">${fmt(row.hf_output, 3)}</td>
      <td style="color:#0070C0">${fmt(row.hce_output, 3)}</td>
      <td>${fmt(row.he_output, 3)}</td>
      <td>${fmt(row.E_output, 3)}</td>
      <td></td>
      <td style="color:#0070C0">${fmt(row.Control_output, 3)}</td>
      <td style="background-color: #aef;">${row.y_output.toFixed(3)}</td>
      <td class="box" style="background-color: ${
          row.Fr_output == 1 ? '#2460A5' :      // 藍色
          row.Fr_output < 1 ? '#FFFF00' :       // 黃色
          row.Fr_output <= 1.6 ? '#942F50' :     //紫色
          row.Fr_output <= 1.75 ? '#CE1625' :     //紫色
          row.Fr_output <= 1.85 ? '#EF070C' :     //紫色
          '#FF0000'                             // 紅色
        }; color: ${
          row.Fr_output == 1  ? 'white' : 'black'
        }"><b>${row.Fr_output.toFixed(3)}</b></td>
      <td>${row.Water_level_output.toFixed(3)}</td>
      <td>${row.Full_output.toFixed(2)}</td>
      `;
      tableBody.appendChild(tr);
    });

}
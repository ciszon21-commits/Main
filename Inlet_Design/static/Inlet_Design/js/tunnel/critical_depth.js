async function critical_depth_cal(){
    console.log('計算臨界流')
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
    const jsondata = {R,Q_tunnel,B2,B1,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n_tunnel,Z_tunnel,S_tunnel,Critical_depth,yc_value,Tunnel_length,Interval,Contraction};
    for (const [key, value] of Object.entries(check)) {
        if (value === undefined|| (isNaN(value) )) {
            alert("請填完所有輸入值");
          return;
        } 
      }

    const response = await fetch(window.djangoUrls.horseshoe, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", // 確保這是 Django 中由模板引擎插入的
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
        <td>${data.b_output}</td>
        <td>${data.L_output}</td>
        <td>${data.n_output}</td>
        <td>${data.Z_output}</td>
        <td>${data.S_output}</td>
        <td>${data.yc_output}</td>
        <td>${data.A_output}</td>
        <td>${data.T_output}</td>
        <td>${data.P_output}</td>
        <td>${data.R_output}</td>
        <td>${data.V_output}</td>
        <td>${data.Sf_output}</td>
        <td>${data.speed_head_output}</td>
        <td>${data.hf_output}</td>
        <td>${data.hce_output}</td>
        <td>${data.he_output}</td>
        <td>${data.E_output}</td>
        <td></td>
        <td>${data.Control_output}</td>
        <td>${data.y_output}</td>
        <td>${data.Fr_output}</td>
        <td>${data.Water_level_output}</td>
        <td>${data.Full_output}</td>
    `;
    
    tableBody.appendChild(tr);
    /////////////////////////////以上是table第一行//////////////////////////////////////////////////
    const response_critical = await fetch(window.location.origin + '/api/horseshoe_critical_table/', {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", // 確保這是 Django 中由模板引擎插入的
        },
        body: JSON.stringify(jsondata),
    });
    const data_critical = await response_critical.json();
    data_critical.data.forEach(row => {
        const tr = document.createElement("tr");
    
        tr.innerHTML = `
        <td>${row.No}</td>
        <td>${row.sta_output}</td>
        <td style='background-color:#757171;color:white'>${row.Q_output}</td>
        <td style='background-color:#757171;color:white'>${row.b_output}</td>
        <td style='background-color:#757171;color:white'>${row.L_output}</td>
        <td style='background-color:#757171;color:white'>${row.n_output}</td>
        <td style='background-color:#757171;color:white'>${row.Z_output}</td>
        <td>${row.S_output}</td>
        <td>${row.yc_output}</td>
        <td>${row.A_output}</td>
        <td>${row.T_output}</td>
        <td>${row.P_output}</td>
        <td>${row.R_output}</td>
        <td>${row.V_output}</td>
        <td>${row.Sf_output}</td>
        <td>${row.speed_head_output}</td>
        <td style="color:#0070C0">${row.hf_output}</td>
        <td style="color:#0070C0">${row.hce_output}</td>
        <td>${row.he_output}</td>
        <td>${row.E_output}</td>
        <td></td>
        <td style="color:#0070C0">${row.Control_output}</td>
        <td style="background-color: #aef;">${row.y_output}</td>
        <td class="box" style="background-color: ${
            row.Fr_output == 1 ? '#2460A5' :      // 藍色
            row.Fr_output < 1 ? '#FFFF00' :       // 黃色
            row.Fr_output <= 1.5 ? '#7F3860' :     //紫色
            '#FF0000'                             // 紅色
          }; color: ${
            row.Fr_output == 1 || row.Fr_output < 1 ? 'white' : 'black'
          }">${row.Fr_output}</td>
        <td>${row.Water_level_output}</td>
        <td>${row.Full_output}</td>
        `;
    
        tableBody.appendChild(tr);
      });
  
  }
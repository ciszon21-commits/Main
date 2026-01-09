let tunnel_table=null
async function tunnel_cal(){
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
    const Exspansion=parseFloat(document.getElementById("Exspansion").value)
    const Contraction=parseFloat(document.getElementById("Contraction").value)
    const check={R,Q_tunnel,B2,B1,n_tunnel,Z_tunnel,S_tunnel,Critical_depth,Tunnel_length,Interval,Exspansion,Contraction}
    for (const [key, value] of Object.entries(check)) {
        if (value === undefined) {

            alert("請填完所有輸入值");
          return;
        } else if (isNaN(value)) {
          console.log(key, value)
            alert("請填完所有輸入值");
          return;
        }
      }
    const jsondata = {R,Q_tunnel,B2,B1,ninety_minus_beta2,yt1max,t1max,p1max,a1max,yt2max,t2max,p2max,a2max,y2max,n_tunnel,Z_tunnel,S_tunnel,Critical_depth,yc_value};
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

    document.getElementById('resultModal').style.display = 'flex';
    if (all_step<=1){
      all_step=1
  }

  }
  function closeModal() {
    document.getElementById('resultModal').style.display = 'none';
  }
  async function tunnel_to_csv() {
    const data = tunnel_table?.data;
  
    if (!Array.isArray(data) || data.length === 0) {
      alert("沒有可下載的資料！");
      return;
    }
  
    // 自動取得欄位名稱
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
  
    for (const row of data) {
      const values = headers.map(header => {
        const val = row[header] ?? '';
        return `"${String(val).replace(/"/g, '""')}"`; // escape 雙引號
      });
      csvRows.push(values.join(','));
    }
  
    const csvString = csvRows.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
  
    const a = document.createElement('a');
    a.href = url;
    a.download = 'tunnel_result.csv';
    a.click();
    URL.revokeObjectURL(url);
  }
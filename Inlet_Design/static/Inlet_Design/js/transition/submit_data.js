let transition_result
async function submit_transition_shape_data(){
    console.log('計算隧道漸變段')
    document.getElementById('transition_step2').classList.remove('d-none')
    const Q=parseFloat(document.getElementById("Q_inlet").textContent);
    const S1=0.2;
    const Z2=parseFloat(document.getElementById("Z2_transition").textContent);
    const b2=parseFloat(document.getElementById("B1_transition").textContent);
    const n=parseFloat(document.getElementById("n_transition").value);
    const C=parseFloat(document.getElementById("C_transition").value);
    const y2=parseFloat(document.getElementById("y2_transition").textContent);
    const y3=yc_for_transition
    if (!y3){
        alert('隧道段為亞臨界流況，不適用隧道漸變段計算')
        return
      }
    let b3, yc3,yt1max,yt2max,y2max,B2,B3,t1max,a1max,a2max,check,api_info,p1max,p2max;
    if (choose_tunnel_type==='circle'){
        b3=parseFloat(document.getElementById("R_round_tunnel").value);
        yc3=parseFloat(document.getElementById("yc_round_value").textContent);
        check={Q,S1,Z2,b2,n,C,b3,yc3,y2,y3}
        api_info={Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type}
      }else if(choose_tunnel_type==='horseshoe'){
        b3=parseFloat(document.getElementById("R_tunnel").value);
        yc3=parseFloat(document.getElementById("yc_value").textContent);
        yt1max=parseFloat(document.getElementById("yt1max_value").textContent);
        yt2max=parseFloat(document.getElementById('yt2max_value').textContent);
        y2max=parseFloat(document.getElementById('y2max_value').textContent);
        B2=parseFloat(document.getElementById("beta2_tunnel").value);
        B3=90-B2
        t1max=parseFloat(document.getElementById("t1max_value").textContent);
        a1max=parseFloat(document.getElementById('a1max_value').textContent);
        a2max=parseFloat(document.getElementById('a2max_value').textContent);
        p1max=parseFloat(document.getElementById('p1max_value').textContent);
        p2max=parseFloat(document.getElementById('p2max_value').textContent);
        
        
        check={Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,yt1max,yt2max,y2max,B3,t1max,a1max,a2max,p1max,p2max}
        api_info={Q,S1,Z2,b2,n,C,b3,yc3,y2,y3,choose_tunnel_type,yt1max,yt2max,y2max,B3,t1max,a1max,a2max,p1max,p2max}
    }

    for (const [key, value] of Object.entries(check)) {
        if (value === undefined) {
            console.log(key, value)
            alert("請填完所有輸入值1");
          return;
        } else if (isNaN(value)) {
            console.log(key, value)
            alert("請填完所有輸入值2");
          return;
        }
    }
    const response_initial = await fetch(window.djangoUrls.transition_shape, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", // 確保這是 Django 中由模板引擎插入的
        },
        body: JSON.stringify(api_info),
    });
    if (!response_initial.ok) {
        console.error("API 請求失敗", response_initial.status);
        return;
    }
    const data_initial = await response_initial.json();

    const tableBody_initial = document.querySelector("#calculation-transition-shape-table tbody");
    if (tableBody_initial) {
        tableBody_initial.innerHTML = ""; // 清空所有 <tr>
      }
    const table_initial=data_initial.data
    transition_result=table_initial
    table_initial.forEach(row => {
        const tr_initial = document.createElement("tr");
        tr_initial.innerHTML = `
        <td>${row.Trial}</td>
        <td>${row.Q}</td>
        <td style="background-color:yellow; color:red">${(row.S*100).toFixed(0)}%</td>
        <td style="background-color:#808080; color:#FFC000">${row.Z2.toFixed(2)}</td>
        <td style="background-color:#808080; color:#FFC000">${row.Z3.toFixed(2)}</td>
        <td style="background-color:#D0CECE; color:red">${row.deltaZ.toFixed(2)}</td>
        <td>${row.b2.toFixed(2)}</td>
        <td>${row.b3.toFixed(1)}</td> 
        <td style=" color:#00B050">${row.L.toFixed(2)}</td>
        <td>${row.n.toFixed(3)}</td>
        <td>${row.y2.toFixed(2)}</td> 
        <td>${row.yc2.toFixed(2)}</td> 
        <td>${row.A2.toFixed(2)}</td> 
        <td>${row.P2.toFixed(2)}</td> 
        <td>${row.R2.toFixed(2)}</td> 
        <td>${row.V2.toFixed(2)}</td> 
        <td>${row.SF2.toFixed(4)}</td> 
        <td>${row.speeding_head2.toFixed(2)}</td>
        <td>${row.E1.toFixed(2)}</td>
        <td>${row.y3.toFixed(2)}</td> 
        <td>${row.yc3.toFixed(2)}</td>
        <td style="background-color:#FFC000">${row.A3.toFixed(2)}</td> 
        <td style="background-color:#FFC000">${row.P3.toFixed(2)}</td>  
        <td>${row.R3.toFixed(2)}</td> 
        <td>${row.T3.toFixed(2)}</td>
        <td>${row.V3.toFixed(2)}</td> 
        <td>${row.SF3.toFixed(4)}</td> 
        <td>${row.speeding_head3.toFixed(3)}</td> 
        <td>${row.E3.toFixed(2)}</td>
        <td>${row.hf.toFixed(3)}</td>
        <td>${row.hce.toFixed(3)}</td>
        <td>${row.he.toFixed(3)}</td>
        <td>${row.E3_.toFixed(2)}</td>
        <td>${row.control.toFixed(3)}</td>
        <td style="background-color:#893459">${row.FR2.toFixed(2)}</td>
        <td style="background-color:#574A7E">${row.FR3.toFixed(2)}</td>
        
        `;
            tableBody_initial.appendChild(tr_initial);
        });
    document.getElementById('next-step').classList.add('d-none');

}
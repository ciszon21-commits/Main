function checknone(value,times,fix){
    if(value!= null){
        return (value*times).toFixed(fix)
    }else{
        return ''
    }
}
async function submit_waterlevel_data(){
    console.log('計算水面線')
    const Q=parseFloat(document.getElementById("Q_inlet").textContent);
    const lweir=parseFloat(document.getElementById("L_weir").textContent);
    const Ogee_crest_elv=parseFloat(document.getElementById("Ogee_crest_elv").textContent)
    const Ogee_height=parseFloat(document.getElementById("Ogee_height").textContent)
    if (choose_tunnel_type==='circle'){
        check={Q,lweir,Ogee_crest_elv,Ogee_height}
        api_info={Q,lweir,choose_tunnel_type,Ogee_crest_elv,Ogee_height}
      }else if(choose_tunnel_type==='horseshoe'){
        check={Q,lweir,Ogee_crest_elv,Ogee_height}
        api_info={Q,lweir,choose_tunnel_type,Ogee_crest_elv,Ogee_height}
        }
    for (const [key, value] of Object.entries(check)) {
        if (value === undefined ||isNaN(value) ) {
            console.log(key, value)
            alert("請填完所有輸入值1");
            return;
        } 
    }
    const response = await fetch(window.djangoUrls.water_level, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", // 確保這是 Django 中由模板引擎插入的
        },
        body: JSON.stringify(api_info),
    });
    if (!response.ok) {
        console.error("API 請求失敗", response.status);
        return;
    }
    const data = await response.json();
    const tableBody = document.querySelector("#waterlevel-table tbody");
    if (tableBody) {
        tableBody.innerHTML = ""; // 清空所有 <tr>
      }
    const table=data.data
    table.forEach(row => {
        const tr_ = document.createElement("tr");
        tr_.innerHTML = `
        <td>${row.No}</td>
        <td>${row.sta}</td>
        <td>${row.type}</td>
        <td style="background-color:#808080; color:white">${row.Q}</td>
        <td style="background-color:#808080; color:white">${checknone(row.b,1,2)}</td>
        <td style="background-color:#808080; color:white">${checknone(row.L,1,2) }</td>
        <td style="background-color:#808080; color:white">${checknone(row.n,1,3)}</td>
        <td style="background-color:#808080; color:white">${row.Z}</td>
        <td>${checknone(row.S,100,2 )}%</td>
        <td>${row.yc.toFixed(2)}</td> 
        <td>${row.A.toFixed(2)}</td> 
        <td>${row.T.toFixed(2)}</td> 
        <td>${row.P.toFixed(2)}</td> 
        <td>${row.R.toFixed(2)}</td> 
        <td>${row.v.toFixed(2)}</td> 
        <td>${row.Sf.toFixed(4)}</td> 
        <td>${row.speeding_head.toFixed(2)}</td>
        <td>${row.hf.toFixed(3)}</td>
        <td>${row.hce.toFixed(3)}</td>
        <td>${row.he.toFixed(3)}</td>
        <td>${row.E.toFixed(3)}</td>
        <td>${row.Control.toFixed(3)}</td>
        <td>${row.Water_depth.toFixed(3)}</td>
        <td>${row.Fr.toFixed(3)}</td>
        <td>${row.Water_level.toFixed(2)}</td>
        <td>${checknone(row.Tunnel_height,1,2 )}</td>
        <td>${checknone(row.full,100,2 )}</td>
        `;
            tableBody.appendChild(tr_);
        });

}
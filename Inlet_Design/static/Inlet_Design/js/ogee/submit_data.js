let result= null
let cachedResultOgee = null; // 全域變數
document.getElementById('submit_data').addEventListener('click', async function() {
    const form = document.getElementById('calculationForm');
    const formData = new FormData(form);
    init_chart()
    
    // Convert form data to JSON
    const jsonData = {};
    formData.forEach((value, key) => {
        jsonData[key] = value;
    });

    try {
        const response = await fetch(window.djangoUrls.step_one_input, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token }}", // Ensure the CSRF token is dynamically inserted
            },
            body: JSON.stringify(jsonData),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        result = await response.json();
        document.getElementById('q').textContent = result.q.toFixed(2) || 'N/A';
        document.getElementById('va').textContent = result.va.toFixed(2) || 'N/A';
        document.getElementById('ha').textContent = result.ha.toFixed(2) || 'N/A';
        document.getElementById('he_add_p').textContent = result.he_add_p.toFixed(2) || 'N/A';
        document.getElementById('sn').textContent = result.sn.toFixed(6) || 'N/A';
        document.getElementById('hf').textContent = result.hf.toFixed(4) || 'N/A';
        document.getElementById('ha_01').textContent = result.ha_01.toFixed(3) || 'N/A';
        document.getElementById('head_loss').textContent = result.head_loss.toFixed(3) || 'N/A';
        document.getElementById('P_over_heff').textContent = result.P_over_heff.toFixed(2) || 'N/A';
        document.getElementById('hd_add_d').textContent = result.hd_add_d.toFixed(2) || 'N/A';
        document.getElementById('heff').textContent = result.heff.toFixed(2) || 'N/A';
        document.getElementById('hd_add_d_over_heff').textContent = result.hd_add_d_over_heff.toFixed(2) || 'N/A';
        document.getElementById('hd_over_heff').textContent = result.hd_over_heff.toFixed(2) || 'N/A';
        document.getElementById('hd').textContent = result.hd.toFixed(2) || 'N/A';
        document.getElementById('d').textContent = result.d.toFixed(2) || 'N/A';
        document.getElementById('v').textContent = result.v.toFixed(2) || 'N/A';
        document.getElementById('hv').textContent = result.hv.toFixed(2) || 'N/A';
        document.getElementById('hv_minus_hv').textContent = result.hd_minus_hv.toFixed(2) || 'N/A';
        document.getElementById('error').textContent = result.error.toFixed(2)*100+'%' || 'N/A';
        if (result.error.toFixed(2)*100>10){
          document.getElementById('check').textContent="判斷式-fail";
          document.getElementById('check').style.color = "red";
        }else{
          
          document.getElementById('check').textContent="判斷式-pass";
          document.getElementById('check').style.color = "green";
          document.getElementById('co_ip').textContent = result.co_ip.toFixed(2) || 'N/A';
          document.getElementById('co_si').textContent = result.co_si.toFixed(2) || 'N/A';
          document.getElementById('cs_over_co').textContent = result.cs_over_co.toFixed(2) || 'N/A';
          document.getElementById('cs').textContent = result.cs.toFixed(2) || 'N/A';
          document.getElementById('ogee_h').textContent = result.ogee_h.toFixed(2) || 'N/A';
          document.getElementById('P1').textContent = result.P1 || 'N/A'
          document.getElementById('Ho=He').textContent = result.he
          document.getElementById('C=Cs').textContent = result.cs.toFixed(2) || 'N/A';
          document.getElementById('q2').textContent = result.q2.toFixed(2) || 'N/A';
          document.getElementById('va2').textContent = result.va2.toFixed(2) || 'N/A';
          document.getElementById('ha2').textContent = result.ha.toFixed(2) || 'N/A';
          document.getElementById('ha/Ho').textContent = result.ha_over_ho.toFixed(2) || 'N/A';
          document.getElementById('K').textContent = result.k.toFixed(2) || 'N/A';
          document.getElementById('n2').textContent = result.n2.toFixed(2) || 'N/A';
          document.getElementById('Xc/Ho').textContent = result.xc_over_ho.toFixed(2) || 'N/A';
          document.getElementById('Xc').textContent = result.Xc.toFixed(4) || 'N/A';
          document.getElementById('Yc/Ho').textContent = result.yc_over_ho.toFixed(4) || 'N/A';
          document.getElementById('Yc').textContent = result.yc.toFixed(4) || 'N/A';
          document.getElementById('R1/Ho').textContent = result.r1_over_ho.toFixed(4) || 'N/A';
          document.getElementById('R1').textContent = result.r1.toFixed(4) || 'N/A';
          document.getElementById('R2/Ho').textContent = result.r2_over_ho.toFixed(4) || 'N/A';
          document.getElementById('R2').textContent = result.r2.toFixed(4) || 'N/A';
          document.getElementById('R1-R2').textContent = result.r1_minus_r2.toFixed(4) || 'N/A';
          ///////////////////////////////////////////////
          document.getElementById('Cd_inlet').textContent = result.cs.toFixed(2) || 'Ogee堰輸入值';


          drawPointAndLines(chart_9_26, result.hd_add_d_over_heff, result.hd_over_heff, {
            pointColor: 'orange',
            horizontalLineColor: 'gray',
            verticalLineColor: 'orange',
            horizontalLineXRange: [1.02, result.hd_add_d_over_heff],
            verticalLineYRange: [0.2,  result.hd_over_heff],
            lineWidth: 2
        })
        drawPointAndLines(chart_9_23, result.P_over_heff, result.co_ip, {
            pointColor: 'orange',
            horizontalLineColor: 'gray',
            verticalLineColor: 'orange',
            horizontalLineXRange: [0, result.P_over_heff],
            verticalLineYRange: [3,result.co_ip],
            lineWidth: 2
        })
        drawPointAndLines(chart_9_27, result.hd_add_d_over_heff, result.cs_over_co, {
            pointColor: 'orange',
            horizontalLineColor: 'gray',
            verticalLineColor: 'orange',
            horizontalLineXRange: [1, result.hd_add_d_over_heff],
            verticalLineYRange: [0.75,result.cs_over_co],
            lineWidth: 2
        })
        drawPointAndLines(chart_9_21_a, result.ha_over_ho, result.k, {
            pointColor: 'orange',
            horizontalLineColor: 'gray',
            verticalLineColor: 'orange',
            horizontalLineXRange: [0, result.ha_over_ho],
            verticalLineYRange: [0.44,result.k],
            lineWidth: 2
        })
        drawPointAndLines(chart_9_21_b, result.ha_over_ho, result.n2, {
            pointColor: 'orange',
            horizontalLineColor: 'gray',
            verticalLineColor: 'orange',
            horizontalLineXRange: [0, result.ha_over_ho],
            verticalLineYRange: [1.74,result.n2],
            lineWidth: 2
        })
        drawPointAndLines(chart_9_21_c, result.ha_over_ho, result.xc_over_ho, {
            pointColor: 'orange',
            horizontalLineColor: 'gray',
            verticalLineColor: 'orange',
            horizontalLineXRange: [0, result.ha_over_ho],
            verticalLineYRange: [0.14,result.xc_over_ho],
            lineWidth: 2
        })
        drawPointAndLines(chart_9_21_d, result.ha_over_ho, result.yc_over_ho, {
            pointColor: 'orange',
            horizontalLineColor: 'gray',
            verticalLineColor: 'orange',
            horizontalLineXRange: [0, result.ha_over_ho],
            verticalLineYRange: [0,result.yc_over_ho],
            lineWidth: 2
        })
        drawPointAndLines(chart_9_21_e, result.ha_over_ho, result.r1_over_ho, {
            pointname:'R1/Ho',
            pointColor: 'gray',
            horizontalLineColor: 'gray',
            verticalLineColor: 'orange',
            horizontalLineXRange: [0, result.ha_over_ho],
            verticalLineYRange: [0,result.r1_over_ho],
            lineWidth: 2
        })
        drawPointAndLines(chart_9_21_e, result.ha_over_ho, result.r2_over_ho, {
            pointname:'R2/Ho',
            pointColor: 'blue',
            horizontalLineColor: 'blue',
            verticalLineColor: 'orange',
            horizontalLineXRange: [0, result.ha_over_ho],
            verticalLineYRange: [0,result.r2_over_ho],
            lineWidth: 2
        })
        let ogee_input={'r1':result.r1,'r2':result.r2,'p':result.P1,'Hd':result.he,'hd':result.hd,'x':result.ogee_h,'d':result.d,'xc': result.Xc,'yc':result.yc,'k':result.k,'n':result.n2}
        const response_ogee = await fetch(window.djangoUrls.ogee, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token }}", // Ensure the CSRF token is dynamically inserted
            },
            body: JSON.stringify(ogee_input),
        });

        if (!response_ogee.ok) {
            throw new Error(`HTTP error! status: ${response_ogee.status}`);
        }

        const result_ogee = await response_ogee.json();
        cachedResultOgee=result_ogee
        drawCircle(chart_ogee, result_ogee.circle_r1, options = {
            pointname: 'circle_r1',
            pointColor: '#DAA520',
            lineWidth: 1,
            dashStyle: 'ShortDash',

        })
        drawCircle(chart_ogee, result_ogee.circle_r2, options = {
            pointname: 'circle_r2',
            pointColor: 'gray',
            lineWidth: 1,
            dashStyle: 'ShortDash', 

        })
        drawCircle(chart_ogee, result_ogee.circle_r1_minus_r2, options = {
            pointname: 'circle_r1_minus_r2',
            pointColor: 'green',
            lineWidth: 1,
            dashStyle: 'ShortDash', 

        })
        drawCircle(chart_ogee, result_ogee.circle_r3, options = {
            pointname: 'circle_r3',
            pointColor: 'blue',
            lineWidth: 1,
            dashStyle: 'ShortDash', 

        })
        drawLine(chart_ogee, result_ogee.ogee_result, options = {
            pointname: 'Ogee',
            pointColor: 'red',
            lineWidth: 3,
            dashStyle: 'solid', 

        })
          const figBtnCell = document.getElementById('fig_btn');
          // Create a button element
          const button = document.createElement('button');
          const fig1 = document.getElementById('fig1');
          // Set the button's text
          button.textContent = '查表';
        
          // Add additional attributes or styles to the button if needed
          button.id = 'dynamic_btn';
          button.style.padding = '5px 8px';
          button.style.backgroundColor = 'blue';
          button.style.color = 'white';
          button.style.border = 'none';
          button.style.borderRadius = '4px';
          button.addEventListener('click', function () {
            
            fig1.style.display = 'block';
          });
        
          figBtnCell.textContent = ''; // Clear existing content
          figBtnCell.appendChild(button); // Add the button to the <td>
          //////////////////////////進水口用///////////////////////////////////
          const y_bot2= result_ogee.y_bot2
          const x_bot2= result_ogee.x_bot2
          const Ogee_length=document.getElementById('Ogee_length')
          const Ogee_height=document.getElementById('Ogee_height')
          const y_og=document.getElementById("y_og")
          Ogee_length.textContent=x_bot2.toFixed(2)
          Ogee_height.textContent=result.he.toFixed(2)
          y_og.textContent=(x_bot2*1.2).toFixed(2)
          updateLmin()
          if (all_step<=2){
            all_step=2
        }
        }
          

    } catch (error) {
        console.error("Error:", error);
        alert("計算失敗，請稍後再試。");
    }
  });
  function downloadOgeeAsCSV() {
    if (!cachedResultOgee || cachedResultOgee.length === 0) {
        alert("沒有可下載的資料！");
        return;
        
    }
    const data = cachedResultOgee?.ogee_result;
    const headers = ['x', 'y'];
    const csvRows = [];
    csvRows.push(headers.join(','));

    for (const row of data) {
        if (Array.isArray(row)) {
            const values = row.map(val => `"${String(val).replace(/"/g, '""')}"`);
            csvRows.push(values.join(','));
        }
    }

    const csvString = csvRows.join('\n');

    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ogee_result.csv';
    a.click();
    URL.revokeObjectURL(url);
}
function updateHe(){
    const He = parseFloat(document.getElementById("He").value);
    const He_inlet=document.getElementById("He_inlet");
    if (!isNaN(He)){
        He_inlet.textContent=(He)
    }
}
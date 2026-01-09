var fig_inlet = Highcharts.chart('fig_inlet', {
    chart: {
        type: 'scatter',
        zoomType: 'xy',
        plotBorderWidth: 1,
        height:600, 
        width:600,
        showEmpty: true 
    },
    title: {
        text: 'Inlet Transition RESULT'
    },
    xAxis: {

        tickInterval: 2,
        min: -10,   
        max: 70,
        gridLineWidth: 0.5,
    },
    yAxis: {
        tickInterval: 2, 
        min: -40,   
        max: 40,
        gridLineWidth: 0.5,
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    tooltip: {
        enabled: false // Disable hover tooltips
    },
    series: [{
        name: 'Transparent Point',
        data: [[0, 0]], // Data point at (0, 0)
        marker: {
            radius: 5, // Size of the point
            fillColor: 'rgba(0, 0, 0, 0)' // Transparent color
        }
    }]
});
var fig_inlet_side_view = Highcharts.chart('fig_inlet_side_view', {
    chart: {
        type: 'scatter',
        zoomType: 'xy',
        plotBorderWidth: 1,
        height:250, 
        width:600,
        showEmpty: true 
    },
    title: {
        text: 'Inlet Transition RESULT'
    },
    xAxis: {

        tickInterval: 2,
        min: -10,   
        max: 70,
        gridLineWidth: 0.5,
    },
    yAxis: {
        tickInterval: 2, 
        min: 8,   
        max: 26,
        gridLineWidth: 0.5,
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    tooltip: {
        enabled: false // Disable hover tooltips
    },
    series: [{
        name: 'Transparent Point',
        data: [[0, 0]], // Data point at (0, 0)
        marker: {
            radius: 5, // Size of the point
            fillColor: 'rgba(0, 0, 0, 0)' // Transparent color
        }
    }]
});
function init_chart(){
    fig_inlet = Highcharts.chart('fig_inlet', {
        chart: {
            type: 'scatter',
            zoomType: 'xy',
            plotBorderWidth: 1,
            height:600, 
            width:600,
            showEmpty: true 
        },
        title: {
            text: 'Inlet Transition RESULT'
        },
        xAxis: {
    
            tickInterval: 2,
            min: -10,   
            max: 70,
            gridLineWidth: 0.5,
        },
        yAxis: {
            tickInterval: 2, 
            min: -40,   
            max: 40,
            gridLineWidth: 0.5,
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: false 
        },
        tooltip: {
            enabled: false // Disable hover tooltips
        },
        series: [{
            name: 'Transparent Point',
            data: [], // Data point at (0, 0)
            marker: {
                radius: 5, // Size of the point
                fillColor: 'rgba(0, 0, 0, 0)' // Transparent color
            }
        }]
    });
    fig_inlet_side_view = Highcharts.chart('fig_inlet_side_view', {
        chart: {
            type: 'scatter',
            zoomType: 'xy',
            plotBorderWidth: 1,
            height:250, 
            width:600,
            showEmpty: true 
        },
        title: {
            text: 'Inlet Transition RESULT'
        },
        xAxis: {
    
            tickInterval: 2,
            min: -10,   
            max: 70,
            gridLineWidth: 0.5,
        },
        yAxis: {
            tickInterval: 2, 
            min: 8,   
            max: 26,
            gridLineWidth: 0.5,
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: false 
        },
        tooltip: {
            enabled: false // Disable hover tooltips
        },
        series: [{
            name: 'Transparent Point',
            data: [], // Data point at (0, 0)
            marker: {
                radius: 5, // Size of the point
                fillColor: 'rgba(0, 0, 0, 0)' // Transparent color
            }
        }]
    });
}
async function inlet_draw(){
    console.log("繪圖")
    init_chart()
    if (inlet_draw_parameter === undefined) {
        alert("請填完所有輸入值");
      return;
    }
    const response = await fetch(window.djangoUrls.inlet_diagram, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", 
        },
        body: JSON.stringify(inlet_draw_parameter),
    });
    if (!response.ok) {
        console.error("API 請求失敗", response.status);
        return;
    }
    const data = await response.json();
    fig_inlet.addSeries({
        name: 'wall_curve_left',
        type: 'line',
        color:'black',
        data: data.data['wall_curve_left'],
        lineWidth: 2,
        
    });
    fig_inlet.addSeries({
        name: 'wall_curve_right',
        type: 'line',
        color:'black',
        lineWidth:2,
        data: data.data['wall_curve_right'],
        
    });
    fig_inlet.addSeries({
        name: 'greenline',
        type: 'line',
        color:'green',
        lineWidth:2,
        data: data.data['greenline'],
        
    });
    fig_inlet.addSeries({
        name: 'vertical_black',
        type: 'line',
        color:'black',
        lineWidth:2,
        data: data.data['vertical_black'],
        
    });
    fig_inlet.addSeries({
        name: 'toe_curve_black',
        type: 'line',
        color:'black',
        lineWidth:2,
        data: data.data['toe_curve_black'],
        
    });
    fig_inlet.addSeries({
        name: 'US_curve_black',
        type: 'line',
        color:'black',
        lineWidth:2,
        data: data.data['US_curve_black'],
        
    });
    fig_inlet.addSeries({
        name: 'center_curve_red',
        type: 'line',
        color:'red',
        lineWidth:2,
        dashStyle: 'Dash',
        data: data.data['center_curve_red'],
        
    });
    fig_inlet.addSeries({
        name: 'left_curve_red',
        type: 'line',
        color:'red',
        lineWidth:2,
        dashStyle: 'Dash',
        data: data.data['left_curve_red'],
        
    });
    fig_inlet.addSeries({
        name: 'right_curve_red',
        type: 'line',
        color:'red',
        lineWidth:2,
        dashStyle: 'Dash',
        data: data.data['right_curve_red'],
        
    });
    fig_inlet.update({
        xAxis: {
            min:-10,     
            max: data.data['x_max']   // 這裡你可以自訂 x 軸的結束值
        }
    });
    const Ogee_crest_elv=parseFloat(document.getElementById("Ogee_crest_elv").textContent);
    const Toe_Elevation=parseFloat(document.getElementById("Toe_Elevation").textContent);
    const Starting_station=parseFloat(document.getElementById("Starting_station").value);
    const X_og=parseFloat(document.getElementById("X_og").textContent);
    const selection_L1=parseFloat(document.getElementById("selection_L1").textContent);
    const selection_Z2=parseFloat(document.getElementById("selection_Z2").textContent);
    var ogee_result=cachedResultOgee.ogee_result
    ogee_result = ogee_result.map(([x, y]) => [x, y + Ogee_crest_elv]);
    ogee_result.push([X_og+Starting_station,Toe_Elevation])
    ogee_result.push([X_og+Starting_station+selection_L1,selection_Z2])
    const yValues = ogee_result.map(point => point[1]);
    const yMax = Math.max(...yValues);
    const yMin = Math.min(...yValues);
    fig_inlet_side_view.addSeries({
        name: 'ogee and inlet transition channel(side view)',
        type: 'line',
        color:'red',
        lineWidth:2,
        data: ogee_result,
        
    });
    fig_inlet_side_view.update({
        xAxis: {
            min:-10,     
            max: data.data['x_max']   
        },
        yAxis: {
            min:yMin-6,     
            max: yMax+6   
        }
    });
}

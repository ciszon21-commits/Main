var transition_cross_section =Highcharts.chart('transition_cross_section', {
    chart: {
        type: 'scatter',
        zoomType: 'xy',
        plotBorderWidth: 1,
        height:800, 
        width:400,
        showEmpty: true 
    },
    title: {
        text: 'Cross Section'
    },
    xAxis: {

        tickInterval: 2,
        min: -8,   
        max: 8,
        gridLineWidth: 0.5,
    },
    yAxis: {
        tickInterval: 2, 
        min: 0,   
        max:30,
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
var transition_layout =Highcharts.chart('transition_layout', {
    chart: {
        type: 'scatter',
        zoomType: 'xy',
        plotBorderWidth: 1,
        height:400, 
        width:600,
        showEmpty: true 
    },
    title: {
        text: 'Layout'
    },
    xAxis: {

        tickInterval: 2,
        min: 60,   
        max: 86,
        gridLineWidth: 0.5,
    },
    yAxis: {
        tickInterval: 2, 
        min: -8,   
        max:8,
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
        data: [[60, 0]], // Data point at (0, 0)
        marker: {
            radius: 5, // Size of the point
            fillColor: 'rgba(0, 0, 0, 0)' // Transparent color
        }
    }]
});
var transition_profile =Highcharts.chart('transition_profile', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Profile'
    },
    
    xAxis: {

        tickInterval: 2,
        min: 60,   
        max: 86,
        gridLineWidth: 0.5,
    },
    yAxis: {
        tickInterval: 2, 
        min: 0,   
        max:30,
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
        data: [[60, 0]], // Data point at (0, 0)
        marker: {
            radius: 5, // Size of the point
            fillColor: 'rgba(0, 0, 0, 0)' // Transparent color
        }
    }]
});
function init_transition_chart(){
    transition_cross_section =Highcharts.chart('transition_cross_section', {
        chart: {
            type: 'scatter',
            zoomType: 'xy',
            plotBorderWidth: 1,
            height:800, 
            width:400,
            showEmpty: true 
        },
        title: {
            text: 'Cross Section'
        },
        xAxis: {
    
            tickInterval: 2,
            min: -8,   
            max: 8,
            gridLineWidth: 0.5,
        },
        yAxis: {
            tickInterval: 2, 
            min: 0,   
            max:30,
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
    transition_layout =Highcharts.chart('transition_layout', {
        chart: {
            type: 'scatter',
            zoomType: 'xy',
            plotBorderWidth: 1,
            height:400, 
            width:600,
            showEmpty: true 
        },
        title: {
            text: 'Layout'
        },
        xAxis: {
    
            tickInterval: 2,
            min: 60,   
            max: 86,
            gridLineWidth: 0.5,
        },
        yAxis: {
            tickInterval: 2, 
            min:-8,   
            max:8,
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
    transition_profile =Highcharts.chart('transition_profile', {
        chart: {
            type: 'line'
        },
        title: {
            text: 'Profile'
        },
        
        xAxis: {
    
            tickInterval: 2,
            min: 60,   
            max: 86,
            gridLineWidth: 0.5,
        },
        yAxis: {
            tickInterval: 2, 
            min: 0,   
            max:30,
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
async function drawtransition() {
    const B2 = parseFloat(document.getElementById('selection_transition_B1').textContent)
    const Z2 = parseFloat(document.getElementById('selection_transition_Z2').textContent)
    const Z3 = parseFloat(document.getElementById('selection_transition_Z3_use').textContent)
    const B3 =parseFloat( document.getElementById('selection_transition_B3').textContent)
    const stastart =parseFloat( document.getElementById('Starting_station').value)
    const ltotal =parseFloat( document.getElementById('selection_Ltotal').textContent)
    const l2 =parseFloat( document.getElementById('selection_transition_L2_use').textContent)
    const beta1 =parseFloat( document.getElementById('beta1_tunnel').value)
    const beta2 =parseFloat( document.getElementById('beta2_tunnel').value)
    const yt2max=parseFloat( document.getElementById('yt2max_value').textContent)
    
    const input={B2,Z2,Z3,B3,choose_tunnel_type,stastart,ltotal,l2,beta1,beta2,yt2max}
    const response_transition = await fetch(window.djangoUrls.transition_figure, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}", // Ensure the CSRF token is dynamically inserted
        },
        body: JSON.stringify(input),
    });

    if (!response_transition.ok) {
        throw new Error(`HTTP error! status: ${response_transition.status}`);
    }
    const result_transition = await response_transition.json();
    drawCircle(transition_cross_section, result_transition.rectangle, options = {
        pointname: 'rectangle',
        pointColor: 'green',
        lineWidth: 1,
        dashStyle: 'solid', 

    })
    drawCircle(transition_cross_section, result_transition.circle_or_horseshoe, options = {
        pointname: 'circle or horseshhoe',
        pointColor: 'red',
        lineWidth: 1,
        dashStyle: 'solid', 
    })
    drawLine(transition_layout, result_transition.left_wall, options = {
        pointname: 'left wall',
        pointColor: 'black',
        lineWidth: 2,
        dashStyle: 'solid', 

    })
    drawLine(transition_layout, result_transition.right_wall, options = {
        pointname: 'right wall',
        pointColor: 'black',
        lineWidth: 2,
        dashStyle: 'solid', 

    })
    drawLine(transition_layout, result_transition.upstream, options = {
        pointname: 'upstream',
        pointColor: 'green',
        lineWidth: 2,
        dashStyle: 'solid', 

    })
    drawLine(transition_layout, result_transition.downstream, options = {
        pointname: 'downstream',
        pointColor: 'red',
        lineWidth: 2,
        dashStyle: 'solid', 

    })
    drawArea(transition_profile, result_transition.top1, {
        pointname: 'Area Between Top 1 and Top 2',
        pointColor: 'rgba(166, 166, 166,0.4)', 
    });
    drawArea(transition_profile, result_transition.top2, {
        pointname: 'Area Between Top 2',
        pointColor: 'rgba(255, 255, 255, 1)', 
    });
    
    drawArea(transition_profile, result_transition.bottom, {
        pointname: 'Area bottom and 0',
        pointColor: 'rgba(0, 0, 0, 0.7)', 
    });
    drawLine(transition_profile, result_transition.top1, options = {
        pointname: 'top1',
        pointColor: 'black',
        lineWidth: 2,
        dashStyle: 'ShortDash', 

    })
    drawLine(transition_profile, result_transition.top2, options = {
        pointname: 'top2',
        pointColor: 'black',
        lineWidth: 2,
        dashStyle: 'ShortDash', 

    })
    drawLine(transition_profile, result_transition.bottom, options = {
        pointname: 'bottom',
        pointColor: 'red',
        lineWidth: 2,
        dashStyle: 'solid', 
    })
    transition_cross_section.update({
        xAxis: {
            min:result_transition.transition_layout_ymin,     
            max: result_transition.transition_layout_ymax   
        },
        yAxis: {
            min:0,     
            max: result_transition.transition_profile_ymax   
        }
    });
    transition_layout.update({
        xAxis: {
            min:result_transition.transition_layout_xmin,     
            max: result_transition.transition_layout_xmax    
        },
        yAxis: {
            min:result_transition.transition_layout_ymin,     
            max: result_transition.transition_layout_ymax   
        }
    });
    transition_profile.update({
        xAxis: {
            min:result_transition.transition_layout_xmin,     
            max: result_transition.transition_layout_xmax 
        },
        yAxis: {
            min:0,     
            max: result_transition.transition_profile_ymax
        }
    });
    document.getElementById('next-step').classList.remove('d-none');
    

}
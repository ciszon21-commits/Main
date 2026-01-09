var chart_9_26 =Highcharts.chart('fig_9_26', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Value of (hd+d)/He for Supercritical'
    },
    subtitle: {
        text: 'Fig. 9-26 '
    },
    xAxis: {
        title: {
            text: 'POSITION OF DOWNSTREAM APRON (hd+d)/He'
        },
        tickLength: 10,
        tickInterval: 0.04,
    },
    yAxis: {
        title: {
            text: 'DEGREE OF SUBMERGENCE (hd/He)'
        },
        tickInterval: 0.2, 
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name:"DEGREE OF SUBMERGENCE (hd/He)",
        data: [
            [1.00, 0.33],
            [1.03, 0.39],
            [1.07, 0.45],
            [1.10, 0.51],
            [1.15, 0.56],
            [1.19, 0.62],
            [1.24, 0.68],
            [1.28, 0.73],
            [1.33, 0.79],
            [1.37, 0.85],
            [1.41, 0.91],
            [1.46, 0.96],
            [1.51, 1.02],
            [1.55, 1.08],
            [1.60, 1.13],
            [1.64, 1.19],
            [1.69, 1.24],
            [1.74, 1.30],
            [1.79, 1.36],
            [1.83, 1.41],
            [1.88, 1.47],
            [1.93, 1.53],
            [1.98, 1.58],
            [2.03, 1.64],
            [2.08, 1.70]
        ]
    }]
});
var chart_9_23 =Highcharts.chart('fig_9_23', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Coefficient of Co (in feet)'
    },
    subtitle: {
        text: 'Fig. 9-23 '
    },
    xAxis: {
        title: {
            text: 'P/Ho'
        },
        tickLength: 10,
        tickInterval: 0.1,
    },
    yAxis: {
        title: {
            text: 'Value Of Co'
        },
        tickInterval: 0.2, 
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name:"Value Of Co",
        data: [
        [0.0, 3.08], [0.1, 3.3816], [0.2, 3.559], [0.3, 3.684], [0.4, 3.7566],
        [0.5, 3.7965], [0.6, 3.8263], [0.7, 3.8483], [0.8, 3.8644], [0.9, 3.8763],
        [1.0, 3.8874], [1.1, 3.8964], [1.2, 3.9031], [1.3, 3.9083], [1.4, 3.9136],
        [1.5, 3.9174], [1.6, 3.922], [1.7, 3.9257], [1.8, 3.928], [1.9, 3.9317],
        [2.0, 3.9354], [2.1, 3.9383], [2.2, 3.9398], [2.3, 3.9427], [2.4, 3.9441],
        [2.5, 3.9449], [2.6, 3.9477], [2.7, 3.9484], [2.8, 3.9483], [2.9, 3.9482]]
    }]
  });
var chart_9_27 = Highcharts.chart('fig_9_27', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Correction Coefficient of Cs'
    },
    subtitle: {
        text: 'Fig. 9-27 '
    },
    xAxis: {
        title: {
            text: '(hd+d)/He'
        },
        tickLength: 10,
        tickInterval: 0.1,
        min: 1,   
        max: 1.7  
    },
    yAxis: {
        title: {
            text: 'Cs/Co'
        },
        tickInterval: 0.05, 
        min: 0.76,   
        max: 1.01
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name: "DEGREE OF SUBMERGENCE (hd/He)",
        data: [
            [1, 0.7705],
            [1.0089, 0.7793],
            [1.0303, 0.7996],
            [1.0488, 0.8148],
            [1.0571, 0.8207],
            [1.0869, 0.8414],
            [1.0991, 0.8481],
            [1.1198, 0.8605],
            [1.1488, 0.876],
            [1.1557, 0.8796],
            [1.1748, 0.8889],
            [1.1989, 0.9001],
            [1.2229, 0.9109],
            [1.249, 0.9209],
            [1.2743, 0.9304],
            [1.2996, 0.9386],
            [1.3069, 0.9404],
            [1.349, 0.9526],
            [1.3841, 0.961],
            [1.4004, 0.9647],
            [1.4494, 0.9741],
            [1.4886, 0.981],
            [1.5009, 0.9829],
            [1.5499, 0.9898],
            [1.6002, 0.9946],
            [1.6513, 0.9984],
            [1.6786, 1],
            [10, 1]
        ],
        marker: {
            enabled: true, 
            radius: 4, 

        }
    }]
});
var chart_9_21_a = Highcharts.chart('fig_9_21_a', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Value of K'
    },
    subtitle: {
        text: 'Fig. 9-21 (圖4)'
    },
    xAxis: {
        title: {
            text: 'ha/Ho'
        },
        tickLength: 10,
        tickInterval: 0.05,
        min: 0,   
        max: 0.25  
    },
    yAxis: {
        title: {
            text: 'k'
        },
        tickInterval: 0.01, 
        min: 0.44,   
        max: 0.52
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name: "Value of K",
        data: 
            [
                [0.0004, 0.499],
                [0.0051, 0.5005],
                [0.0099, 0.5019],
                [0.0199, 0.5042],
                [0.03, 0.506],
                [0.0398, 0.5081],
                [0.0501, 0.51],
                [0.0599, 0.5118],
                [0.07, 0.5125],
                [0.0798, 0.5125],
                [0.0898, 0.5118],
                [0.1001, 0.5109],
                [0.1097, 0.5091],
                [0.12, 0.5067],
                [0.1299, 0.5035],
                [0.1402, 0.4998],
                [0.1501, 0.4945],
                [0.1597, 0.4901],
                [0.1701, 0.485],
                [0.1786, 0.4799],
                [0.1805, 0.4788],
                [0.19, 0.473],
                [0.1998, 0.4658]
              ]
        ,
        marker: {
            enabled: true, 
            radius: 4, 

        }
    }]
});
var chart_9_21_b = Highcharts.chart('fig_9_21_b', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Value of n'
    },
    subtitle: {
        text: 'Fig. 9-21 (圖5)'
    },
    xAxis: {
        title: {
            text: 'ha/Ho'
        },
        tickLength: 10,
        tickInterval: 0.05,
        min: 0,   
        max: 0.25  
    },
    yAxis: {
        title: {
            text: 'n'
        },
        tickInterval: 0.02, 
        min: 1.74,   
        max: 1.9
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name: "Value of XC/Ho",
        data: [
                [0, 1.8728],
                [0.0098, 1.8666],
                [0.0198, 1.8615],
                [0.0298, 1.8564],
                [0.0397, 1.8518],
                [0.0499, 1.8479],
                [0.0597, 1.8442],
                [0.0699, 1.8409],
                [0.0795, 1.8382],
                [0.0895, 1.8363],
                [0.0995, 1.8347],
                [0.1096, 1.8333],
                [0.1196, 1.8317],
                [0.1295, 1.8312],
                [0.1399, 1.8312],
                [0.1498, 1.8305],
                [0.1599, 1.8312],
                [0.1698, 1.8321],
                [0.1797, 1.8338],
                [0.1899, 1.8354],
                [0.1997, 1.837]  
              ],
        marker: {
            enabled: true, 
            radius: 4, 

        }
    }]
});
var chart_9_21_c = Highcharts.chart('fig_9_21_c', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Value of XC/Ho'
    },
    subtitle: {
        text: 'Fig. 9-21 (圖6)'
    },
    xAxis: {
        title: {
            text: 'ha/Ho'
        },
        tickLength: 10,
        tickInterval: 0.05,
        min: 0,   
        max: 0.25  
    },
    yAxis: {
        title: {
            text: 'Xc/Ho'
        },
        tickInterval: 0.02, 
        min: 0.15,   
        max: 0.31
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name: "Value of XC/Ho",
        data: [
            [0.0001, 0.2834],
            [0.0088, 0.279],
            [0.0175, 0.2747],
            [0.0262, 0.2703],
            [0.0348, 0.2658],
            [0.0434, 0.2613],
            [0.0521, 0.2569],
            [0.0607, 0.2523],
            [0.0693, 0.2478],
            [0.0779, 0.2432],
            [0.0865, 0.2387],
            [0.095, 0.234],
            [0.1034, 0.2291],
            [0.1117, 0.224],
            [0.1201, 0.219],
            [0.1285, 0.2141],
            [0.1367, 0.209],
            [0.1449, 0.2037],
            [0.1531, 0.1985],
            [0.1612, 0.1931],
            [0.1692, 0.1876],
            [0.1772, 0.1821],
            [0.1851, 0.1763],
            [0.1927, 0.1703],
            [0.2001, 0.164]
              ],
        marker: {
            enabled: true, 
            radius: 4, 

        }
    }]
});
var chart_9_21_d = Highcharts.chart('fig_9_21_d', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Value of YC/Ho'
    },
    subtitle: {
        text: 'Fig. 9-21 (圖7)'
    },
    xAxis: {
        title: {
            text: 'ha/Ho'
        },
        tickLength: 10,
        tickInterval: 0.05,
        min: 0,   
        max: 0.25  
    },
    yAxis: {
        title: {
            text: 'YC/Ho'
        },
        tickInterval: 0.02, 
        min: 0,   
        max: 0.14
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name: "Value of YC/Ho",
        data: [
            [0.0003, 0.1272],
            [0.1203, 0.0746],
            [0.1333, 0.0697],
            [0.1401, 0.0671],
            [0.15, 0.0634],
            [0.1604, 0.0603],
            [0.2001, 0.0482]
              ],
        marker: {
            enabled: true, 
            radius: 4, 

        }
    }]
});
var chart_9_21_e = Highcharts.chart('fig_9_21_e', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Value of R1/Ho and R2/Ho for vertical'
    },
    subtitle: {
        text: 'Fig. 9-21 (圖8)'
    },
    xAxis: {
        title: {
            text: 'ha/Ho'
        },
        tickLength: 10,
        tickInterval: 0.05,
        min: 0,   
        max: 0.25  
    },
    yAxis: {
        title: {
            text: 'R1/Ho ---------------------- R2/Ho'
        },
        tickInterval: 0.05, 
        min: 0,   
        max: 0.55
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name: 'R1',
        data: [
            [0.0005, 0.5314],
            [0.0107, 0.5256],
            [0.0204, 0.5212],
            [0.0308, 0.5161],
            [0.0404, 0.511],
            [0.0506, 0.5045],
            [0.0603, 0.4979],
            [0.0705, 0.4921],
            [0.0805, 0.4863],
            [0.0904, 0.4804],
            [0.1005, 0.4739],
            [0.1101, 0.4659],
            [0.1207, 0.4593],
            [0.1303, 0.4506],
            [0.1402, 0.44185],
            [0.1501, 0.4331],
            [0.1604, 0.4229],
            [0.17, 0.4112],
            [0.1802, 0.3988],
            [0.1901, 0.3857],
            [0.2002, 0.3719]
        ],
        marker: {
            enabled: true,
            radius: 4,
            fillColor: 'blue'
        },
        color: 'blue'
    }, {
        name: 'R2',
        data: [
            [0.0005, 0.2336],
            [0.0107, 0.2266],
            [0.0204, 0.2207],
            [0.0308, 0.2161],
            [0.0404, 0.2126],
            [0.0506, 0.2085],
            [0.0603, 0.2056],
            [0.0705, 0.2044],
            [0.0805, 0.2033],
            [0.0904, 0.2021],
            [0.1005, 0.2009],
            [0.1101, 0.1998],
            [0.1207, 0.1992],
            [0.1303, 0.198],
            [0.1402, 0.1968],
            [0.1501, 0.1968],
            [0.1604, 0.1963],
            [0.17, 0.1963],
            [0.1802, 0.1963],
            [0.1901, 0.1963],
            [0.2002, 0.1957]
        ],
        marker: {
            enabled: true,
            radius: 4,
            fillColor: '#DAA520'
        },
        color: '#DAA520'
    }]
});
var chart_ogee = Highcharts.chart('fig_ogee', {
    chart: {
        type: 'scatter',
        zoomType: 'xy',
        plotBorderWidth: 1,
    },
    title: {
        text: 'OGEE SHAPE RESULT'
    },
    xAxis: {
        tickLength: 10,
        tickInterval: 1,
        min: -5,   
        max: 7 ,
        gridLineWidth: 0.5, 
    },
    yAxis: {
        
        tickInterval: 1, 
        min: -5,   
        max: 3,
        gridLineWidth: 0.5, 
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: []
});
let lastHorizontalLine = null;

function drawPointAndLines(chart, pointX, pointY, options = {}) {
    // Default options
    const defaultOptions = {
        pointname:'point',
        pointColor: 'orange',
        pointRadius: 7,
        horizontalLineColor: 'gray',
        verticalLineColor: 'orange',
        lineWidth: 1,
        horizontalLineXRange: [0, 3.5], 
        verticalLineYRange: [3, 4],    
    };
    const config = { ...defaultOptions, ...options };

    // Draw the point
   chart.addSeries({
        name: config.pointname,
        type: 'scatter',
        color:config.pointColor,
        data: [[pointX, pointY]],
        marker: {
            radius: config.pointRadius 
        }
    });



    // Draw the horizontal line
    chart.renderer.path([
        'M', chart.xAxis[0].toPixels(config.horizontalLineXRange[0]), chart.yAxis[0].toPixels(pointY),
        'L', chart.xAxis[0].toPixels(config.horizontalLineXRange[1]), chart.yAxis[0].toPixels(pointY)
    ])
    .attr({
        stroke: config.horizontalLineColor,
        'stroke-width': config.lineWidth,
        zIndex: 4
    })
    .add();

    // Draw the vertical line
    chart.renderer.path([
        'M', chart.xAxis[0].toPixels(pointX), chart.yAxis[0].toPixels(config.verticalLineYRange[0]),
        'L', chart.xAxis[0].toPixels(pointX), chart.yAxis[0].toPixels(config.verticalLineYRange[1])
    ])
    .attr({
        stroke: config.verticalLineColor,
        'stroke-width': config.lineWidth,
        zIndex: 4
    })
    .add();
    }
function drawCircle(chart, circle_data, options = {}) {
    // Default options
    const defaultOptions = {
        pointname: 'circle',
        pointColor: 'orange',
        lineWidth: 1,
        dashStyle: 'ShortDash', // 設置為虛線
        marker: {
            enabled: true, // 隱藏數據點
            radius: 1
        }  
    };
    const config = { ...defaultOptions, ...options };

    // Draw the point
    chart.addSeries({
        name: config.pointname,
        type: 'scatter',
        plotBorderWidth: 1,
        color: config.pointColor,
        data: circle_data,
        dashStyle: config.dashStyle, // 添加虛線樣式
        marker: config.marker,
        showInLegend: true 
    });
}

function drawLine(chart, line_data, options = {}) {
    // Default options
    const defaultOptions = {
        pointname: 'line',
        pointColor: 'red',
        lineWidth: 1,
        dashStyle: 'ShortDash', // 設置為虛線
        marker: {
            enabled: false, // 隱藏數據點
        }  
    };
    const config = { ...defaultOptions, ...options };

    // Draw the point
    chart.addSeries({
        name: config.pointname,
        type: 'line',
        plotBorderWidth: 1,
        color: config.pointColor,
        data: line_data,
        dashStyle: config.dashStyle, 
        marker: config.marker
    });
}
function drawArea(chart, line_data, options = {}) {
    // Default options
    const defaultOptions = {
        pointname: 'Area',
        pointColor: 'rgba(166, 166, 166, 0.5)', // Semi-transparent black for better visibility
        lineWidth: 0,
        marker: {
            enabled: false, // Hide data points
        },
        linkedTo: null // Default to no linkage
    };
    const config = { ...defaultOptions, ...options };

    // Draw the area series
    chart.addSeries({
        name: config.pointname,
        type: 'area',
        plotBorderWidth:0,
        color: config.pointColor,
        data: line_data,
        marker: config.marker,
        linkedTo: config.linkedTo // Use the linkedTo option
    });
}

function init_chart(){
    chart_9_26 =Highcharts.chart('fig_9_26', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Value of (hd+d)/He for Supercritical'
    },
    subtitle: {
        text: 'Fig. 9-26 '
    },
    xAxis: {
        title: {
            text: 'POSITION OF DOWNSTREAM APRON (hd+d)/He'
        },
        tickLength: 10,
        tickInterval: 0.04,
    },
    yAxis: {
        title: {
            text: 'DEGREE OF SUBMERGENCE (hd/He)'
        },
        tickInterval: 0.2, 
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name:"DEGREE OF SUBMERGENCE (hd/He)",
        data: [
            [1.00, 0.33],
            [1.03, 0.39],
            [1.07, 0.45],
            [1.10, 0.51],
            [1.15, 0.56],
            [1.19, 0.62],
            [1.24, 0.68],
            [1.28, 0.73],
            [1.33, 0.79],
            [1.37, 0.85],
            [1.41, 0.91],
            [1.46, 0.96],
            [1.51, 1.02],
            [1.55, 1.08],
            [1.60, 1.13],
            [1.64, 1.19],
            [1.69, 1.24],
            [1.74, 1.30],
            [1.79, 1.36],
            [1.83, 1.41],
            [1.88, 1.47],
            [1.93, 1.53],
            [1.98, 1.58],
            [2.03, 1.64],
            [2.08, 1.70]
        ]
    }]
    });
    chart_9_23 =Highcharts.chart('fig_9_23', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Coefficient of Co (in feet)'
    },
    subtitle: {
        text: 'Fig. 9-23 '
    },
    xAxis: {
        title: {
            text: 'P/Ho'
        },
        tickLength: 10,
        tickInterval: 0.1,
    },
    yAxis: {
        title: {
            text: 'Value Of Co'
        },
        tickInterval: 0.2, 
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name:"Value Of Co",
        data: [
        [0.0, 3.08], [0.1, 3.3816], [0.2, 3.559], [0.3, 3.684], [0.4, 3.7566],
        [0.5, 3.7965], [0.6, 3.8263], [0.7, 3.8483], [0.8, 3.8644], [0.9, 3.8763],
        [1.0, 3.8874], [1.1, 3.8964], [1.2, 3.9031], [1.3, 3.9083], [1.4, 3.9136],
        [1.5, 3.9174], [1.6, 3.922], [1.7, 3.9257], [1.8, 3.928], [1.9, 3.9317],
        [2.0, 3.9354], [2.1, 3.9383], [2.2, 3.9398], [2.3, 3.9427], [2.4, 3.9441],
        [2.5, 3.9449], [2.6, 3.9477], [2.7, 3.9484], [2.8, 3.9483], [2.9, 3.9482]]
    }]
    });
    chart_9_27 = Highcharts.chart('fig_9_27', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Correction Coefficient of Cs'
    },
    subtitle: {
        text: 'Fig. 9-27 '
    },
    xAxis: {
        title: {
            text: '(hd+d)/He'
        },
        tickLength: 10,
        tickInterval: 0.1,
        min: 1,   
        max: 1.7  
    },
    yAxis: {
        title: {
            text: 'Cs/Co'
        },
        tickInterval: 0.05, 
        min: 0.76,   
        max: 1.01
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name: "DEGREE OF SUBMERGENCE (hd/He)",
        data: [
            [1, 0.7705],
            [1.0089, 0.7793],
            [1.0303, 0.7996],
            [1.0488, 0.8148],
            [1.0571, 0.8207],
            [1.0869, 0.8414],
            [1.0991, 0.8481],
            [1.1198, 0.8605],
            [1.1488, 0.876],
            [1.1557, 0.8796],
            [1.1748, 0.8889],
            [1.1989, 0.9001],
            [1.2229, 0.9109],
            [1.249, 0.9209],
            [1.2743, 0.9304],
            [1.2996, 0.9386],
            [1.3069, 0.9404],
            [1.349, 0.9526],
            [1.3841, 0.961],
            [1.4004, 0.9647],
            [1.4494, 0.9741],
            [1.4886, 0.981],
            [1.5009, 0.9829],
            [1.5499, 0.9898],
            [1.6002, 0.9946],
            [1.6513, 0.9984],
            [1.6786, 1],
            [10, 1]
        ],
        marker: {
            enabled: true, 
            radius: 4, 

        }
    }]
    });
    chart_9_21_a = Highcharts.chart('fig_9_21_a', {
    chart: {
        type: 'line'
    },
    title: {
        text: 'Value of K'
    },
    subtitle: {
        text: 'Fig. 9-21 (圖4)'
    },
    xAxis: {
        title: {
            text: 'ha/Ho'
        },
        tickLength: 10,
        tickInterval: 0.05,
        min: 0,   
        max: 0.25  
    },
    yAxis: {
        title: {
            text: 'k'
        },
        tickInterval: 0.01, 
        min: 0.44,   
        max: 0.52
    },
    credits: {
        enabled: false
    },
    legend: {
        enabled: false 
    },
    series: [{
        name: "Value of K",
        data: 
            [
                [0.0004, 0.499],
                [0.0051, 0.5005],
                [0.0099, 0.5019],
                [0.0199, 0.5042],
                [0.03, 0.506],
                [0.0398, 0.5081],
                [0.0501, 0.51],
                [0.0599, 0.5118],
                [0.07, 0.5125],
                [0.0798, 0.5125],
                [0.0898, 0.5118],
                [0.1001, 0.5109],
                [0.1097, 0.5091],
                [0.12, 0.5067],
                [0.1299, 0.5035],
                [0.1402, 0.4998],
                [0.1501, 0.4945],
                [0.1597, 0.4901],
                [0.1701, 0.485],
                [0.1786, 0.4799],
                [0.1805, 0.4788],
                [0.19, 0.473],
                [0.1998, 0.4658]
              ]
        ,
        marker: {
            enabled: true, 
            radius: 4, 

        }
    }]
    });
    chart_9_21_b = Highcharts.chart('fig_9_21_b', {
        chart: {
            type: 'line'
        },
        title: {
            text: 'Value of n'
        },
        subtitle: {
            text: 'Fig. 9-21 (圖5)'
        },
        xAxis: {
            title: {
                text: 'ha/Ho'
            },
            tickLength: 10,
            tickInterval: 0.05,
            min: 0,   
            max: 0.25  
        },
        yAxis: {
            title: {
                text: 'n'
            },
            tickInterval: 0.02, 
            min: 1.74,   
            max: 1.9
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: false 
        },
        series: [{
            name: "Value of XC/Ho",
            data: [
                    [0, 1.8728],
                    [0.0098, 1.8666],
                    [0.0198, 1.8615],
                    [0.0298, 1.8564],
                    [0.0397, 1.8518],
                    [0.0499, 1.8479],
                    [0.0597, 1.8442],
                    [0.0699, 1.8409],
                    [0.0795, 1.8382],
                    [0.0895, 1.8363],
                    [0.0995, 1.8347],
                    [0.1096, 1.8333],
                    [0.1196, 1.8317],
                    [0.1295, 1.8312],
                    [0.1399, 1.8312],
                    [0.1498, 1.8305],
                    [0.1599, 1.8312],
                    [0.1698, 1.8321],
                    [0.1797, 1.8338],
                    [0.1899, 1.8354],
                    [0.1997, 1.837]  
                ],
            marker: {
                enabled: true, 
                radius: 4, 

            }
        }]
    });
    chart_9_21_c = Highcharts.chart('fig_9_21_c', {
        chart: {
            type: 'line'
        },
        title: {
            text: 'Value of XC/Ho'
        },
        subtitle: {
            text: 'Fig. 9-21 (圖6)'
        },
        xAxis: {
            title: {
                text: 'ha/Ho'
            },
            tickLength: 10,
            tickInterval: 0.05,
            min: 0,   
            max: 0.25  
        },
        yAxis: {
            title: {
                text: 'Xc/Ho'
            },
            tickInterval: 0.02, 
            min: 0.15,   
            max: 0.31
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: false 
        },
        series: [{
            name: "Value of XC/Ho",
            data: [
                [0.0001, 0.2834],
                [0.0088, 0.279],
                [0.0175, 0.2747],
                [0.0262, 0.2703],
                [0.0348, 0.2658],
                [0.0434, 0.2613],
                [0.0521, 0.2569],
                [0.0607, 0.2523],
                [0.0693, 0.2478],
                [0.0779, 0.2432],
                [0.0865, 0.2387],
                [0.095, 0.234],
                [0.1034, 0.2291],
                [0.1117, 0.224],
                [0.1201, 0.219],
                [0.1285, 0.2141],
                [0.1367, 0.209],
                [0.1449, 0.2037],
                [0.1531, 0.1985],
                [0.1612, 0.1931],
                [0.1692, 0.1876],
                [0.1772, 0.1821],
                [0.1851, 0.1763],
                [0.1927, 0.1703],
                [0.2001, 0.164]
                ],
            marker: {
                enabled: true, 
                radius: 4, 

            }
        }]
    });
    chart_9_21_d = Highcharts.chart('fig_9_21_d', {
        chart: {
            type: 'line'
        },
        title: {
            text: 'Value of YC/Ho'
        },
        subtitle: {
            text: 'Fig. 9-21 (圖7)'
        },
        xAxis: {
            title: {
                text: 'ha/Ho'
            },
            tickLength: 10,
            tickInterval: 0.05,
            min: 0,   
            max: 0.25  
        },
        yAxis: {
            title: {
                text: 'YC/Ho'
            },
            tickInterval: 0.02, 
            min: 0,   
            max: 0.14
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: false 
        },
        series: [{
            name: "Value of YC/Ho",
            data: [
                [0.0003, 0.1272],
                [0.1203, 0.0746],
                [0.1333, 0.0697],
                [0.1401, 0.0671],
                [0.15, 0.0634],
                [0.1604, 0.0603],
                [0.2001, 0.0482]
                ],
            marker: {
                enabled: true, 
                radius: 4, 

            }
        }]
    });
    chart_9_21_e = Highcharts.chart('fig_9_21_e', {
        chart: {
            type: 'line'
        },
        title: {
            text: 'Value of R1/Ho and R2/Ho for vertical'
        },
        subtitle: {
            text: 'Fig. 9-21 (圖8)'
        },
        xAxis: {
            title: {
                text: 'ha/Ho'
            },
            tickLength: 10,
            tickInterval: 0.05,
            min: 0,   
            max: 0.25  
        },
        yAxis: {
            title: {
                text: 'R1/Ho ---------------------- R2/Ho'
            },
            tickInterval: 0.05, 
            min: 0,   
            max: 0.55
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: false 
        },
        series: [{
            name: 'R1',
            data: [
                [0.0005, 0.5314],
                [0.0107, 0.5256],
                [0.0204, 0.5212],
                [0.0308, 0.5161],
                [0.0404, 0.511],
                [0.0506, 0.5045],
                [0.0603, 0.4979],
                [0.0705, 0.4921],
                [0.0805, 0.4863],
                [0.0904, 0.4804],
                [0.1005, 0.4739],
                [0.1101, 0.4659],
                [0.1207, 0.4593],
                [0.1303, 0.4506],
                [0.1402, 0.44185],
                [0.1501, 0.4331],
                [0.1604, 0.4229],
                [0.17, 0.4112],
                [0.1802, 0.3988],
                [0.1901, 0.3857],
                [0.2002, 0.3719]
            ],
            marker: {
                enabled: true,
                radius: 4,
                fillColor: 'blue'
            },
            color: 'blue'
        }, {
            name: 'R2',
            data: [
                [0.0005, 0.2336],
                [0.0107, 0.2266],
                [0.0204, 0.2207],
                [0.0308, 0.2161],
                [0.0404, 0.2126],
                [0.0506, 0.2085],
                [0.0603, 0.2056],
                [0.0705, 0.2044],
                [0.0805, 0.2033],
                [0.0904, 0.2021],
                [0.1005, 0.2009],
                [0.1101, 0.1998],
                [0.1207, 0.1992],
                [0.1303, 0.198],
                [0.1402, 0.1968],
                [0.1501, 0.1968],
                [0.1604, 0.1963],
                [0.17, 0.1963],
                [0.1802, 0.1963],
                [0.1901, 0.1963],
                [0.2002, 0.1957]
            ],
            marker: {
                enabled: true,
                radius: 4,
                fillColor: '#DAA520'
            },
            color: '#DAA520'
        }]
    });
    chart_ogee = Highcharts.chart('fig_ogee', {
        chart: {
            type: 'scatter',
            zoomType: 'xy',
            plotBorderWidth: 1,
        },
        title: {
            text: 'OGEE SHAPE RESULT'
        },
        xAxis: {
            tickLength: 10,
            tickInterval: 1,
            min: -5,   
            max: 7 ,
            gridLineWidth: 0.5, 
        },
        yAxis: {
            
            tickInterval: 1, 
            min: -5,   
            max: 3,
            gridLineWidth: 0.5, 
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: false 
        },
        series: []
    });
}



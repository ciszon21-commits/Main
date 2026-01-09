async function update_selection_transition(){
    const selectedValue = document.getElementById("selection_transition").value;
    console.log(`選了 ${selectedValue} 號`);
    const S2 = document.getElementById('selection_transition_S2')
    const B1 = document.getElementById('selection_transition_B1')
    const B3 = document.getElementById('selection_transition_B3')
    const Z2 = document.getElementById('selection_transition_Z2')
    const Z3 = document.getElementById('selection_transition_Z3')
    const deltaZ = document.getElementById('selection_transition_deltaZ')
    const L2min = document.getElementById('selection_transition_L2min')
    const L2_use = document.getElementById('selection_transition_L2_use')
    const Z3_use = document.getElementById('selection_transition_Z3_use')
    if (transition_result === undefined) {
        alert("請填完所有輸入值");
      return;
    }
    const result = transition_result.find(item => item.Trial === parseInt(selectedValue));
    S2.textContent=(result.S*100).toFixed(0)+ '%'
    B1.textContent=result.b2.toFixed(2)
    B3.textContent=result.b3.toFixed(2)
    Z2.textContent=result.Z2.toFixed(2)
    Z3.textContent=result.Z3.toFixed(2)
    deltaZ.textContent=result.deltaZ.toFixed(2)
    L2min.textContent=result.L.toFixed(2)
    L2_use.textContent=ceilToMultiple(result.L, 5)
    Z3_use.textContent=(result.Z2-result.S*ceilToMultiple(result.L, 5)).toFixed(2)
    B1.style.color='black'
    B3.style.color='black'
    Z2.style.color='black'
    Z3.style.color='black'
    deltaZ.style.color='black'
    L2min.style.color='black'
}
async function draw_transition(){
    init_transition_chart()
    drawtransition()
}
async function showWaterlevel(){
    document.getElementById('transition_main').classList.add('d-none');
    document.getElementById('waterlevel_main').classList.remove('d-none');
    const Tunnel_length = document.getElementById('Tunnel_length_Waterlevel')
    const Interval = document.getElementById('Interval_Waterlevel')
    const Tunnel_length_ = parseFloat(document.getElementById('Tunnel_length').value)
    const Interval_ = parseFloat(document.getElementById('Interval').value)
    Tunnel_length.textContent=Tunnel_length_
    Interval.textContent=Interval_
}
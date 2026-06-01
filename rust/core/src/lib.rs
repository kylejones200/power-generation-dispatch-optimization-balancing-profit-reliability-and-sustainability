//! Merit-order economic dispatch total cost.

pub fn economic_dispatch_cost(mw_demand: f64, unit_mw: &[f64], unit_cost: &[f64]) -> f64 {
    assert_eq!(unit_mw.len(), unit_cost.len());
    let mut remaining = mw_demand;
    let mut total = 0.0;
    let mut order: Vec<usize> = (0..unit_cost.len()).collect();
    order.sort_by(|&a, &b| unit_cost[a].partial_cmp(&unit_cost[b]).unwrap());
    for idx in order {
        let dispatch = remaining.min(unit_mw[idx]).max(0.0);
        total += dispatch * unit_cost[idx];
        remaining -= dispatch;
        if remaining <= 1e-12 {
            break;
        }
    }
    total
}

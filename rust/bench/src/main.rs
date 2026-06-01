use power_generation_dispatch_optimization_balancing_profit_reliability_and_sustainability_core::economic_dispatch_cost;

fn main() {
    let mw = vec![100.0, 80.0, 60.0, 40.0];
    let cost = vec![25.0, 30.0, 45.0, 60.0];
    for _ in 0..50000 {
        let _ = economic_dispatch_cost(200.0, &mw, &cost);
    }
}

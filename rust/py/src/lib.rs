use power_generation_dispatch_optimization_balancing_profit_reliability_and_sustainability_core::economic_dispatch_cost;
use numpy::PyReadonlyArray1;
use pyo3::prelude::*;

#[pyfunction]
fn economic_dispatch_cost_py(
    mw_demand: f64,
    unit_mw: PyReadonlyArray1<f64>,
    unit_cost: PyReadonlyArray1<f64>,
) -> PyResult<f64> {
    Ok(economic_dispatch_cost(mw_demand, unit_mw.as_slice()?, unit_cost.as_slice()?))
}

#[pyfunction]
#[pyo3(signature = (mw_demand, unit_mw, unit_cost, iterations=50_000))]
fn bench_kernel_py(
    mw_demand: f64,
    unit_mw: PyReadonlyArray1<f64>,
    unit_cost: PyReadonlyArray1<f64>,
    iterations: usize,
) -> PyResult<f64> {
    let mw = unit_mw.as_slice()?.to_vec();
    let cost = unit_cost.as_slice()?.to_vec();
    let start = std::time::Instant::now();
    for _ in 0..iterations {
        let _ = economic_dispatch_cost(mw_demand, &mw, &cost);
    }
    Ok(start.elapsed().as_secs_f64())
}

#[pymodule]
fn power_generation_dispatch_optimization_balancing_profit_reliability_and_sustainability_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(economic_dispatch_cost_py, m)?)?;
    m.add_function(wrap_pyfunction!(bench_kernel_py, m)?)?;
    Ok(())
}

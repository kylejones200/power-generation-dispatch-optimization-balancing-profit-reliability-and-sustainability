"""
Python code extracted from 03_generation_dispatch_blog.md

This code was automatically extracted from the markdown file.
You may need to adjust imports and add necessary dependencies.
"""
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s', stream=sys.stderr, force=True)
logger = logging.getLogger(__name__)

def define_generation_sources():
    """
    Define characteristics of different generation sources.
    
    Each source has unique cost structures, capabilities, and constraints
    that determine optimal dispatch decisions.
    """
    sources = {'coal': {'capacity_mw': 800, 'min_output_mw': 400, 'variable_cost_mwh': 35.0, 'startup_cost': 25000, 'shutdown_cost': 5000, 'ramp_rate_mw_hour': 100, 'emissions_co2_ton_mwh': 0.95, 'min_up_time_hours': 8, 'min_down_time_hours': 4}, 'natural_gas_combined_cycle': {'capacity_mw': 600, 'min_output_mw': 200, 'variable_cost_mwh': 45.0, 'startup_cost': 8000, 'shutdown_cost': 1000, 'ramp_rate_mw_hour': 200, 'emissions_co2_ton_mwh': 0.55, 'min_up_time_hours': 2, 'min_down_time_hours': 1}, 'natural_gas_peaker': {'capacity_mw': 250, 'min_output_mw': 50, 'variable_cost_mwh': 85.0, 'startup_cost': 1500, 'shutdown_cost': 500, 'ramp_rate_mw_hour': 250, 'emissions_co2_ton_mwh': 0.65, 'min_up_time_hours': 0.5, 'min_down_time_hours': 0.25}, 'wind': {'capacity_mw': 500, 'min_output_mw': 0, 'variable_cost_mwh': 0.0, 'startup_cost': 0, 'shutdown_cost': 0, 'ramp_rate_mw_hour': 500, 'emissions_co2_ton_mwh': 0.0, 'min_up_time_hours': 0, 'min_down_time_hours': 0, 'variability': True, 'forecast_accuracy': 0.85}, 'solar': {'capacity_mw': 300, 'min_output_mw': 0, 'variable_cost_mwh': 0.0, 'startup_cost': 0, 'shutdown_cost': 0, 'ramp_rate_mw_hour': 300, 'emissions_co2_ton_mwh': 0.0, 'min_up_time_hours': 0, 'min_down_time_hours': 0, 'variability': True, 'forecast_accuracy': 0.9}}
    return sources
sources = define_generation_sources()
logger.info('Generation Source Economics:')
for name, specs in sources.items():
    logger.info(f'\n{name.upper()}:')
    logger.info(f"  Capacity: {specs['capacity_mw']} MW")
    logger.info(f"  Variable Cost: ${specs['variable_cost_mwh']:.2f}/MWh")
    logger.info(f"  CO2 Emissions: {specs['emissions_co2_ton_mwh']:.2f} tons/MWh")

def calculate_merit_order_dispatch(demand_mw, generation_sources, hour):
    """
    Calculate optimal economic dispatch using merit order.
    
    Dispatches generators from lowest to highest marginal cost
    until total demand is satisfied.
    """
    available_gen = []
    for source_name, specs in generation_sources.items():
        if source_name == 'solar':
            capacity = np.where(6 <= hour <= 18, specs['capacity_mw'] * (0.1 + 0.9 * np.sin((hour - 6) * np.pi / 12)), 0)
        capacity = np.where(source_name == 'wind', specs['capacity_mw'] * 0.7, specs['capacity_mw'])
        if capacity > 0:
            available_gen.append({'source': source_name, 'capacity_mw': capacity, 'min_output_mw': specs.get('min_output_mw', 0), 'variable_cost_mwh': specs['variable_cost_mwh'], 'emissions_co2_ton_mwh': specs['emissions_co2_ton_mwh']})
    available_gen.sort(key=lambda x: x['variable_cost_mwh'])
    dispatch_schedule = []
    remaining_demand = demand_mw
    total_cost = 0
    total_emissions = 0
    for gen in available_gen:
        if remaining_demand <= 0:
            break
        dispatch_mw = min(gen['capacity_mw'], remaining_demand)
        if dispatch_mw < gen['min_output_mw'] and dispatch_mw > 0:
            dispatch_mw = gen['min_output_mw']
        if dispatch_mw > 0:
            cost = dispatch_mw * gen['variable_cost_mwh']
            emissions = dispatch_mw * gen['emissions_co2_ton_mwh']
            dispatch_schedule.append({'source': gen['source'], 'output_mw': dispatch_mw, 'cost': cost, 'emissions_tons': emissions})
            remaining_demand -= dispatch_mw
            total_cost += cost
            total_emissions += emissions
    marginal_price = max([d['cost'] / d['output_mw'] for d in dispatch_schedule]) if dispatch_schedule else 0
    return {'dispatch': dispatch_schedule, 'total_demand_met': demand_mw - remaining_demand, 'total_cost': total_cost, 'total_emissions_tons': total_emissions, 'marginal_price_mwh': marginal_price, 'renewable_percentage': sum((d['output_mw'] for d in dispatch_schedule if d['source'] in ['wind', 'solar'])) / (demand_mw - remaining_demand) * 100 if remaining_demand < demand_mw else 0}
sources = define_generation_sources()
demand = 1800
hour = 14
dispatch_result = calculate_merit_order_dispatch(demand, sources, hour)
logger.info(f'\nEconomic Dispatch for {demand} MW demand at hour {hour}:')
logger.info(f"  Total Cost: ${dispatch_result['total_cost']:,.2f}")
logger.info(f"  Total Emissions: {dispatch_result['total_emissions_tons']:.1f} tons CO2")
logger.info(f"  Marginal Price: ${dispatch_result['marginal_price_mwh']:.2f}/MWh")
logger.info(f"  Renewable %: {dispatch_result['renewable_percentage']:.1f}%")
logger.info('\nDispatch by Source:')
for unit in dispatch_result['dispatch']:
    logger.info(f"  {unit['source']}: {unit['output_mw']:.0f} MW")

def optimize_unit_commitment(demand_profile_24h, generation_sources):
    """
    Optimize which units to commit over 24-hour period.
    
    Considers startup costs, minimum run times, and ramping constraints
    to minimize total production cost.
    """
    unit_states = {name: {'online': False, 'hours_online': 0, 'hours_offline': 24} for name in generation_sources.keys()}
    commitment_schedule = []
    total_cost = 0
    for hour, demand_mw in enumerate(demand_profile_24h):
        hour_dispatch = {'hour': hour, 'demand': demand_mw, 'units_online': [], 'generation': [], 'hour_cost': 0}
        for source_name, specs in generation_sources.items():
            if specs.get('variability', False):
                continue
            current_state = unit_states[source_name]
            should_be_online = np.select([source_name == 'coal', source_name == 'natural_gas_combined_cycle', source_name == 'natural_gas_peaker'], [demand_mw > 800, demand_mw > 1200, demand_mw > 1600], default=True)
            if current_state['online']:
                if current_state['hours_online'] < specs['min_up_time_hours']:
                    should_be_online = True
            elif current_state['hours_offline'] < specs['min_down_time_hours']:
                should_be_online = False
            if should_be_online and (not current_state['online']):
                hour_dispatch['hour_cost'] += specs['startup_cost']
                total_cost += specs['startup_cost']
                current_state['online'] = True
                current_state['hours_online'] = 1
                current_state['hours_offline'] = 0
            elif not should_be_online and current_state['online']:
                hour_dispatch['hour_cost'] += specs['shutdown_cost']
                total_cost += specs['shutdown_cost']
                current_state['online'] = False
                current_state['hours_offline'] = 1
                current_state['hours_online'] = 0
            elif current_state['online']:
                current_state['hours_online'] += 1
            else:
                current_state['hours_offline'] += 1
            if current_state['online']:
                hour_dispatch['units_online'].append(source_name)
        online_sources = {name: specs for name, specs in generation_sources.items() if unit_states[name]['online'] or specs.get('variability', False)}
        dispatch = calculate_merit_order_dispatch(demand_mw, online_sources, hour)
        hour_dispatch['generation'] = dispatch['dispatch']
        hour_dispatch['hour_cost'] += dispatch['total_cost']
        total_cost += dispatch['total_cost']
        commitment_schedule.append(hour_dispatch)
    return {'schedule': commitment_schedule, 'total_24h_cost': total_cost, 'avg_hourly_cost': total_cost / 24}
demand_profile = []
for hour in range(24):
    base_demand = np.select([6 <= hour <= 9, 17 <= hour <= 21, 22 <= hour or hour <= 5], [1850, 2100, 1400], default=1650)
    demand_profile.append(base_demand + np.random.randint(-50, 50))
commitment = optimize_unit_commitment(demand_profile, sources)
logger.info(f'\n24-Hour Unit Commitment Optimization:')
logger.info(f"  Total Daily Cost: ${commitment['total_24h_cost']:,.2f}")
logger.info(f"  Average Hourly Cost: ${commitment['avg_hourly_cost']:,.2f}")
logger.info(f'\nPeak Hour (19:00) Dispatch:')
peak_hour = commitment['schedule'][19]
logger.info(f"  Demand: {peak_hour['demand']} MW")
logger.info(f"  Units Online: {len(peak_hour['units_online'])}")
for unit in peak_hour['generation']:
    logger.info(f"    {unit['source']}: {unit['output_mw']:.0f} MW at ${unit['cost']:,.0f}")

def dispatch_with_renewable_uncertainty(demand_mw, wind_forecast_mw, solar_forecast_mw, generation_sources, hour):
    """
    Dispatch considering renewable forecast uncertainty.
    
    Maintains reserve margins to handle renewable forecast errors
    while maximizing renewable utilization.
    """
    wind_actual = wind_forecast_mw * (1 + np.random.uniform(-0.15, 0.15))
    solar_actual = solar_forecast_mw * (1 + np.random.uniform(-0.1, 0.1))
    wind_actual = max(0, min(wind_actual, generation_sources['wind']['capacity_mw']))
    solar_actual = max(0, min(solar_actual, generation_sources['solar']['capacity_mw']))
    renewable_generation = wind_actual + solar_actual
    conventional_demand = demand_mw - renewable_generation
    reserve_margin = max(demand_mw * 0.12, 200)
    total_conventional_needed = conventional_demand + reserve_margin
    conventional_sources = {k: v for k, v in generation_sources.items() if k not in ['wind', 'solar']}
    dispatch = calculate_merit_order_dispatch(total_conventional_needed, conventional_sources, hour)
    actual_cost = renewable_generation * 0 + conventional_demand * (dispatch['total_cost'] / total_conventional_needed)
    emissions_rate_conventional = 0.65
    emissions_saved = renewable_generation * emissions_rate_conventional
    return {'demand_mw': demand_mw, 'renewable_generation_mw': renewable_generation, 'renewable_percentage': renewable_generation / demand_mw * 100, 'conventional_generation_mw': conventional_demand, 'reserve_mw': reserve_margin, 'actual_cost': actual_cost, 'emissions_saved_tons': emissions_saved, 'wind_forecast_error_pct': (wind_actual - wind_forecast_mw) / wind_forecast_mw * 100 if wind_forecast_mw > 0 else 0, 'solar_forecast_error_pct': (solar_actual - solar_forecast_mw) / solar_forecast_mw * 100 if solar_forecast_mw > 0 else 0}
result = dispatch_with_renewable_uncertainty(demand_mw=1800, wind_forecast_mw=350, solar_forecast_mw=250, generation_sources=sources, hour=14)
logger.info('\nRenewable Integration Analysis:')
logger.info(f"  Total Demand: {result['demand_mw']} MW")
logger.info(f"  Renewable Generation: {result['renewable_generation_mw']:.0f} MW ({result['renewable_percentage']:.1f}%)")
logger.info(f"  Conventional Generation: {result['conventional_generation_mw']:.0f} MW")
logger.info(f"  Reserve Margin: {result['reserve_mw']:.0f} MW")
logger.info(f"  Total Cost: ${result['actual_cost']:,.2f}")
logger.info(f"  Emissions Saved: {result['emissions_saved_tons']:.1f} tons CO2")
logger.info(f"  Wind Forecast Error: {result['wind_forecast_error_pct']:.1f}%")
logger.info(f"  Solar Forecast Error: {result['solar_forecast_error_pct']:.1f}%")

def dispatch_with_emissions_constraint(demand_profile_24h, generation_sources, daily_emissions_limit_tons):
    """
    Optimize dispatch subject to daily emissions constraint.
    
    Balances cost minimization with emissions compliance,
    potentially dispatching higher-cost, lower-emission units.
    """
    schedule = []
    cumulative_emissions = 0
    total_cost = 0
    for hour, demand_mw in enumerate(demand_profile_24h):
        hours_remaining = 24 - hour
        emissions_budget = daily_emissions_limit_tons - cumulative_emissions
        emissions_budget_per_hour = emissions_budget / hours_remaining if hours_remaining > 0 else 0
        emissions_penalty = 50
        available_sources = {}
        for name, specs in generation_sources.items():
            modified_specs = specs.copy()
            modified_specs['variable_cost_mwh'] = specs['variable_cost_mwh'] + specs['emissions_co2_ton_mwh'] * emissions_penalty
            available_sources[name] = modified_specs
        dispatch = calculate_merit_order_dispatch(demand_mw, available_sources, hour)
        if cumulative_emissions + dispatch['total_emissions_tons'] > daily_emissions_limit_tons:
            logger.info(f'  Hour {hour}: Emissions constraint binding, adjusting dispatch')
        cumulative_emissions += dispatch['total_emissions_tons']
        total_cost += dispatch['total_cost']
        schedule.append({'hour': hour, 'demand': demand_mw, 'dispatch': dispatch, 'hour_emissions': dispatch['total_emissions_tons'], 'cumulative_emissions': cumulative_emissions, 'emissions_budget_remaining': daily_emissions_limit_tons - cumulative_emissions})
    return {'schedule': schedule, 'total_cost': total_cost, 'total_emissions': cumulative_emissions, 'emissions_limit': daily_emissions_limit_tons, 'emissions_utilization_pct': cumulative_emissions / daily_emissions_limit_tons * 100}
emissions_constrained = dispatch_with_emissions_constraint(demand_profile, sources, daily_emissions_limit_tons=25000)
logger.info('\nEmissions-Constrained Dispatch:')
logger.info(f"  Total Daily Cost: ${emissions_constrained['total_cost']:,.2f}")
logger.info(f"  Total Emissions: {emissions_constrained['total_emissions']:.0f} tons CO2")
logger.info(f"  Emissions Limit: {emissions_constrained['emissions_limit']:.0f} tons CO2")
logger.info(f"  Utilization: {emissions_constrained['emissions_utilization_pct']:.1f}%")
'\nDefine characteristics of different generation sources.\n\nEach source has unique cost structures, capabilities, and constraints\nthat determine optimal dispatch decisions.\n'
sources = {'coal': {'capacity_mw': 800, 'min_output_mw': 400, 'variable_cost_mwh': 35.0, 'startup_cost': 25000, 'shutdown_cost': 5000, 'ramp_rate_mw_hour': 100, 'emissions_co2_ton_mwh': 0.95, 'min_up_time_hours': 8, 'min_down_time_hours': 4}, 'natural_gas_combined_cycle': {'capacity_mw': 600, 'min_output_mw': 200, 'variable_cost_mwh': 45.0, 'startup_cost': 8000, 'shutdown_cost': 1000, 'ramp_rate_mw_hour': 200, 'emissions_co2_ton_mwh': 0.55, 'min_up_time_hours': 2, 'min_down_time_hours': 1}, 'natural_gas_peaker': {'capacity_mw': 250, 'min_output_mw': 50, 'variable_cost_mwh': 85.0, 'startup_cost': 1500, 'shutdown_cost': 500, 'ramp_rate_mw_hour': 250, 'emissions_co2_ton_mwh': 0.65, 'min_up_time_hours': 0.5, 'min_down_time_hours': 0.25}, 'wind': {'capacity_mw': 500, 'min_output_mw': 0, 'variable_cost_mwh': 0.0, 'startup_cost': 0, 'shutdown_cost': 0, 'ramp_rate_mw_hour': 500, 'emissions_co2_ton_mwh': 0.0, 'min_up_time_hours': 0, 'min_down_time_hours': 0, 'variability': True, 'forecast_accuracy': 0.85}, 'solar': {'capacity_mw': 300, 'min_output_mw': 0, 'variable_cost_mwh': 0.0, 'startup_cost': 0, 'shutdown_cost': 0, 'ramp_rate_mw_hour': 300, 'emissions_co2_ton_mwh': 0.0, 'min_up_time_hours': 0, 'min_down_time_hours': 0, 'variability': True, 'forecast_accuracy': 0.9}}
return sources
logger.info(f'\n{name.upper()}:')
logger.info(f"  Capacity: {specs['capacity_mw']} MW")
logger.info(f"  Variable Cost: ${specs['variable_cost_mwh']:.2f}/MWh")
logger.info(f"  CO2 Emissions: {specs['emissions_co2_ton_mwh']:.2f} tons/MWh")
available_gen = []
for source_name, specs in generation_sources.items():
    pass
if source_name == 'solar':
    pass
if 6 <= hour <= 18:
    capacity = specs['capacity_mw'] * (0.1 + 0.9 * np.sin((hour - 6) * np.pi / 12))
    capacity = 0
capacity = specs['capacity_mw'] * 0.7
available_gen.sort(key=lambda x: x['variable_cost_mwh'])
dispatch_schedule = []
remaining_demand = demand_mw
total_cost = 0
total_emissions = 0
for gen in available_gen:
    if remaining_demand <= 0:
        break
dispatch_mw = min(gen['capacity_mw'], remaining_demand)
if dispatch_mw < gen['min_output_mw'] and dispatch_mw > 0:
    dispatch_mw = gen['min_output_mw']
    cost = dispatch_mw * gen['variable_cost_mwh']
    emissions = dispatch_mw * gen['emissions_co2_ton_mwh']
    dispatch_schedule.append({'source': gen['source'], 'output_mw': dispatch_mw, 'cost': cost, 'emissions_tons': emissions})
    remaining_demand -= dispatch_mw
    total_cost += cost
    total_emissions += emissions
marginal_price = max([d['cost'] / d['output_mw'] for d in dispatch_schedule]) if dispatch_schedule else 0
return {'dispatch': dispatch_schedule, 'total_demand_met': demand_mw - remaining_demand, 'total_cost': total_cost, 'total_emissions_tons': total_emissions, 'marginal_price_mwh': marginal_price, 'renewable_percentage': sum((d['output_mw'] for d in dispatch_schedule if d['source'] in ['wind', 'solar'])) / (demand_mw - remaining_demand) * 100 if remaining_demand < demand_mw else 0}
logger.info(f"  {unit['source']}: {unit['output_mw']:.0f} MW")
unit_states = {name: {'online': False, 'hours_online': 0, 'hours_offline': 24} for name in generation_sources.keys()}
commitment_schedule = []
total_cost = 0
for hour, demand_mw in enumerate(demand_profile_24h):
    hour_dispatch = {'hour': hour, 'demand': demand_mw, 'units_online': [], 'generation': [], 'hour_cost': 0}
if specs.get('variability', False):
    continue
if source_name == 'coal':
    should_be_online = demand_mw > 800
    should_be_online = demand_mw > 1200
    should_be_online = demand_mw > 1600
    should_be_online = True
if current_state['online']:
    if current_state['hours_online'] < specs['min_up_time_hours']:
        should_be_online = True
    if current_state['hours_offline'] < specs['min_down_time_hours']:
        should_be_online = False
hour_dispatch['hour_cost'] += specs['startup_cost']
hour_dispatch['hour_cost'] += specs['shutdown_cost']
online_sources = {name: specs for name, specs in generation_sources.items() if unit_states[name]['online'] or specs.get('variability', False)}
return {'schedule': commitment_schedule, 'total_24h_cost': total_cost, 'avg_hourly_cost': total_cost / 24}
base_demand = np.select([6 <= hour <= 9, 17 <= hour <= 21, 22 <= hour or hour <= 5], [1850, 2100, 1400], default=1650)
demand_profile.append(base_demand + np.random.randint(-50, 50))
logger.info(f"    {unit['source']}: {unit['output_mw']:.0f} MW at ${unit['cost']:,.0f}")
wind_actual = wind_forecast_mw * (1 + np.random.uniform(-0.15, 0.15))
solar_actual = solar_forecast_mw * (1 + np.random.uniform(-0.1, 0.1))
wind_actual = max(0, min(wind_actual, generation_sources['wind']['capacity_mw']))
solar_actual = max(0, min(solar_actual, generation_sources['solar']['capacity_mw']))
renewable_generation = wind_actual + solar_actual
conventional_demand = demand_mw - renewable_generation
reserve_margin = max(demand_mw * 0.12, 200)
total_conventional_needed = conventional_demand + reserve_margin
conventional_sources = {k: v for k, v in generation_sources.items() if k not in ['wind', 'solar']}
dispatch = calculate_merit_order_dispatch(total_conventional_needed, conventional_sources, hour)
actual_cost = renewable_generation * 0 + conventional_demand * (dispatch['total_cost'] / total_conventional_needed)
emissions_rate_conventional = 0.65
emissions_saved = renewable_generation * emissions_rate_conventional
return {'demand_mw': demand_mw, 'renewable_generation_mw': renewable_generation, 'renewable_percentage': renewable_generation / demand_mw * 100, 'conventional_generation_mw': conventional_demand, 'reserve_mw': reserve_margin, 'actual_cost': actual_cost, 'emissions_saved_tons': emissions_saved, 'wind_forecast_error_pct': (wind_actual - wind_forecast_mw) / wind_forecast_mw * 100 if wind_forecast_mw > 0 else 0, 'solar_forecast_error_pct': (solar_actual - solar_forecast_mw) / solar_forecast_mw * 100 if solar_forecast_mw > 0 else 0}
demand_mw = (1800,)
wind_forecast_mw = (350,)
solar_forecast_mw = (250,)
generation_sources = (sources,)
hour = 14
'\nOptimize dispatch subject to daily emissions constraint.\n\nBalances cost minimization with emissions compliance,\npotentially dispatching higher-cost, lower-emission units.\n'
schedule = []
cumulative_emissions = 0
total_cost = 0
for hour, demand_mw in enumerate(demand_profile_24h):
    pass
hours_remaining = 24 - hour
emissions_penalty = 50
available_sources = {}
modified_specs['variable_cost_mwh'] = specs['variable_cost_mwh'] + specs['emissions_co2_ton_mwh'] * emissions_penalty
logger.info(f'  Hour {hour}: Emissions constraint binding, adjusting dispatch')
cumulative_emissions += dispatch['total_emissions_tons']
return {'schedule': schedule, 'total_cost': total_cost, 'total_emissions': cumulative_emissions, 'emissions_limit': daily_emissions_limit_tons, 'emissions_utilization_pct': cumulative_emissions / daily_emissions_limit_tons * 100}
(demand_profile,)
(sources,)
daily_emissions_limit_tons = 25000

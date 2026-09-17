# Simulator
def run_usim_simulation(base_price, monthly_fixed_cost, variable_cost_per_unit, marketing_spend, organic_growth_rate, churn_rate, initial_cash=500000.0, initial_customers=5, cac=2000.0, projection_months=12):
    contribution_margin = base_price - variable_cost_per_unit
    margin_percentage = (contribution_margin / base_price * 100) if base_price > 0 else 0
    effective_cac = max(cac, 100.0)
    monthly_projections = []
    current_customers = initial_customers
    current_cash = initial_cash
    break_even_month = None
    cash_out_month = None

    for m in range(1, projection_months + 1):
        churned = int(current_customers * (churn_rate / 100.0))
        paid_acquisitions = int(marketing_spend / effective_cac) if effective_cac > 0 else 0
        organic_acquisitions = max(1, int(current_customers * (organic_growth_rate / 100.0))) if current_customers > 0 else 1
        new_customers = paid_acquisitions + organic_acquisitions
        current_customers = max(0, current_customers - churned + new_customers)
        
        revenue = current_customers * base_price
        var_costs = current_customers * variable_cost_per_unit
        total_costs = monthly_fixed_cost + var_costs + marketing_spend
        net_flow = revenue - total_costs
        current_cash += net_flow
        
        if revenue >= total_costs and break_even_month is None:
            break_even_month = m
            
        if current_cash <= 0 and cash_out_month is None:
            cash_out_month = m

        monthly_projections.append({
            'month': m,
            'customers': current_customers,
            'revenue': round(revenue, 2),
            'fixed_cost': round(monthly_fixed_cost, 2),
            'variable_cost': round(var_costs, 2),
            'marketing_spend': round(marketing_spend, 2),
            'total_expenses': round(total_costs, 2),
            'net_cash_flow': round(net_flow, 2),
            'cash_balance': round(current_cash, 2)
        })

    latest = monthly_projections[-1]
    projected_arr = latest['revenue'] * 12
    latest_burn = max(0, latest['total_expenses'] - latest['revenue'])
    runway_months = round(current_cash / latest_burn, 1) if latest_burn > 0 else (99.0 if current_cash > 0 else 0.0)
    avg_lifetime_months = (100.0 / churn_rate) if churn_rate > 0 else 36.0
    ltv = contribution_margin * avg_lifetime_months
    ltv_cac_ratio = round(ltv / effective_cac, 2) if effective_cac > 0 else 0

    return {
        'summary': {
            'contribution_margin': round(contribution_margin, 2),
            'margin_percentage': round(margin_percentage, 1),
            'effective_cac': round(effective_cac, 2),
            'estimated_ltv': round(ltv, 2),
            'ltv_cac_ratio': ltv_cac_ratio,
            'break_even_month': break_even_month if break_even_month else 'Beyond 12 Months',
            'cash_out_month': cash_out_month if cash_out_month else 'Sufficient Runway',
            'final_projected_cash': round(current_cash, 2),
            'projected_arr': round(projected_arr, 2),
            'runway_months': runway_months,
            'final_customer_count': current_customers
        },
        'monthly_projections': monthly_projections
    }

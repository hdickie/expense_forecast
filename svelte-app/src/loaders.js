import {
    draft_parameters,
    draft_accounts,
    draft_line_items,
    draft_decision_rules,
    browse,
    view_time_series,
    view_sankey,
    view_milestone_results,
    view_line_items
  } from './stores.js';
  
  const storeMap = {
    draft_parameters,
    draft_accounts,
    draft_line_items,
    draft_decision_rules,
    browse,
    view_time_series,
    view_sankey,
    view_milestone_results,
    view_line_items
  };
  
  export async function fetchData(name, user) {
    if (!(name in storeMap)) throw new Error(`Unknown data source: ${name}`);
  
    const res = await fetch(`http://api.localhost/${name}?user=${encodeURIComponent(user)}`, {
      credentials: 'include'
    });
  
    if (!res.ok) {
      console.warn(`Failed to load ${name}`);
      return;
    }
  
    const raw = await res.json();
    storeMap[name].set(JSON.parse(raw));
  }
  
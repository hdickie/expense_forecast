// stores.js
import { writable } from 'svelte/store';


export const activeTab = writable('draft');
export const draft_parameters = writable([]);
export const draft_accounts = writable([]);
export const draft_line_items = writable([]);
export const draft_decision_rules = writable([]);
export const browse = writable([]);
export const view_time_series = writable([]);
export const view_sankey = writable([]);
export const view_line_items = writable([]);
export const view_milestone_results = writable([]);
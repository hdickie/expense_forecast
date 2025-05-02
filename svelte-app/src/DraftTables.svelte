<!-- DraftTables.svelte -->
<script>
  import { draft_parameters, draft_accounts, draft_line_items, draft_decision_rules } from './stores.js';
</script>

<h2>Parameters</h2>
{#each $draft_parameters as p}
  <div>{p.name}: {p.value}</div>
{/each}

<h2>Accounts</h2>
{#each $draft_accounts as a}
  <div>{a.name} ({a.type})</div>
{/each}

<!-- repeat for line_items, decision_rules -->

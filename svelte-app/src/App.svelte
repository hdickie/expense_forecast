<!-- App.svelte -->
<script>
	import config from './site_config.json'; // bundled at build time

	document.title = config.title;

	import { activeTab } from './stores.js';

	import IndexNavbar from './index_navbar.svelte';
	import IndexDraftTab from './index_draft_tab.svelte';
	import IndexBrowseTab from './index_browse_tab.svelte';
	import IndexViewTab from './index_view_tab.svelte';
	
	import { fetchData } from './loaders.js';
	import { draft_parameters, draft_accounts, draft_line_items, draft_decision_rules, browse, view_time_series, view_sankey, view_milestone_results, view_line_items } from './stores.js';

	import LineItemsTable from './DraftLineItemsTable.svelte';

</script>

 <IndexNavbar />
 
  {#if $activeTab === 'draft'}
  	<IndexDraftTab />
  {/if}
  
  {#if $activeTab === 'browse'}
  <IndexBrowseTab />
  {/if}
  
  {#if $activeTab === 'view'}
  <IndexViewTab /> 
  {/if}
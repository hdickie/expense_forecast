<script>
    export let title = "Expense Forecast Tool";
    import { activeTab } from './stores.js';    
    // Optional: callbacks or state management
    function handleRequestFeature() {
      // dispatch an event or trigger logic
      console.log("Request feature clicked");
    }
  
    function handleReportProblem() {
      console.log("Report problem clicked");
    }
  </script>


  
  <div class="tabs">
    <div class="tab-buttons">
      <button class="tab" class:active={activeTab === 'draft'} on:click={() => {
        console.log('Switching to draft tab');
        activeTab.set('draft');
      } }>DRAFT</button>
      <button class="tab" class:active={activeTab === 'browse'} on:click={() => {
        console.log('Switching to browse view');
        activeTab.set('browse');
      }}>BROWSE</button>
      <button class="tab" class:active={activeTab === 'view'} on:click={() => {
        console.log('Switching to view view');
        activeTab.set('view');
      }}>VIEW</button>
    </div>
  
    <div class="navbar-page-title">{title}</div>
  
    <div>
      <button class="request-feature-button" on:click={handleRequestFeature}>
        Request a Feature
      </button>
      <button class="report-problem-button" on:click={handleReportProblem}>
        Report a Problem
      </button>
    </div>
  </div>
  
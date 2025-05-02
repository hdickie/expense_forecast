<script>
  import { onMount } from 'svelte';
  import { Tabulator } from 'tabulator-tables';

  let tableContainer;
  let startDate = '';
  let endDate = '';
  let forecastName = '';
  let approximate = false;

  let table;

  onMount(() => {
    table = new Tabulator(tableContainer, {
      layout: 'fitColumns',
      columns: [
        { title: 'Start Date', field: 'start_date' },
        { title: 'End Date', field: 'end_date' },
        { title: 'Name', field: 'forecast_name' },
        { title: 'Approx.', field: 'approximate' },
        {
          title: '',
          formatter: 'buttonCross',
          width: 40,
          hozAlign: 'center',
          cellClick: (e, cell) => cell.getRow().delete(),
        }
      ],
      data: []
    });
  });

  function addRow() {
    table.addRow({
      start_date: new Date(startDate),
      end_date: new Date(endDate),
      forecast_name: forecastName,
      approximate
    });
  }
</script>

<div bind:this={tableContainer} style="margin-bottom: 1rem;"></div>

<h3>Parameters</h3>
<label>Forecast Name <input type="text" bind:value={forecastName}></label>
<label>Start Date <input type="date" bind:value={startDate}></label>
<label>End Date <input type="date" bind:value={endDate}></label>
<label>Approximate <input type="checkbox" bind:checked={approximate}></label>

<button on:click={addRow}>Add Row</button>

<script>
  import { onMount } from 'svelte';
  import { Tabulator } from 'tabulator-tables';
  import { draft_line_items } from './stores.js';

  let tableContainer;

  let table; // keep reference if needed

  $: data = $draft_line_items;

  onMount(() => {
    table = new Tabulator(tableContainer, {
      layout: "fitColumns",
      data,
      columns: [
        { title: "Name", field: "name" },
        { title: "Amount", field: "amount", formatter: "money" },
        { title: "Priority", field: "priority" },
        { title: "Choice Index", field: "choice_index" },
        { title: "Cadence", field: "cadence" },
        { title: "Start", field: "start" },
        { title: "End", field: "end" },
        { title: "Deferrable", field: "deferrable" },
        { title: "Partial", field: "partial" },
        {
          title: "",
          formatter: "buttonCross",
          width: 40,
          hozAlign: "center",
          cellClick: function (e, cell) {
            cell.getRow().delete();
          }
        }
      ]
    });

    // Reactive update when data changes
    draft_line_items.subscribe(newData => {
      table.replaceData(newData);
    });
  });
</script>

<div bind:this={tableContainer}></div>

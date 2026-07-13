<script lang="ts">
  export let title: string;
  export let message: string;
  export let detail: string | undefined = undefined;
</script>

<div class="flex min-h-[420px] items-center justify-center p-6 text-center">
  <div class="max-w-sm">
    <h2 class="text-base font-semibold text-foreground">{title}</h2>
    <p class="mt-3 text-sm leading-6 text-muted-foreground">{message}</p>
    {#if detail}
      <p class="mt-2 text-sm leading-6 text-muted-foreground">{detail}</p>
    {/if}
  </div>
</div>

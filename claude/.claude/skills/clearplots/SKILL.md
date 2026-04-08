---
name: clearplots
description: Clear all files in the agent plots directory ($SCRATCH/$USER/agent_plots/). Invoked via /clearplots.
---

Clear all plots and tables from the agent plots directory, preserving the server log.

Run this command:

```bash
find $SCRATCH/$USER/agent_plots -mindepth 1 -not -name 'server.log' -delete
```

Then confirm to the user: "Cleared. http://localhost:8765 is now empty."

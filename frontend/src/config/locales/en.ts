/** English translation resources. The single source of user-facing copy. */
const en = {
  app: {
    name: "Praxis",
    tagline: "Disaster Response Doctrine & Command",
  },
  status: {
    online: "API Online",
    offline: "API Offline",
    checking: "Checking…",
    db: "Database",
    version: "Version",
    lastChecked: "Last checked",
  },
  scenario: {
    label: "Active scenario",
    placeholder: "No scenario loaded",
    empty: "Scenario management arrives in a later phase.",
  },
  nav: {
    overview: "Overview",
    sense: "Sense",
    decide: "Decide",
    act: "Act",
    learn: "Learn",
    loopSection: "Response Loop",
  },
  landing: {
    kicker: "Command Platform",
    title: "A calm command center for disaster response.",
    subtitle:
      "Praxis turns fragmented signals into deliberate action across a single loop — Sense, Decide, Act, and Learn — built for Sri Lanka's disaster management authorities.",
    enter: "Enter the console",
    loopTitle: "The response loop",
  },
  stage: {
    comingSoon: "Arriving in a later phase",
    sense: {
      title: "Sense",
      summary: "A live operational picture of the emergency as it unfolds.",
      description:
        "Incidents, shelters, assets, and road closures on one map-backed dashboard — the shared situational picture every decision draws from.",
    },
    decide: {
      title: "Decide",
      summary: "Playbook Studio — design, compare, and stress-test response strategies.",
      description:
        "The flagship workspace: compose candidate response plans, compare them side by side, and stress-test each under uncertainty before committing.",
    },
    act: {
      title: "Act",
      summary: "Turn the chosen strategy into a ready-to-execute operational brief.",
      description:
        "Export a clear, authoritative brief — tasks, assignments, and timing — that field units can execute without ambiguity.",
    },
    learn: {
      title: "Learn",
      summary: "Compare the plan you chose against what actually happened.",
      description:
        "After-action review: measure the executed plan against real outcomes to sharpen doctrine for the next event.",
    },
  },
  theme: {
    toggle: "Toggle theme",
    light: "Light",
    dark: "Dark",
  },
} as const;

export default en;

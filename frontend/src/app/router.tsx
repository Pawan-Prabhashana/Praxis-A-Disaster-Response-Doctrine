import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "@/components/shell/AppShell";
import LandingRoute from "@/routes/Landing";

/**
 * Stage routes are lazy-loaded so heavy dependencies (MapLibre, Recharts on
 * /sense) stay out of the initial bundle and load only when their stage is
 * visited. The landing route is eager (it is the entry point).
 */
export const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <AppShell />,
      children: [
        { index: true, element: <LandingRoute /> },
        {
          path: "sense",
          lazy: async () => ({ Component: (await import("@/routes/Sense")).default }),
        },
        {
          path: "decide",
          lazy: async () => ({ Component: (await import("@/routes/Decide")).default }),
        },
        {
          path: "act",
          lazy: async () => ({ Component: (await import("@/routes/Act")).default }),
        },
        {
          path: "learn",
          lazy: async () => ({ Component: (await import("@/routes/Learn")).default }),
        },
      ],
    },
  ],
  // Opt in early to React Router v7 behaviours (silences dev warnings).
  {
    future: {
      v7_relativeSplatPath: true,
    },
  },
);

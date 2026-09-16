import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "@/components/shell/AppShell";
import ActRoute from "@/routes/Act";
import DecideRoute from "@/routes/Decide";
import LandingRoute from "@/routes/Landing";
import LearnRoute from "@/routes/Learn";
import SenseRoute from "@/routes/Sense";

export const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <AppShell />,
      children: [
        { index: true, element: <LandingRoute /> },
        { path: "sense", element: <SenseRoute /> },
        { path: "decide", element: <DecideRoute /> },
        { path: "act", element: <ActRoute /> },
        { path: "learn", element: <LearnRoute /> },
      ],
    },
  ],
  // Opt in early to React Router v7 behaviours (silences the future-flag warnings).
  {
    future: {
      v7_relativeSplatPath: true,
      v7_fetcherPersist: true,
      v7_normalizeFormMethod: true,
      v7_partialHydration: true,
      v7_skipActionErrorRevalidation: true,
    },
  },
);

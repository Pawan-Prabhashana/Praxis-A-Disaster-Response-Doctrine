import { RouterProvider } from "react-router-dom";

import { AppProviders } from "@/app/providers";
import { router } from "@/app/router";

export function App() {
  return (
    <AppProviders>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </AppProviders>
  );
}

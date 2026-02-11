import { Suspense } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { MobileNav } from "@/components/layout/mobile-nav";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { SkipLink } from "@/components/shared/SkipLink";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { PageSkeleton } from "@/components/ui/skeleton";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <SkipLink />
      <Sidebar />
      <MobileNav />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main id="main-content" className="flex-1 overflow-y-auto p-6" role="main">
          <Breadcrumb />
          <ErrorBoundary>
            <Suspense fallback={<PageSkeleton />}>
              {children}
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}

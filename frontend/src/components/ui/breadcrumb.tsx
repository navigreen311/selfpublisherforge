'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

// Map route segments to human-readable labels
const ROUTE_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  writing: 'Writing Studio',
  projects: 'Projects',
  market: 'Market Research',
  marketing: 'Marketing',
  analytics: 'Analytics',
  pipeline: 'Production Pipeline',
  publishing: 'Publishing',
  settings: 'Settings',
  agents: 'AI Agents',
  specialty: 'Specialty',
  'childrens-books': "Children's Books",
  'coloring-books': 'Coloring Books',
  'puzzle-books': 'Puzzle Books',
  'product-page': 'Product Page Lab',
  covers: 'Cover Design',
  outline: 'Outline Generator',
  tasks: 'Tasks',
  workflows: 'Workflows',
  advertising: 'Advertising',
  onboarding: 'Onboarding',
  knowledge: 'Knowledge Base',
  competitors: 'Competitors',
  keywords: 'Keywords',
  blurb: 'Blurb',
  new: 'New',
};

// UUID v4 pattern
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function isUUID(segment: string): boolean {
  return UUID_REGEX.test(segment);
}

function formatSegment(segment: string): string {
  if (isUUID(segment)) {
    return segment.slice(0, 8) + '...';
  }
  if (ROUTE_LABELS[segment]) {
    return ROUTE_LABELS[segment];
  }
  // Fallback: capitalize and replace hyphens
  return segment
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function generateBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname
    .split('/')
    .filter(Boolean)
    .filter((s) => !s.startsWith('('));

  if (segments.length === 0) {
    return [];
  }

  return segments.map((segment, index) => {
    const href = '/' + segments.slice(0, index + 1).join('/');
    const isLast = index === segments.length - 1;

    return {
      label: formatSegment(segment),
      href: isLast ? undefined : href,
    };
  });
}

export function Breadcrumb({
  items,
  className,
}: {
  items?: BreadcrumbItem[];
  className?: string;
}) {
  const pathname = usePathname();

  const breadcrumbs = items ?? generateBreadcrumbs(pathname || '');

  if (breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <nav
      aria-label="Breadcrumb"
      className={cn('flex items-center gap-1.5 text-sm mb-4', className)}
    >
      <Link
        href="/dashboard"
        className="text-muted-foreground hover:text-foreground transition-colors"
        aria-label="Home"
      >
        <Home className="h-3.5 w-3.5" />
      </Link>

      {breadcrumbs.map((crumb, index) => (
        <span key={index} className="flex items-center gap-1.5">
          <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
          {crumb.href ? (
            <Link
              href={crumb.href}
              className="text-muted-foreground hover:text-foreground transition-colors truncate max-w-[160px]"
              title={crumb.label}
            >
              {crumb.label}
            </Link>
          ) : (
            <span
              className="font-medium text-foreground truncate max-w-[200px]"
              title={crumb.label}
            >
              {crumb.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}

"use client";

import { BookOpen, DollarSign, Megaphone, Bot, Plus, ArrowRight } from "lucide-react";
import { StatCard } from "@/components/shared/stat-card";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

const stats = [
  {
    label: "Total Books",
    value: 12,
    icon: BookOpen,
    trend: { value: 8, isPositive: true },
  },
  {
    label: "Monthly Revenue",
    value: "$4,320",
    icon: DollarSign,
    trend: { value: 12, isPositive: true },
  },
  {
    label: "Active Campaigns",
    value: 3,
    icon: Megaphone,
    trend: { value: -5, isPositive: false },
  },
  {
    label: "AI Tasks",
    value: 28,
    icon: Bot,
    trend: { value: 24, isPositive: true },
  },
];

const recentActivity = [
  {
    id: "1",
    action: "Book published",
    detail: '"The Art of Self-Publishing" is now live on KDP',
    time: "2 hours ago",
    type: "success" as const,
  },
  {
    id: "2",
    action: "AI generation complete",
    detail: "Book description generated for Project Alpha",
    time: "4 hours ago",
    type: "info" as const,
  },
  {
    id: "3",
    action: "Campaign paused",
    detail: "AMS campaign for Summer Collection paused due to budget",
    time: "6 hours ago",
    type: "warning" as const,
  },
  {
    id: "4",
    action: "New review received",
    detail: "5-star review on 'Writing Mastery Guide'",
    time: "1 day ago",
    type: "success" as const,
  },
];

const quickActions = [
  { label: "New Project", href: "/projects/new", icon: Plus },
  { label: "View Projects", href: "/projects", icon: ArrowRight },
  { label: "AI Agents", href: "/agents", icon: Bot },
  { label: "Analytics", href: "/analytics", icon: ArrowRight },
];

const recentProjects = [
  { id: "1", title: "The Art of Self-Publishing", type: "book", status: "active" },
  { id: "2", title: "Summer Romance Series", type: "series", status: "draft" },
  { id: "3", title: "Writing Mastery Guide", type: "book", status: "active" },
];

const badgeVariant = (status: string) => {
  switch (status) {
    case "active":
      return "default" as const;
    case "draft":
      return "secondary" as const;
    case "archived":
      return "outline" as const;
    default:
      return "secondary" as const;
  }
};

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here is an overview of your publishing activity.
          </p>
        </div>
        <Button asChild>
          <Link href="/projects/new">
            <Plus className="mr-2 h-4 w-4" /> New Project
          </Link>
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Recent Activity</CardTitle>
            <CardDescription>Your latest publishing activity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-start gap-3 pb-4 last:pb-0 border-b last:border-0"
                >
                  <div
                    className={`mt-1 h-2 w-2 rounded-full shrink-0 ${
                      activity.type === "success"
                        ? "bg-green-500"
                        : activity.type === "warning"
                        ? "bg-yellow-500"
                        : "bg-blue-500"
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{activity.action}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {activity.detail}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {activity.time}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
            <CardDescription>Common tasks at a glance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {quickActions.map((action) => {
                const Icon = action.icon;
                return (
                  <Button
                    key={action.label}
                    variant="outline"
                    className="h-auto py-4 flex-col gap-2"
                    asChild
                  >
                    <Link href={action.href}>
                      <Icon className="h-5 w-5" />
                      <span className="text-xs">{action.label}</span>
                    </Link>
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg">Recent Projects</CardTitle>
            <CardDescription>Your latest projects</CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/projects">View all</Link>
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentProjects.map((project) => (
              <div
                key={project.id}
                className="flex items-center justify-between py-2 border-b last:border-0"
              >
                <div className="flex items-center gap-3">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">{project.title}</p>
                    <p className="text-xs text-muted-foreground capitalize">
                      {project.type}
                    </p>
                  </div>
                </div>
                <Badge variant={badgeVariant(project.status)}>
                  {project.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

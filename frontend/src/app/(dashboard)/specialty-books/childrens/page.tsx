"use client";

import { useState } from "react";
import { Plus, Sparkles, BookOpen, Clock, CheckCircle2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ChildrensBookList } from "@/modules/specialty-books/childrens/components/ChildrensBookList";
import { CreateChildrensBookWizard } from "@/modules/specialty-books/childrens/components/CreateChildrensBookWizard";
import { useChildrensBookStats } from "@/modules/specialty-books/childrens/hooks";

function StatCard({
  label,
  value,
  icon: Icon,
  isLoading,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  isLoading: boolean;
}) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-primary/10">
            <Icon className="h-5 w-5 text-primary" />
          </div>
          <div>
            {isLoading ? (
              <Skeleton className="h-7 w-12" />
            ) : (
              <div className="text-2xl font-bold">{value}</div>
            )}
            <div className="text-xs text-muted-foreground">{label}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function ChildrensBooksPage() {
  const [wizardOpen, setWizardOpen] = useState(false);
  const { data: stats, isLoading: statsLoading } = useChildrensBookStats();

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Sparkles className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Children&#39;s Books</h1>
            <p className="text-muted-foreground">
              Create illustrated children&#39;s books with AI
            </p>
          </div>
        </div>
        <Button onClick={() => setWizardOpen(true)}>
          <Plus className="h-4 w-4 mr-2" /> New Book
        </Button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Books" value={stats?.total_books ?? 0} icon={BookOpen} isLoading={statsLoading} />
        <StatCard label="In Progress" value={stats?.in_progress ?? 0} icon={Clock} isLoading={statsLoading} />
        <StatCard label="Published" value={stats?.published ?? 0} icon={CheckCircle2} isLoading={statsLoading} />
        <StatCard label="Pages Created" value={stats?.pages_created ?? 0} icon={FileText} isLoading={statsLoading} />
      </div>

      <ChildrensBookList onCreateNew={() => setWizardOpen(true)} />

      <CreateChildrensBookWizard open={wizardOpen} onOpenChange={setWizardOpen} />
    </div>
  );
}

import { Puzzle } from "lucide-react";

export default function PuzzleBooksPage() {
  return (
    <div className="container mx-auto py-6 space-y-4">
      <div className="flex items-center gap-3">
        <Puzzle className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-2xl font-bold">Puzzle Book Generator</h1>
          <p className="text-muted-foreground">Coming soon.</p>
        </div>
      </div>
    </div>
  );
}

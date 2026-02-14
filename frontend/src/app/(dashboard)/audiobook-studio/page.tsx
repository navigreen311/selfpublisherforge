"use client";

import { useState } from "react";
import { Plus, Headphones } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AudiobookProjectList } from "@/modules/audiobook/components/AudiobookProjectList";
import { CreateAudiobookWizard } from "@/modules/audiobook/components/CreateAudiobookWizard";

export default function AudiobookStudioPage() {
  const [wizardOpen, setWizardOpen] = useState(false);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Headphones className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Audiobook Studio</h1>
            <p className="text-muted-foreground">
              AI-powered audiobook production
            </p>
          </div>
        </div>
        <Button onClick={() => setWizardOpen(true)}>
          <Plus className="h-4 w-4 mr-2" /> New Audiobook
        </Button>
      </div>

      <AudiobookProjectList onCreateNew={() => setWizardOpen(true)} />

      <CreateAudiobookWizard
        open={wizardOpen}
        onOpenChange={setWizardOpen}
      />
    </div>
  );
}

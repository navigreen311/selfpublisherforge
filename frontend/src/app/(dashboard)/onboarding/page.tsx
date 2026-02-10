"use client";

import { useRouter } from "next/navigation";
import {
  Sparkles,
  FolderPlus,
  Link as LinkIcon,
  Wand2,
} from "lucide-react";
import { OnboardingWizard, type WizardStep } from "@/components/shared/onboarding-wizard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

function WelcomeStep() {
  return (
    <div className="text-center space-y-4 py-4">
      <div className="mx-auto rounded-full bg-primary/10 p-4 w-fit">
        <Sparkles className="h-12 w-12 text-primary" />
      </div>
      <h2 className="text-xl font-semibold">Welcome to SelfPublisherForge!</h2>
      <p className="text-muted-foreground max-w-md mx-auto">
        We will guide you through setting up your account in just a few steps.
        You will create your first project, connect your KDP account, and
        experience the power of AI-assisted publishing.
      </p>
    </div>
  );
}

function CreateProjectStep() {
  return (
    <div className="space-y-4 py-2">
      <div className="flex items-center gap-3 mb-4">
        <div className="rounded-full bg-primary/10 p-2">
          <FolderPlus className="h-5 w-5 text-primary" />
        </div>
        <p className="text-sm text-muted-foreground">
          Create your first publishing project to get started.
        </p>
      </div>
      <Input label="Project Title" placeholder="My First Book" />
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Project Type</label>
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="book">Book</SelectItem>
            <SelectItem value="series">Series</SelectItem>
            <SelectItem value="course">Course</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Genre</label>
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select genre" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="fiction">Fiction</SelectItem>
            <SelectItem value="non-fiction">Non-Fiction</SelectItem>
            <SelectItem value="romance">Romance</SelectItem>
            <SelectItem value="mystery">Mystery</SelectItem>
            <SelectItem value="self-help">Self-Help</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}

function ConnectKDPStep() {
  return (
    <div className="space-y-4 py-2">
      <div className="flex items-center gap-3 mb-4">
        <div className="rounded-full bg-primary/10 p-2">
          <LinkIcon className="h-5 w-5 text-primary" />
        </div>
        <p className="text-sm text-muted-foreground">
          Connect your Amazon KDP account to sync your books and sales data.
        </p>
      </div>
      <Input
        label="KDP Email"
        type="email"
        placeholder="your-kdp-email@example.com"
      />
      <div className="rounded-lg border border-dashed p-6 text-center">
        <p className="text-sm text-muted-foreground mb-3">
          We use secure OAuth to connect to your KDP account. Your credentials
          are never stored.
        </p>
        <Button variant="outline">
          <LinkIcon className="mr-2 h-4 w-4" />
          Connect KDP Account
        </Button>
      </div>
    </div>
  );
}

function AIGenerationStep() {
  return (
    <div className="space-y-4 py-2">
      <div className="flex items-center gap-3 mb-4">
        <div className="rounded-full bg-primary/10 p-2">
          <Wand2 className="h-5 w-5 text-primary" />
        </div>
        <p className="text-sm text-muted-foreground">
          Experience AI-powered content generation. Try generating a book
          description!
        </p>
      </div>
      <div className="rounded-lg bg-muted/50 p-4 space-y-3">
        <p className="text-sm font-medium">Sample AI Generation</p>
        <p className="text-sm text-muted-foreground italic">
          &ldquo;Discover the secrets of successful self-publishing in this
          comprehensive guide. From manuscript to marketplace, learn proven
          strategies that have helped thousands of authors turn their writing
          dreams into reality...&rdquo;
        </p>
      </div>
      <Button className="w-full">
        <Wand2 className="mr-2 h-4 w-4" />
        Generate Book Description
      </Button>
    </div>
  );
}

export default function OnboardingPage() {
  const router = useRouter();

  const steps: WizardStep[] = [
    {
      id: "welcome",
      title: "Welcome",
      description: "Let us get you set up",
      content: <WelcomeStep />,
    },
    {
      id: "project",
      title: "First Project",
      description: "Create your first publishing project",
      content: <CreateProjectStep />,
    },
    {
      id: "kdp",
      title: "Connect KDP",
      description: "Link your Amazon KDP account",
      content: <ConnectKDPStep />,
      isOptional: true,
    },
    {
      id: "ai",
      title: "AI Tools",
      description: "Try AI-powered generation",
      content: <AIGenerationStep />,
      isOptional: true,
    },
  ];

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-8">
      <OnboardingWizard
        steps={steps}
        onComplete={() => router.push("/dashboard")}
        onSkip={() => router.push("/dashboard")}
      />
    </div>
  );
}

"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Sparkles,
  FolderPlus,
  Link as LinkIcon,
  Wand2,
  Loader2,
  CheckCircle2,
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
import { api } from "@/lib/api";
import { extractApiError } from "@/hooks/use-api";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CreateBookResponse {
  id: string;
  title: string;
  type: string;
  status: string;
}

interface PublishingAccountResponse {
  id: string;
  platform: string;
  account_name: string;
  account_email: string | null;
  is_active: boolean;
}

interface GenerateResponse {
  request_id: string;
  generation_type: string;
  content: string;
  tokens_used: number;
  model_used: string;
}

// ---------------------------------------------------------------------------
// Step 1: Welcome
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Step 2: Create Project
// ---------------------------------------------------------------------------

interface CreateProjectStepProps {
  title: string;
  setTitle: (v: string) => void;
  projectType: string;
  setProjectType: (v: string) => void;
  genre: string;
  setGenre: (v: string) => void;
  isCreated: boolean;
  touched: Record<string, boolean>;
  onBlur: (field: string) => void;
}

function getProjectTitleError(title: string): string | undefined {
  const trimmed = title.trim();
  if (!trimmed) return "Project title is required.";
  if (trimmed.length < 3) return "Project title must be at least 3 characters.";
  return undefined;
}

function getGenreError(genre: string): string | undefined {
  if (!genre) return "Please select a genre.";
  return undefined;
}

function CreateProjectStep({
  title,
  setTitle,
  projectType,
  setProjectType,
  genre,
  setGenre,
  isCreated,
  touched,
  onBlur,
}: CreateProjectStepProps) {
  const titleError = touched.title ? getProjectTitleError(title) : undefined;
  const genreError = touched.genre ? getGenreError(genre) : undefined;

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
      {isCreated ? (
        <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950 p-4">
          <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 shrink-0" />
          <p className="text-sm text-green-800 dark:text-green-200">
            Project <span className="font-medium">&ldquo;{title}&rdquo;</span> created successfully.
          </p>
        </div>
      ) : (
        <>
          <Input
            label="Project Title"
            placeholder="My First Book"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={() => onBlur("title")}
            error={titleError}
          />
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Project Type</label>
            <Select value={projectType} onValueChange={setProjectType}>
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
            <Select
              value={genre}
              onValueChange={(v) => {
                setGenre(v);
                onBlur("genre");
              }}
            >
              <SelectTrigger
                className={cn(
                  genreError && "border-destructive focus:ring-destructive"
                )}
              >
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
            {genreError && (
              <p className="text-sm text-destructive">{genreError}</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 3: Connect KDP
// ---------------------------------------------------------------------------

interface ConnectKDPStepProps {
  kdpEmail: string;
  setKdpEmail: (v: string) => void;
  isConnecting: boolean;
  isConnected: boolean;
  onConnect: () => void;
  touched: Record<string, boolean>;
  onBlur: (field: string) => void;
}

function getKdpEmailError(email: string): string | undefined {
  const trimmed = email.trim();
  if (!trimmed) return undefined; // KDP step is optional, email only required for connect
  // Basic email check
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) return "Please enter a valid email address.";
  return undefined;
}

function ConnectKDPStep({
  kdpEmail,
  setKdpEmail,
  isConnecting,
  isConnected,
  onConnect,
  touched,
  onBlur,
}: ConnectKDPStepProps) {
  const emailError = touched.kdpEmail ? getKdpEmailError(kdpEmail) : undefined;

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
      {isConnected ? (
        <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950 p-4">
          <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 shrink-0" />
          <p className="text-sm text-green-800 dark:text-green-200">
            KDP account connected successfully.
          </p>
        </div>
      ) : (
        <>
          <Input
            label="KDP Email"
            type="email"
            placeholder="your-kdp-email@example.com"
            value={kdpEmail}
            onChange={(e) => setKdpEmail(e.target.value)}
            onBlur={() => onBlur("kdpEmail")}
            error={emailError}
          />
          <div className="rounded-lg border border-dashed p-6 text-center">
            <p className="text-sm text-muted-foreground mb-3">
              We use secure OAuth to connect to your KDP account. Your credentials
              are never stored.
            </p>
            <Button
              variant="outline"
              onClick={onConnect}
              disabled={isConnecting || !kdpEmail.trim() || !!emailError}
            >
              {isConnecting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <LinkIcon className="mr-2 h-4 w-4" />
              )}
              {isConnecting ? "Connecting..." : "Connect KDP Account"}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 4: AI Generation
// ---------------------------------------------------------------------------

interface AIGenerationStepProps {
  isGenerating: boolean;
  generatedContent: string | null;
  onGenerate: () => void;
  projectId: string | null;
}

function AIGenerationStep({
  isGenerating,
  generatedContent,
  onGenerate,
  projectId,
}: AIGenerationStepProps) {
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
        <p className="text-sm font-medium">
          {generatedContent ? "Generated Book Description" : "Sample AI Generation"}
        </p>
        {isGenerating ? (
          <div className="flex items-center gap-2 py-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Generating your book description...</p>
          </div>
        ) : generatedContent ? (
          <p className="text-sm text-muted-foreground italic">
            &ldquo;{generatedContent}&rdquo;
          </p>
        ) : (
          <p className="text-sm text-muted-foreground italic">
            &ldquo;Discover the secrets of successful self-publishing in this
            comprehensive guide. From manuscript to marketplace, learn proven
            strategies that have helped thousands of authors turn their writing
            dreams into reality...&rdquo;
          </p>
        )}
      </div>
      {generatedContent ? (
        <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950 p-3">
          <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 shrink-0" />
          <p className="text-sm text-green-800 dark:text-green-200">
            Description generated successfully.
          </p>
        </div>
      ) : (
        <Button
          className="w-full"
          onClick={onGenerate}
          disabled={isGenerating || !projectId}
        >
          {isGenerating ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Wand2 className="mr-2 h-4 w-4" />
          )}
          {isGenerating ? "Generating..." : "Generate Book Description"}
        </Button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Onboarding Page
// ---------------------------------------------------------------------------

export default function OnboardingPage() {
  const router = useRouter();

  // -- Step 2 state: Create Project --
  const [bookTitle, setBookTitle] = useState("");
  const [projectType, setProjectType] = useState("book");
  const [genre, setGenre] = useState("");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [projectCreated, setProjectCreated] = useState(false);

  // -- Step 3 state: Connect KDP --
  const [kdpEmail, setKdpEmail] = useState("");
  const [kdpConnected, setKdpConnected] = useState(false);

  // -- Step 4 state: AI Generation --
  const [generatedContent, setGeneratedContent] = useState<string | null>(null);

  // -- Field-level touched tracking for validation UX --
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const handleFieldBlur = useCallback((field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }, []);

  // -- Mutations --

  // Step 2: Create a project via POST /api/v1/books
  const createProjectMutation = useMutation<
    CreateBookResponse,
    Error,
    { title: string; type: string; genre: string }
  >({
    mutationFn: async (payload) => {
      const { data } = await api.post<CreateBookResponse>("/api/v1/books", {
        title: payload.title,
        type: payload.type,
        genre: payload.genre,
      });
      return data;
    },
    onSuccess: (data) => {
      setProjectId(data.id);
      setProjectCreated(true);
      toast.success("Project created successfully!");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });

  // Step 3: Connect KDP account
  const connectKdpMutation = useMutation<PublishingAccountResponse, Error, { email: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post<PublishingAccountResponse>(
        "/api/v1/publishing/accounts",
        {
          platform: "kdp",
          account_name: "KDP Account",
          account_email: payload.email,
          credentials: {},
        }
      );
      return data;
    },
    onSuccess: () => {
      setKdpConnected(true);
      toast.success("KDP account connected successfully!");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });

  // Step 4: AI generation (non-streaming)
  const generateMutation = useMutation<GenerateResponse, Error, { projectId: string; title: string; genre: string }>({
    mutationFn: async (payload) => {
      const { data } = await api.post<GenerateResponse>("/api/v1/generate", {
        generation_type: "blurb",
        project_id: payload.projectId,
        instructions: `Generate a compelling book description for "${payload.title}" in the ${payload.genre || "general"} genre.`,
        context: {
          title: payload.title,
          genre: payload.genre,
        },
        stream: false,
      });
      return data;
    },
    onSuccess: (data) => {
      setGeneratedContent(data.content);
      toast.success("Book description generated!");
    },
    onError: (error) => {
      toast.error(extractApiError(error));
    },
  });

  // -- Step callbacks --

  const handleCreateProject = useCallback(async () => {
    if (projectCreated) return; // Already created, just advance

    // Mark all project fields as touched to reveal errors
    setTouched((prev) => ({ ...prev, title: true, genre: true }));

    const titleErr = getProjectTitleError(bookTitle);
    const genreErr = getGenreError(genre);

    if (titleErr || genreErr) {
      toast.error(titleErr || genreErr || "Please fix the errors before continuing.");
      throw new Error("Validation failed");
    }

    await createProjectMutation.mutateAsync({
      title: bookTitle.trim(),
      type: projectType,
      genre,
    });
  }, [bookTitle, projectType, genre, projectCreated, createProjectMutation]);

  const handleConnectKdp = useCallback(() => {
    if (kdpConnected || !kdpEmail.trim()) return;
    connectKdpMutation.mutate({ email: kdpEmail.trim() });
  }, [kdpEmail, kdpConnected, connectKdpMutation]);

  const handleGenerate = useCallback(() => {
    if (!projectId || generatedContent) return;
    generateMutation.mutate({
      projectId,
      title: bookTitle,
      genre,
    });
  }, [projectId, bookTitle, genre, generatedContent, generateMutation]);

  // -- Build steps --

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
      content: (
        <CreateProjectStep
          title={bookTitle}
          setTitle={setBookTitle}
          projectType={projectType}
          setProjectType={setProjectType}
          genre={genre}
          setGenre={setGenre}
          isCreated={projectCreated}
          touched={touched}
          onBlur={handleFieldBlur}
        />
      ),
      onBeforeNext: handleCreateProject,
    },
    {
      id: "kdp",
      title: "Connect KDP",
      description: "Link your Amazon KDP account",
      content: (
        <ConnectKDPStep
          kdpEmail={kdpEmail}
          setKdpEmail={setKdpEmail}
          isConnecting={connectKdpMutation.isPending}
          isConnected={kdpConnected}
          onConnect={handleConnectKdp}
          touched={touched}
          onBlur={handleFieldBlur}
        />
      ),
      isOptional: true,
    },
    {
      id: "ai",
      title: "AI Tools",
      description: "Try AI-powered generation",
      content: (
        <AIGenerationStep
          isGenerating={generateMutation.isPending}
          generatedContent={generatedContent}
          onGenerate={handleGenerate}
          projectId={projectId}
        />
      ),
      isOptional: true,
    },
  ];

  // Propagate loading state to the wizard's Continue button
  const isLoading = createProjectMutation.isPending;

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-8">
      <OnboardingWizard
        steps={steps}
        onComplete={() => router.push("/dashboard")}
        onSkip={() => router.push("/dashboard")}
        isLoading={isLoading}
      />
    </div>
  );
}

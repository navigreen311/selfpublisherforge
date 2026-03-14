"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  ArrowLeft,
  BookOpen,
  Plus,
  Wand2,
  Clock,
  Flame,
  Users,
  ChefHat,
  UtensilsCrossed,
  Trash2,
  GripVertical,
  Image as ImageIcon,
  Download,
  Eye,
  Calculator,
  Scale,
  FileText,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import {
  useCookbook,
  useCookbookChapters,
  useCreateChapter,
  useCreateRecipe,
  useDeleteRecipe,
  useGenerateRecipe,
  useGenerateRecipeImage,
  useImproveInstructions,
  useCalculateNutrition,
  useScaleRecipe,
  type CookbookRecipe,
  type CookbookIngredient,
  type CookbookInstruction,
} from "@/modules/specialty/cookbook/hooks";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline"> = {
  draft: "secondary",
  "in-progress": "default",
  published: "outline",
};

const DIFFICULTY_OPTIONS = [
  { value: "beginner", label: "Beginner" },
  { value: "easy", label: "Easy" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "expert", label: "Expert" },
];

const UNIT_OPTIONS = [
  "cups", "tbsp", "tsp", "oz", "g", "lbs", "kg", "ml", "L", "pieces", "pinch",
];

const DIETARY_FLAGS = [
  "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Nut-Free",
  "Keto", "Paleo", "Low-Sodium", "Sugar-Free",
];

const SCALE_FACTORS = [0.5, 1, 2, 3, 4];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default function CookbookDetailPage() {
  const params = useParams();
  const router = useRouter();
  const bookId = params.id as string;

  const { data: book, isLoading, error } = useCookbook(bookId);
  const { data: chapters } = useCookbookChapters(bookId);

  const createChapter = useCreateChapter(bookId);
  const createRecipe = useCreateRecipe(bookId);
  const generateRecipe = useGenerateRecipe(bookId);
  const generateImage = useGenerateRecipeImage(bookId);
  const improveInstructions = useImproveInstructions(bookId);
  const calculateNutrition = useCalculateNutrition(bookId);
  const scaleRecipe = useScaleRecipe(bookId);

  const [selectedRecipeId, setSelectedRecipeId] = useState<string | null>(null);
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set());
  const [scaleFactor, setScaleFactor] = useState(2);

  const selectedRecipe = chapters
    ?.flatMap((ch) => ch.recipes ?? [])
    .find((r) => r.id === selectedRecipeId);

  const totalRecipes =
    chapters?.reduce((sum, ch) => sum + (ch.recipes?.length ?? 0), 0) ?? 0;

  const toggleChapter = (chapterId: string) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(chapterId)) next.delete(chapterId);
      else next.add(chapterId);
      return next;
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
          <Skeleton className="h-9 w-9 rounded-md" />
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
        <div className="flex-1 flex">
          <Skeleton className="w-64 h-full shrink-0" />
          <div className="flex-1 p-6 space-y-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-[400px] w-full" />
          </div>
          <Skeleton className="w-64 h-full shrink-0" />
        </div>
      </div>
    );
  }

  // Error state
  if (error || !book) {
    return (
      <div className="h-screen flex flex-col bg-background">
        <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
          <Button variant="ghost" size="sm" className="gap-1.5"
            onClick={() => router.push("/specialty/cookbook-books")}>
            <ChevronLeft className="h-4 w-4" /> Back
          </Button>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-xl font-semibold">Cookbook not found</h2>
          <p className="text-muted-foreground max-w-md">
            This cookbook could not be loaded. It may have been deleted or you
            may not have permission to view it.
          </p>
          <Button asChild variant="outline">
            <Link href="/specialty/cookbook-books">
              <ArrowLeft className="h-4 w-4 mr-2" /> Return to Cookbooks
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Breadcrumb */}
      <div className="px-4 pt-2">
        <Breadcrumb items={[
          { label: "Specialty", href: "/specialty" },
          { label: "Cookbooks", href: "/specialty/cookbook-books" },
          { label: book.title },
        ]} />
      </div>
      {/* Header */}
      <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
        <Button variant="ghost" size="sm" className="gap-1.5" asChild>
          <Link href="/specialty/cookbook-books">
            <ChevronLeft className="h-4 w-4" /> Back to Cookbooks
          </Link>
        </Button>
        <div className="h-6 w-px bg-border" />
        <div className="flex items-center gap-2 min-w-0">
          <ChefHat className="h-4 w-4 text-muted-foreground shrink-0" />
          <h1 className="text-base font-semibold truncate">{book.title}</h1>
          <Badge variant={STATUS_VARIANT[book.status] ?? "secondary"} className="shrink-0 capitalize">
            {book.status}
          </Badge>
        </div>
        <div className="flex-1" />
        <span className="text-sm text-muted-foreground">
          {chapters?.length ?? 0} chapters &middot; {totalRecipes} recipes
        </span>
        <Button size="sm" variant="outline" className="gap-1.5">
          <Eye className="h-3.5 w-3.5" /> Preflight
        </Button>
        <Button size="sm" variant="outline" className="gap-1.5">
          <Download className="h-3.5 w-3.5" /> Export
        </Button>
      </div>

      {/* Three-column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT SIDEBAR: Chapter / Recipe Tree */}
        <ScrollArea className="w-64 border-r bg-muted/30 shrink-0">
          <div className="p-3 space-y-1">
            <div className="flex items-center justify-between px-1 mb-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Chapters
              </span>
              <Button variant="ghost" size="icon" className="h-6 w-6"
                onClick={() => createChapter.mutate({ title: "New Chapter" })}>
                <Plus className="h-3.5 w-3.5" />
              </Button>
            </div>

            {chapters?.map((chapter) => {
              const isExpanded = expandedChapters.has(chapter.id);
              return (
                <div key={chapter.id}>
                  <button onClick={() => toggleChapter(chapter.id)}
                    className="w-full flex items-center gap-1.5 rounded-md px-2 py-1.5 text-left hover:bg-muted transition-colors group">
                    <GripVertical className="h-3 w-3 text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100 cursor-grab" />
                    {isExpanded
                      ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />}
                    <span className="text-sm font-medium truncate flex-1">{chapter.title}</span>
                    {chapter.chapter_type && (
                      <Badge variant="outline" className="text-[9px] px-1 py-0 shrink-0">
                        {chapter.chapter_type}
                      </Badge>
                    )}
                  </button>

                  {isExpanded && (
                    <div className="ml-5 mt-0.5 space-y-0.5">
                      {chapter.recipes?.map((recipe) => (
                        <button key={recipe.id}
                          onClick={() => setSelectedRecipeId(recipe.id)}
                          className={cn(
                            "w-full flex items-center gap-2 rounded-md px-2 py-1 text-left text-sm transition-colors",
                            recipe.id === selectedRecipeId
                              ? "bg-primary/10 text-primary ring-1 ring-primary/30"
                              : "text-muted-foreground hover:bg-muted hover:text-foreground",
                          )}>
                          <UtensilsCrossed className="h-3 w-3 shrink-0" />
                          <span className="truncate">{recipe.title}</span>
                        </button>
                      ))}
                      <button
                        onClick={() => createRecipe.mutate({ chapter_id: chapter.id, title: "New Recipe" })}
                        className="w-full flex items-center gap-2 rounded-md px-2 py-1 text-left text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
                        <Plus className="h-3 w-3" /> Add Recipe
                      </button>
                    </div>
                  )}
                </div>
              );
            })}

            {(!chapters || chapters.length === 0) && (
              <p className="text-xs text-muted-foreground text-center py-4">No chapters yet</p>
            )}

            <Separator className="my-2" />
            <Button variant="ghost" size="sm" className="w-full justify-start gap-1.5 text-xs"
              onClick={() => createChapter.mutate({ title: "New Chapter" })}>
              <Plus className="h-3.5 w-3.5" /> Add Chapter
            </Button>
          </div>
        </ScrollArea>

        {/* CENTER: Recipe Card Editor */}
        <ScrollArea className="flex-1">
          {selectedRecipe ? (
            <RecipeEditor recipe={selectedRecipe} />
          ) : (
            <CookbookOverview book={book} chapterCount={chapters?.length ?? 0} recipeCount={totalRecipes} />
          )}
        </ScrollArea>

        {/* RIGHT SIDEBAR: Properties & AI Actions */}
        <ScrollArea className="w-64 border-l shrink-0">
          <div className="p-4 space-y-4">
            {/* AI Actions */}
            <div>
              <h3 className="font-semibold text-sm mb-3 flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5" /> AI Actions
              </h3>
              <div className="space-y-2">
                <Button size="sm" variant="outline" className="w-full justify-start gap-2 h-8 text-xs"
                  disabled={!selectedRecipe}
                  onClick={() => {
                    if (!selectedRecipe) return;
                    const chapter = chapters?.find((ch) => ch.recipes?.some((r) => r.id === selectedRecipe.id));
                    if (chapter) generateRecipe.mutate({ chapter_id: chapter.id });
                  }}>
                  <Wand2 className="h-3.5 w-3.5" /> Generate Recipe
                </Button>
                <Button size="sm" variant="outline" className="w-full justify-start gap-2 h-8 text-xs"
                  disabled={!selectedRecipe}
                  onClick={() => selectedRecipe && generateImage.mutate({ recipeId: selectedRecipe.id })}>
                  <ImageIcon className="h-3.5 w-3.5" /> Generate Image
                </Button>
                <Button size="sm" variant="outline" className="w-full justify-start gap-2 h-8 text-xs"
                  disabled={!selectedRecipe}
                  onClick={() => selectedRecipe && improveInstructions.mutate({ recipeId: selectedRecipe.id })}>
                  <FileText className="h-3.5 w-3.5" /> Improve Instructions
                </Button>
                <Button size="sm" variant="outline" className="w-full justify-start gap-2 h-8 text-xs"
                  disabled={!selectedRecipe}
                  onClick={() => selectedRecipe && calculateNutrition.mutate({ recipeId: selectedRecipe.id })}>
                  <Calculator className="h-3.5 w-3.5" /> Calculate Nutrition
                </Button>
                <div className="flex gap-1.5">
                  <Button size="sm" variant="outline" className="flex-1 gap-1.5 h-8 text-xs"
                    disabled={!selectedRecipe}
                    onClick={() => selectedRecipe && scaleRecipe.mutate({ recipeId: selectedRecipe.id, factor: scaleFactor })}>
                    <Scale className="h-3.5 w-3.5" /> Scale
                  </Button>
                  <Select value={String(scaleFactor)} onValueChange={(v) => setScaleFactor(Number(v))}>
                    <SelectTrigger className="w-16 h-8 text-xs"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {SCALE_FACTORS.map((f) => (
                        <SelectItem key={f} value={String(f)}>{f}x</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            <Separator />

            {selectedRecipe ? (
              <>
                {/* Recipe Info */}
                <div>
                  <h3 className="font-semibold text-sm mb-3">Recipe Info</h3>
                  <div className="space-y-2">
                    <div className="space-y-1">
                      <Label className="text-[10px]">Source</Label>
                      <Input className="h-7 text-xs" placeholder="Original source..." defaultValue={selectedRecipe.source ?? ""} />
                    </div>
                    <div className="text-[10px] text-muted-foreground space-y-0.5">
                      <p>Created: {new Date(selectedRecipe.created_at).toLocaleDateString()}</p>
                      <p>Updated: {new Date(selectedRecipe.updated_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Tags */}
                <div>
                  <h3 className="font-semibold text-sm mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {selectedRecipe.tags?.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                    ))}
                    {(!selectedRecipe.tags || selectedRecipe.tags.length === 0) && (
                      <span className="text-[10px] text-muted-foreground">No tags</span>
                    )}
                  </div>
                  <Input className="h-7 text-xs" placeholder="Add tag + Enter"
                    onKeyDown={(e) => { if (e.key === "Enter") e.currentTarget.value = ""; }} />
                </div>

                <Separator />

                {/* Dietary Flags */}
                <div>
                  <h3 className="font-semibold text-sm mb-2">Dietary Flags</h3>
                  <div className="space-y-1.5">
                    {DIETARY_FLAGS.map((flag) => (
                      <label key={flag} className="flex items-center gap-2 text-xs cursor-pointer">
                        <Checkbox checked={selectedRecipe.dietary_flags?.includes(flag)} />
                        {flag}
                      </label>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div>
                <h3 className="font-semibold text-sm mb-2">Cookbook Info</h3>
                <div className="text-[10px] text-muted-foreground space-y-0.5">
                  <p>Cuisine: {book.cuisine ?? "\u2014"}</p>
                  <p>Type: {book.cookbook_type}</p>
                  <p>Created: {new Date(book.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Recipe Editor (Center panel)
// ---------------------------------------------------------------------------

function RecipeEditor({ recipe }: { recipe: CookbookRecipe }) {
  const totalTime = (recipe.prep_time ?? 0) + (recipe.cook_time ?? 0);

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      {/* Image Section */}
      <div className="relative aspect-[16/9] bg-muted rounded-lg overflow-hidden flex items-center justify-center">
        {recipe.image_url ? (
          <img src={recipe.image_url} alt={recipe.title} className="h-full w-full object-cover" />
        ) : (
          <div className="flex flex-col items-center gap-3 text-muted-foreground">
            <ImageIcon className="h-16 w-16" />
            <p className="text-sm">No recipe image</p>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" className="gap-1.5">
                <Wand2 className="h-3.5 w-3.5" /> Generate Image
              </Button>
              <Button size="sm" variant="outline" className="gap-1.5">
                <ImageIcon className="h-3.5 w-3.5" /> Upload Image
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Basic Info */}
      <div className="space-y-4">
        <Input
          className="text-2xl font-bold h-auto py-2 border-none shadow-none focus-visible:ring-0 px-0"
          defaultValue={recipe.title} placeholder="Recipe title..." />
        <Textarea
          className="text-sm resize-none border-none shadow-none focus-visible:ring-0 px-0"
          rows={2} defaultValue={recipe.description ?? ""} placeholder="Short description of this recipe..." />
      </div>

      {/* Time / Servings / Difficulty */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="space-y-1">
          <Label className="text-xs flex items-center gap-1"><Users className="h-3 w-3" /> Servings</Label>
          <Input type="number" className="h-8 text-sm" defaultValue={recipe.servings ?? ""} placeholder="4" />
        </div>
        <div className="space-y-1">
          <Label className="text-xs flex items-center gap-1"><Clock className="h-3 w-3" /> Prep (min)</Label>
          <Input type="number" className="h-8 text-sm" defaultValue={recipe.prep_time ?? ""} placeholder="15" />
        </div>
        <div className="space-y-1">
          <Label className="text-xs flex items-center gap-1"><Flame className="h-3 w-3" /> Cook (min)</Label>
          <Input type="number" className="h-8 text-sm" defaultValue={recipe.cook_time ?? ""} placeholder="30" />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Total</Label>
          <div className="h-8 flex items-center text-sm text-muted-foreground bg-muted rounded-md px-3">
            {totalTime > 0 ? `${totalTime} min` : "\u2014"}
          </div>
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Difficulty</Label>
          <Select defaultValue={recipe.difficulty ?? "easy"}>
            <SelectTrigger className="h-8 text-sm"><SelectValue /></SelectTrigger>
            <SelectContent>
              {DIFFICULTY_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Separator />

      {/* Ingredients */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            Ingredients
            <Badge variant="secondary" className="text-[10px]">{recipe.ingredients?.length ?? 0}</Badge>
          </h3>
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1">
            <Plus className="h-3 w-3" /> Add Ingredient
          </Button>
        </div>
        <div className="space-y-2">
          {recipe.ingredients?.map((ing, idx) => (
            <IngredientRow key={idx} ingredient={ing} />
          ))}
          {(!recipe.ingredients || recipe.ingredients.length === 0) && (
            <p className="text-xs text-muted-foreground py-2">No ingredients added yet.</p>
          )}
        </div>
      </div>

      <Separator />

      {/* Instructions */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            Instructions
            <Badge variant="secondary" className="text-[10px]">{recipe.instructions?.length ?? 0} steps</Badge>
          </h3>
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1">
            <Plus className="h-3 w-3" /> Add Step
          </Button>
        </div>
        <div className="space-y-3">
          {recipe.instructions?.map((step, idx) => (
            <InstructionRow key={idx} step={step} index={idx} />
          ))}
          {(!recipe.instructions || recipe.instructions.length === 0) && (
            <p className="text-xs text-muted-foreground py-2">No instructions added yet.</p>
          )}
        </div>
      </div>

      <Separator />

      {/* Nutrition */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-sm flex items-center gap-1.5">
            <Calculator className="h-3.5 w-3.5" /> Nutrition (per serving)
          </h3>
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1">
            <Calculator className="h-3 w-3" /> Calculate
          </Button>
        </div>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
          {[
            { label: "Calories", value: recipe.nutrition?.calories, unit: "" },
            { label: "Fat", value: recipe.nutrition?.fat, unit: "g" },
            { label: "Protein", value: recipe.nutrition?.protein, unit: "g" },
            { label: "Carbs", value: recipe.nutrition?.carbs, unit: "g" },
            { label: "Fiber", value: recipe.nutrition?.fiber, unit: "g" },
            { label: "Sodium", value: recipe.nutrition?.sodium, unit: "mg" },
          ].map((n) => (
            <div key={n.label} className="space-y-1">
              <Label className="text-[10px]">{n.label}</Label>
              <Input type="number" className="h-7 text-xs" defaultValue={n.value ?? ""} placeholder="\u2014" />
              {n.unit && <span className="text-[9px] text-muted-foreground">{n.unit}</span>}
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Notes & Tips */}
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="space-y-1">
          <Label className="text-xs">Notes</Label>
          <Textarea className="text-xs min-h-[60px]" rows={2} defaultValue={recipe.notes ?? ""} placeholder="Additional notes..." />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Tips</Label>
          <Textarea className="text-xs min-h-[60px]" rows={2} defaultValue={recipe.tips ?? ""} placeholder="Chef tips..." />
        </div>
      </div>

      {/* Variations */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <Label className="text-xs">Variations</Label>
          <Button variant="ghost" size="sm" className="h-6 text-[10px] gap-1">
            <Plus className="h-3 w-3" /> Add
          </Button>
        </div>
        <div className="space-y-1.5">
          {recipe.variations?.map((v, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <Input className="h-7 text-xs flex-1" defaultValue={v} />
              <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0">
                <Trash2 className="h-3 w-3 text-muted-foreground" />
              </Button>
            </div>
          ))}
          {(!recipe.variations || recipe.variations.length === 0) && (
            <p className="text-[10px] text-muted-foreground">No variations added.</p>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Ingredient Row
// ---------------------------------------------------------------------------

function IngredientRow({ ingredient }: { ingredient: CookbookIngredient }) {
  return (
    <div className="flex items-center gap-2 group">
      <GripVertical className="h-3 w-3 text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100 cursor-grab" />
      <Input className="h-7 text-xs w-16 shrink-0" defaultValue={ingredient.amount} placeholder="Amt" />
      <Select defaultValue={ingredient.unit || "cups"}>
        <SelectTrigger className="h-7 text-xs w-20 shrink-0"><SelectValue /></SelectTrigger>
        <SelectContent>
          {UNIT_OPTIONS.map((u) => <SelectItem key={u} value={u}>{u}</SelectItem>)}
        </SelectContent>
      </Select>
      <Input className="h-7 text-xs flex-1" defaultValue={ingredient.name} placeholder="Ingredient name" />
      <Input className="h-7 text-xs w-32 shrink-0" defaultValue={ingredient.notes ?? ""} placeholder="Notes" />
      <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0 opacity-0 group-hover:opacity-100">
        <Trash2 className="h-3 w-3 text-muted-foreground" />
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Instruction Row
// ---------------------------------------------------------------------------

function InstructionRow({ step, index }: { step: CookbookInstruction; index: number }) {
  return (
    <div className="flex gap-3 group">
      <div className="flex flex-col items-center gap-1 pt-1">
        <GripVertical className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 cursor-grab" />
        <div className="h-6 w-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-semibold shrink-0">
          {index + 1}
        </div>
      </div>
      <div className="flex-1 space-y-1.5">
        <Textarea className="text-xs min-h-[48px]" rows={2} defaultValue={step.text} placeholder="Describe this step..." />
        {step.tip && (
          <div className="text-[10px] text-muted-foreground bg-muted/50 rounded px-2 py-1">
            Tip: {step.tip}
          </div>
        )}
      </div>
      <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0 opacity-0 group-hover:opacity-100 mt-1">
        <Trash2 className="h-3 w-3 text-muted-foreground" />
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Cookbook Overview (when no recipe selected)
// ---------------------------------------------------------------------------

function CookbookOverview({
  book,
  chapterCount,
  recipeCount,
}: {
  book: { title: string; description?: string };
  chapterCount: number;
  recipeCount: number;
}) {
  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="text-center py-12 space-y-4">
        <BookOpen className="h-16 w-16 text-muted-foreground mx-auto" />
        <h2 className="text-xl font-semibold">{book.title}</h2>
        {book.description && (
          <p className="text-sm text-muted-foreground max-w-md mx-auto">{book.description}</p>
        )}
        <div className="flex items-center justify-center gap-6 text-sm text-muted-foreground">
          <span>{chapterCount} chapters</span>
          <span>{recipeCount} recipes</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Select a recipe from the left panel to begin editing, or add a new chapter to get started.
        </p>
      </div>
    </div>
  );
}

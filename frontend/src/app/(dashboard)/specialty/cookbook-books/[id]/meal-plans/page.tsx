"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, Plus, Calendar, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { MealPlanBuilder } from "@/modules/specialty/cookbook/components/MealPlanBuilder";
import { ShoppingList, type ShoppingListItem } from "@/modules/specialty/cookbook/components/ShoppingList";
import {
  useCookbook,
  useMealPlans,
  useChapterRecipes,
  useCreateMealPlan,
} from "@/modules/specialty/cookbook/hooks";

export default function MealPlansPage() {
  const params = useParams();
  const cookbookId = params.id as string;

  const { data: cookbook, isLoading: loadingCookbook } = useCookbook(cookbookId);
  const { data: recipes, isLoading: loadingRecipes } = useChapterRecipes(cookbookId);
  const { data: mealPlans } = useMealPlans(cookbookId);
  const saveMutation = useCreateMealPlan(cookbookId);

  const [activeTab, setActiveTab] = useState("builder");
  const [shoppingItems, setShoppingItems] = useState<ShoppingListItem[]>([]);

  const handleSave = useCallback(
    (plan: { title: string; type: string; calorieTarget: number; weeks: unknown }) => {
      // The API takes title/plan_type/description; the wizard's calorie target
      // and week layout have no field on CookbookMealPlan yet.
      saveMutation.mutate({ title: plan.title, plan_type: plan.type });
    },
    [saveMutation],
  );

  const handleGenerateShoppingList = useCallback((_weeks: unknown) => {
    const mockItems: ShoppingListItem[] = [
      { name: "Chicken Breast", amount: "2", unit: "lbs", category: "Meat & Seafood", checked: false },
      { name: "Broccoli", amount: "3", unit: "heads", category: "Produce", checked: false },
      { name: "Brown Rice", amount: "2", unit: "cups", category: "Pantry", checked: false },
      { name: "Olive Oil", amount: "1", unit: "bottle", category: "Pantry", checked: false },
      { name: "Eggs", amount: "12", unit: "ct", category: "Dairy", checked: false },
      { name: "Whole Wheat Bread", amount: "1", unit: "loaf", category: "Bakery", checked: false },
      { name: "Frozen Berries", amount: "1", unit: "bag", category: "Frozen", checked: false },
      { name: "Orange Juice", amount: "1", unit: "carton", category: "Beverages", checked: false },
      { name: "Spinach", amount: "1", unit: "bag", category: "Produce", checked: false },
      { name: "Greek Yogurt", amount: "2", unit: "cups", category: "Dairy", checked: false },
      { name: "Salmon Fillets", amount: "1", unit: "lb", category: "Meat & Seafood", checked: false },
      { name: "Garlic", amount: "1", unit: "head", category: "Produce", checked: false },
    ];
    setShoppingItems(mockItems);
    setActiveTab("shopping");
  }, []);

  const toggleItem = useCallback((index: number) => {
    setShoppingItems((prev) => prev.map((item, i) => (i === index ? { ...item, checked: !item.checked } : item)));
  }, []);

  const handlePrint = useCallback(() => { window.print(); }, []);

  const handleExport = useCallback(() => {
    const lines = shoppingItems.map(
      (item) => (item.checked ? "[x] " : "[ ] ") + item.amount + " " + item.unit + " " + item.name + " (" + item.category + ")",
    );
    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "shopping-list.txt";
    a.click();
    URL.revokeObjectURL(url);
  }, [shoppingItems]);

  if (loadingCookbook || loadingRecipes) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-[500px] w-full" />
      </div>
    );
  }

  const recipeList = (recipes ?? []).map((r) => ({
    id: r.id,
    title: r.title,
    calories: r.nutrition?.calories,
  }));

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 border-b flex items-center gap-3 px-4 shrink-0">
        <Button variant="ghost" size="sm" className="gap-1.5" asChild>
          <Link href={"/specialty/cookbook-books/" + cookbookId}>
            <ChevronLeft className="h-4 w-4" /> Back to Cookbook
          </Link>
        </Button>
        <div className="h-6 w-px bg-border" />
        <h1 className="text-base font-semibold truncate">
          {(cookbook?.title ?? "Cookbook") + " \u2014 Meal Plans"}
        </h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
        <div className="border-b px-4">
          <TabsList className="h-10">
            <TabsTrigger value="builder" className="gap-1.5"><Calendar className="h-3.5 w-3.5" /> Meal Plan Builder</TabsTrigger>
            <TabsTrigger value="plans" className="gap-1.5"><Plus className="h-3.5 w-3.5" /> {"Saved Plans (" + (mealPlans?.length ?? 0) + ")"}</TabsTrigger>
            <TabsTrigger value="shopping" className="gap-1.5"><ShoppingCart className="h-3.5 w-3.5" /> Shopping List</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="builder" className="flex-1 overflow-auto m-0 p-6">
          <div className="max-w-6xl mx-auto">
            <MealPlanBuilder cookbookId={cookbookId} recipes={recipeList} onSave={handleSave} onGenerateShoppingList={handleGenerateShoppingList} />
          </div>
        </TabsContent>

        <TabsContent value="plans" className="flex-1 overflow-auto m-0 p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Saved Meal Plans</h2>
                <p className="text-sm text-muted-foreground">Previously created meal plans for this cookbook.</p>
              </div>
              <Button size="sm" className="gap-1.5" onClick={() => setActiveTab("builder")}><Plus className="h-4 w-4" /> New Plan</Button>
            </div>
            {mealPlans && mealPlans.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {mealPlans.map((plan) => (
                  <Card key={plan.id} className="cursor-pointer hover:shadow-sm transition-shadow">
                    <CardHeader className="pb-2"><CardTitle className="text-base">{plan.title}</CardTitle></CardHeader>
                    <CardContent className="space-y-1 text-sm text-muted-foreground">
                      <p>{"Type: " + plan.plan_type}</p>
                      <p>{"Target: " + plan.total_calories_target + " cal/day"}</p>
                      <p className="text-xs">{"Created " + new Date(plan.created_at).toLocaleDateString()}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="p-8 text-center">
                <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <h3 className="font-medium">No saved meal plans</h3>
                <p className="text-sm text-muted-foreground mt-1">Use the Meal Plan Builder to create your first plan.</p>
                <Button size="sm" className="mt-4 gap-1.5" onClick={() => setActiveTab("builder")}><Plus className="h-4 w-4" /> Create Meal Plan</Button>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="shopping" className="flex-1 overflow-auto m-0 p-6">
          <div className="max-w-2xl mx-auto">
            {shoppingItems.length > 0 ? (
              <ShoppingList items={shoppingItems} onToggle={toggleItem} onPrint={handlePrint} onExport={handleExport} />
            ) : (
              <Card className="p-8 text-center">
                <ShoppingCart className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <h3 className="font-medium">No shopping list yet</h3>
                <p className="text-sm text-muted-foreground mt-1">Generate a shopping list from the Meal Plan Builder.</p>
                <Button size="sm" className="mt-4 gap-1.5" onClick={() => setActiveTab("builder")}><Calendar className="h-4 w-4" /> Go to Builder</Button>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
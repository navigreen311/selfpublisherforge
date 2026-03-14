"use client";

import { useState, useMemo, useCallback } from "react";
import {
  Calendar, Plus, Trash2, Wand2, ShoppingCart,
  ChevronLeft, ChevronRight, Coffee, Sun, Moon, Cookie,
  AlertTriangle, X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type MealType = "breakfast" | "lunch" | "dinner" | "snack";

interface MealSlot {
  meal: MealType;
  recipeId?: string;
  recipeName?: string;
  calories?: number;
}

interface DayPlan {
  day: string;
  meals: MealSlot[];
}

interface MealPlanBuilderProps {
  cookbookId: string;
  planId?: string;
  recipes: Array<{ id: string; title: string; calories?: number }>;
  onSave?: (plan: { title: string; type: string; calorieTarget: number; weeks: DayPlan[][] }) => void;
  onGenerateShoppingList?: (weeks: DayPlan[][]) => void;
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const MEAL_TYPES: { key: MealType; label: string; icon: typeof Coffee }[] = [
  { key: "breakfast", label: "Breakfast", icon: Coffee },
  { key: "lunch", label: "Lunch", icon: Sun },
  { key: "dinner", label: "Dinner", icon: Moon },
  { key: "snack", label: "Snack", icon: Cookie },
];

const PLAN_TYPES = [
  { value: "weekly", label: "Weekly", weeks: 1 },
  { value: "biweekly", label: "Biweekly", weeks: 2 },
  { value: "monthly", label: "Monthly", weeks: 4 },
];

function createEmptyWeek(): DayPlan[] {
  return DAYS.map((day) => ({ day, meals: MEAL_TYPES.map((mt) => ({ meal: mt.key })) }));
}

function MealSlotCard({ slot, recipes, onAssign, onRemove }: {
  slot: MealSlot; recipes: MealPlanBuilderProps["recipes"];
  onAssign: (recipeId: string) => void; onRemove: () => void;
}) {
  const [picking, setPicking] = useState(false);
  const meta = MEAL_TYPES.find((m) => m.key === slot.meal)!;
  const Icon = meta.icon;

  if (slot.recipeId && slot.recipeName) {
    return (
      <Card className="group relative border bg-card hover:shadow-sm transition-shadow">
        <CardContent className="p-2 space-y-1">
          <div className="flex items-start gap-1.5">
            <Icon className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
            <span className="text-xs font-medium leading-tight line-clamp-2">{slot.recipeName}</span>
          </div>
          {slot.calories != null && (
            <Badge variant="secondary" className="text-[10px] h-4 px-1">{slot.calories} cal</Badge>
          )}
          <button onClick={onRemove} className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity h-5 w-5 rounded-sm bg-destructive/10 hover:bg-destructive/20 flex items-center justify-center">
            <X className="h-3 w-3 text-destructive" />
          </button>
        </CardContent>
      </Card>
    );
  }

  if (picking) {
    return (
      <div className="border border-dashed rounded-lg p-1">
        <Select onValueChange={(val) => { onAssign(val); setPicking(false); }}>
          <SelectTrigger className="h-7 text-xs"><SelectValue placeholder="Pick recipe..." /></SelectTrigger>
          <SelectContent>
            {recipes.map((r) => (<SelectItem key={r.id} value={r.id}>{r.title}</SelectItem>))}
          </SelectContent>
        </Select>
        <Button variant="ghost" size="sm" className="w-full h-6 text-[10px] mt-0.5" onClick={() => setPicking(false)}>Cancel</Button>
      </div>
    );
  }

  return (
    <button onClick={() => setPicking(true)} className="w-full border border-dashed rounded-lg p-3 flex flex-col items-center justify-center gap-1 text-muted-foreground hover:border-primary/50 hover:text-primary transition-colors min-h-[60px]">
      <Plus className="h-4 w-4" />
      <span className="text-[10px]">Add</span>
    </button>
  );
}

interface DayWarning { day: string; message: string; }

function validateWeek(week: DayPlan[], calorieTarget: number): DayWarning[] {
  const warnings: DayWarning[] = [];
  for (const dayPlan of week) {
    const assigned = dayPlan.meals.filter((m) => m.recipeId);
    const totalCal = assigned.reduce((s, m) => s + (m.calories ?? 0), 0);
    if (assigned.length === 0) warnings.push({ day: dayPlan.day, message: "No meals assigned" });
    if (calorieTarget > 0 && totalCal > calorieTarget * 1.2)
      warnings.push({ day: dayPlan.day, message: "Exceeds target by >20% (" + totalCal + " cal)" });
    if (calorieTarget > 0 && assigned.length > 0 && totalCal < calorieTarget * 0.7)
      warnings.push({ day: dayPlan.day, message: "Below target by >30% (" + totalCal + " cal)" });
  }
  const recipeCounts: Record<string, number> = {};
  for (const dp of week) for (const m of dp.meals) if (m.recipeId) recipeCounts[m.recipeId] = (recipeCounts[m.recipeId] ?? 0) + 1;
  for (const [, count] of Object.entries(recipeCounts)) {
    if (count > 3) { warnings.push({ day: "Week", message: "Same recipe used more than 3 times" }); break; }
  }
  return warnings;
}

export function MealPlanBuilder({ cookbookId, planId, recipes, onSave, onGenerateShoppingList }: MealPlanBuilderProps) {
  const [title, setTitle] = useState(planId ? "My Meal Plan" : "New Meal Plan");
  const [planType, setPlanType] = useState("weekly");
  const [calorieTarget, setCalorieTarget] = useState(2000);
  const [currentWeekIndex, setCurrentWeekIndex] = useState(0);
  const totalWeeks = PLAN_TYPES.find((p) => p.value === planType)?.weeks ?? 1;
  const [weeks, setWeeks] = useState<DayPlan[][]>(() => Array.from({ length: 4 }, () => createEmptyWeek()));
  const currentWeek = weeks[currentWeekIndex];
  const warnings = useMemo(() => validateWeek(currentWeek, calorieTarget), [currentWeek, calorieTarget]);

  const updateSlot = useCallback((dayIndex: number, mealIndex: number, recipeId: string | undefined) => {
    setWeeks((prev) => {
      const next = prev.map((w) => w.map((d) => ({ ...d, meals: [...d.meals] })));
      const recipe = recipeId ? recipes.find((r) => r.id === recipeId) : undefined;
      next[currentWeekIndex][dayIndex].meals[mealIndex] = {
        meal: next[currentWeekIndex][dayIndex].meals[mealIndex].meal,
        recipeId: recipe?.id, recipeName: recipe?.title, calories: recipe?.calories,
      };
      return next;
    });
  }, [currentWeekIndex, recipes]);

  const clearAll = useCallback(() => {
    setWeeks((prev) => { const next = [...prev]; next[currentWeekIndex] = createEmptyWeek(); return next; });
  }, [currentWeekIndex]);

  const autoFill = useCallback(() => {
    setWeeks((prev) => {
      const next = prev.map((w) => w.map((d) => ({ ...d, meals: [...d.meals] })));
      for (const dayPlan of next[currentWeekIndex]) {
        for (let i = 0; i < dayPlan.meals.length; i++) {
          if (!dayPlan.meals[i].recipeId && recipes.length > 0) {
            const recipe = recipes[Math.floor(Math.random() * recipes.length)];
            dayPlan.meals[i] = { meal: dayPlan.meals[i].meal, recipeId: recipe.id, recipeName: recipe.title, calories: recipe.calories };
          }
        }
      }
      return next;
    });
  }, [currentWeekIndex, recipes]);

  const dailyTotals = currentWeek.map((d) => d.meals.reduce((s, m) => s + (m.calories ?? 0), 0));
  const weeklyAvg = dailyTotals.reduce((s, v) => s + v, 0) / 7;

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1 flex-1 min-w-[200px]">
              <Label className="text-xs">Plan Title</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} className="h-8 text-sm" />
            </div>
            <div className="space-y-1 w-[140px]">
              <Label className="text-xs">Plan Type</Label>
              <Select value={planType} onValueChange={setPlanType}>
                <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {PLAN_TYPES.map((pt) => (<SelectItem key={pt.value} value={pt.value}>{pt.label}</SelectItem>))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1 w-[120px]">
              <Label className="text-xs">Daily Calorie Target</Label>
              <Input type="number" value={calorieTarget} onChange={(e) => setCalorieTarget(Number(e.target.value))} className="h-8 text-sm" />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <Button size="sm" variant="outline" className="gap-1.5" onClick={autoFill}><Wand2 className="h-3.5 w-3.5" /> Auto-Fill</Button>
              <Button size="sm" variant="outline" className="gap-1.5" onClick={() => onGenerateShoppingList?.(weeks.slice(0, totalWeeks))}><ShoppingCart className="h-3.5 w-3.5" /> Shopping List</Button>
              <Button size="sm" variant="outline" className="gap-1.5 text-destructive hover:text-destructive" onClick={clearAll}><Trash2 className="h-3.5 w-3.5" /> Clear All</Button>
              {onSave && (<Button size="sm" className="gap-1.5" onClick={() => onSave({ title, type: planType, calorieTarget, weeks: weeks.slice(0, totalWeeks) })}>Save Plan</Button>)}
            </div>
          </div>
        </CardContent>
      </Card>

      {totalWeeks > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button variant="ghost" size="icon" className="h-8 w-8" disabled={currentWeekIndex === 0} onClick={() => setCurrentWeekIndex((i) => i - 1)}><ChevronLeft className="h-4 w-4" /></Button>
          <span className="text-sm font-medium">{"Week " + (currentWeekIndex + 1) + " of " + totalWeeks}</span>
          <Button variant="ghost" size="icon" className="h-8 w-8" disabled={currentWeekIndex >= totalWeeks - 1} onClick={() => setCurrentWeekIndex((i) => i + 1)}><ChevronRight className="h-4 w-4" /></Button>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {warnings.map((w, i) => (
            <Badge key={i} variant="outline" className="gap-1 text-amber-600 border-amber-300 bg-amber-50">
              <AlertTriangle className="h-3 w-3" /> {w.day}: {w.message}
            </Badge>
          ))}
        </div>
      )}

      <div className="overflow-x-auto">
        <div className="min-w-[800px]">
          <div className="grid grid-cols-8 gap-2 mb-2">
            <div className="text-xs font-semibold text-muted-foreground p-2" />
            {DAYS.map((day) => (<div key={day} className="text-xs font-semibold text-center p-2">{day}</div>))}
          </div>
          {MEAL_TYPES.map((mt, mealIndex) => {
            const Icon = mt.icon;
            return (
              <div key={mt.key} className="grid grid-cols-8 gap-2 mb-2">
                <div className="flex items-center gap-1.5 p-2">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  <span className="text-xs font-medium">{mt.label}</span>
                </div>
                {currentWeek.map((dayPlan, dayIndex) => (
                  <div key={dayPlan.day}>
                    <MealSlotCard slot={dayPlan.meals[mealIndex]} recipes={recipes} onAssign={(rid) => updateSlot(dayIndex, mealIndex, rid)} onRemove={() => updateSlot(dayIndex, mealIndex, undefined)} />
                  </div>
                ))}
              </div>
            );
          })}
          <div className="grid grid-cols-8 gap-2 border-t pt-2">
            <div className="flex items-center p-2"><span className="text-xs font-semibold text-muted-foreground">Daily Total</span></div>
            {dailyTotals.map((total, i) => (
              <div key={i} className="text-center p-2">
                <span className={cn("text-xs font-semibold", calorieTarget > 0 && total > calorieTarget * 1.2 ? "text-red-500" : calorieTarget > 0 && total > 0 && total < calorieTarget * 0.7 ? "text-amber-500" : "text-foreground")}>
                  {total > 0 ? total + " cal" : "\u2014"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground px-2">
        <span>{"Weekly average: "}<strong className="text-foreground">{Math.round(weeklyAvg)} cal/day</strong></span>
        <span className="flex items-center gap-1.5"><Calendar className="h-3.5 w-3.5" /> {recipes.length} recipes available</span>
      </div>
    </div>
  );
}
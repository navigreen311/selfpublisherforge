"use client";

import * as React from "react";
import Link from "next/link";
import { Eye, EyeOff, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";

const plans = [
  { id: "free", name: "Free", description: "Get started with basics", price: "$0" },
  { id: "starter", name: "Starter", description: "For individual authors", price: "$19/mo" },
  { id: "pro", name: "Pro", description: "For professional publishers", price: "$49/mo" },
  { id: "business", name: "Business", description: "For publishing teams", price: "$99/mo" },
];

export default function RegisterPage() {
  const { register, isLoading } = useAuth();
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [orgName, setOrgName] = React.useState("");
  const [plan, setPlan] = React.useState("free");
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError] = React.useState("");

  const passwordChecks = {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
  };

  const isPasswordValid = Object.values(passwordChecks).every(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!isPasswordValid) {
      setError("Please meet all password requirements");
      return;
    }
    try {
      await register({ name, email, password, orgName, planTier: plan });
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Registration failed. Please try again."
      );
    }
  };

  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">Create your account</CardTitle>
        <CardDescription>Start your self-publishing journey today</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Input
            label="Full Name"
            placeholder="John Doe"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoComplete="name"
          />

          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Create a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            {password && (
              <div className="grid grid-cols-2 gap-1 mt-2">
                {[
                  { key: "minLength", label: "8+ characters" },
                  { key: "hasUppercase", label: "Uppercase letter" },
                  { key: "hasLowercase", label: "Lowercase letter" },
                  { key: "hasNumber", label: "Number" },
                ].map(({ key, label }) => (
                  <div
                    key={key}
                    className={cn(
                      "flex items-center gap-1 text-xs",
                      passwordChecks[key as keyof typeof passwordChecks]
                        ? "text-green-600"
                        : "text-muted-foreground"
                    )}
                  >
                    <Check className="h-3 w-3" />
                    {label}
                  </div>
                ))}
              </div>
            )}
          </div>

          <Input
            label="Organization Name"
            placeholder="My Publishing House (optional)"
            value={orgName}
            onChange={(e) => setOrgName(e.target.value)}
            helperText="You can change this later"
          />

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Plan</label>
            <Select value={plan} onValueChange={setPlan}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {plans.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    <span className="flex items-center gap-2">
                      <span className="font-medium">{p.name}</span>
                      <span className="text-muted-foreground">
                        - {p.price}
                      </span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !isPasswordValid}
          >
            {isLoading ? "Creating account..." : "Create account"}
          </Button>
          <p className="text-sm text-muted-foreground text-center">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}

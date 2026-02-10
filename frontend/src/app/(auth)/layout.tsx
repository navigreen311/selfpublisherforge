import { BookOpen } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      {/* Left: Branding panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary flex-col justify-between p-12 text-primary-foreground">
        <div className="flex items-center gap-2">
          <BookOpen className="h-8 w-8" />
          <span className="text-xl font-bold">SelfPublisherForge</span>
        </div>
        <div className="space-y-4">
          <h1 className="text-4xl font-bold leading-tight">
            Your complete
            <br />
            self-publishing
            <br />
            command center.
          </h1>
          <p className="text-lg text-primary-foreground/80 max-w-md">
            AI-powered tools to research, write, publish, and market your books
            -- all in one platform.
          </p>
        </div>
        <p className="text-sm text-primary-foreground/60">
          Trusted by 10,000+ self-published authors worldwide
        </p>
      </div>

      {/* Right: Auth form */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-lg">
          <div className="lg:hidden flex items-center justify-center gap-2 mb-8">
            <BookOpen className="h-6 w-6 text-primary" />
            <span className="text-lg font-bold">SelfPublisherForge</span>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}

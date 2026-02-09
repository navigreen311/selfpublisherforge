import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-4">SelfPublisherForge</h1>
      <p className="text-muted-foreground text-lg mb-8">
        AI-powered self-publishing platform
      </p>
      <div className="flex gap-4">
        <Link
          href="/login"
          className="bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:opacity-90"
        >
          Sign In
        </Link>
        <Link
          href="/register"
          className="border border-border px-6 py-3 rounded-lg hover:bg-accent"
        >
          Get Started
        </Link>
      </div>
    </main>
  );
}

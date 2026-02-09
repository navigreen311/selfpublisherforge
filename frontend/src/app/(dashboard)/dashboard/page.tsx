export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Dashboard cards will be populated by various modules */}
        <div className="border rounded-lg p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Total Books</h3>
          <p className="text-3xl font-bold mt-2">-</p>
        </div>
        <div className="border rounded-lg p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Monthly Revenue</h3>
          <p className="text-3xl font-bold mt-2">-</p>
        </div>
        <div className="border rounded-lg p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Active Campaigns</h3>
          <p className="text-3xl font-bold mt-2">-</p>
        </div>
        <div className="border rounded-lg p-6">
          <h3 className="text-sm font-medium text-muted-foreground">AI Tasks</h3>
          <p className="text-3xl font-bold mt-2">-</p>
        </div>
      </div>
    </div>
  );
}

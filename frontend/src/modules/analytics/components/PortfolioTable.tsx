"use client";

interface BookData {
  title: string;
  revenue: number;
  units: number;
  book_id?: string;
}

interface PortfolioTableProps {
  books: BookData[];
  title?: string;
}

export function PortfolioTable({ books, title = "Top Books" }: PortfolioTableProps) {
  if (!books || books.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="mt-4 text-gray-500 text-center py-4">No book data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead>
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Title
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Revenue
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Units
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Avg/Unit
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {books.map((book, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900 font-medium max-w-xs truncate">
                  {book.title}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right">
                  ${Number(book.revenue).toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right">
                  {book.units.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500 text-right">
                  $
                  {book.units > 0
                    ? (Number(book.revenue) / book.units).toFixed(2)
                    : "0.00"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

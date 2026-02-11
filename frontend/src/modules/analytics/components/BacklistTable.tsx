"use client";

import { type BookSummary } from "../hooks";

interface BacklistTableProps {
  books: BookSummary[];
}

export function BacklistTable({ books }: BacklistTableProps) {
  if (!books || books.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Backlist Performance</h3>
        <p className="text-gray-500 text-center py-8">No books in your portfolio yet</p>
      </div>
    );
  }

  const getRecommendation = (book: BookSummary) => {
    const { roi, monthly_revenue, status } = book;

    if (status !== "active") {
      return { label: "Inactive", color: "text-gray-500 bg-gray-100" };
    }

    if (roi > 200 && monthly_revenue > 100) {
      return { label: "Scale", color: "text-green-700 bg-green-100" };
    } else if (roi < 0 && monthly_revenue < 10) {
      return { label: "Kill", color: "text-red-700 bg-red-100" };
    } else if (roi < 50 && monthly_revenue < 50) {
      return { label: "Revive", color: "text-orange-700 bg-orange-100" };
    } else {
      return { label: "Maintain", color: "text-blue-700 bg-blue-100" };
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900">Backlist Performance</h3>
        <p className="text-sm text-gray-500 mt-1">Book-by-book ROI and recommendations</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-y border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Title
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Genre
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Lifetime Revenue
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Monthly Revenue
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Units/Month
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                ROI
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {books.map((book) => {
              const recommendation = getRecommendation(book);
              return (
                <tr key={book.book_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{book.title}</div>
                    {book.launch_date && (
                      <div className="text-xs text-gray-500">
                        Launched: {new Date(book.launch_date).toLocaleDateString()}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-600 capitalize">{book.genre}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className="text-sm font-semibold text-gray-900">
                      ${book.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className="text-sm text-gray-900">
                      ${book.monthly_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className="text-sm text-gray-900">{book.monthly_units}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className={`text-sm font-semibold ${book.roi > 0 ? "text-green-600" : "text-red-600"}`}>
                      {book.roi.toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${recommendation.color}`}>
                      {recommendation.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
        <div className="flex justify-between text-sm">
          <div>
            <span className="font-medium text-gray-700">Total: </span>
            <span className="text-gray-900">{books.length} books</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Lifetime Revenue: </span>
            <span className="text-gray-900 font-semibold">
              ${books.reduce((sum, b) => sum + b.total_revenue, 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Monthly Revenue: </span>
            <span className="text-gray-900 font-semibold">
              ${books.reduce((sum, b) => sum + b.monthly_revenue, 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

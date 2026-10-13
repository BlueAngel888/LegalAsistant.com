'use client';

import { AnalysisResult } from '@/lib/types';
import { AlertCircle, CheckCircle, AlertTriangle, TrendingDown } from 'lucide-react';
import { formatDate } from '@/lib/utils';

interface AnalysisResultProps {
  analysis: AnalysisResult;
}

export function AnalysisResultComponent({ analysis }: AnalysisResultProps) {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'MEDIUM':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'HIGH':
        return 'bg-orange-50 border-orange-200 text-orange-800';
      case 'CRITICAL':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'LOW':
        return <CheckCircle className="w-5 h-5" />;
      case 'CRITICAL':
        return <AlertCircle className="w-5 h-5" />;
      case 'HIGH':
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <TrendingDown className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm text-gray-600 mb-2">Document Type</h3>
            <p className="text-xl font-semibold text-gray-900">
              {analysis.documentType.replace(/_/g, ' ')}
            </p>
          </div>
          <div>
            <h3 className="text-sm text-gray-600 mb-2">Jurisdiction</h3>
            <p className="text-xl font-semibold text-gray-900">
              {analysis.jurisdiction}
            </p>
          </div>
        </div>
      </div>

      {/* Risk Assessment */}
      <div className={`card p-6 border-2 ${getRiskColor(analysis.riskLevel)}`}>
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">{getRiskIcon(analysis.riskLevel)}</div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold mb-2">Risk Level: {analysis.riskLevel}</h3>
            <p className="opacity-75">{analysis.summary}</p>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">Analysis Summary</h3>
        <p className="text-gray-700 leading-relaxed">{analysis.summary}</p>
        <p className="text-xs text-gray-500 mt-4">
          Analyzed on {formatDate(analysis.createdAt)}
        </p>
      </div>

      {/* Strengths */}
      {analysis.strengths.length > 0 && (
        <div className="card p-6 border-l-4 border-green-500">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Strengths</h3>
          <ul className="space-y-3">
            {analysis.strengths.map((strength, idx) => (
              <li key={idx} className="flex gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">{strength}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Weaknesses */}
      {analysis.weaknesses.length > 0 && (
        <div className="card p-6 border-l-4 border-yellow-500">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Weaknesses</h3>
          <ul className="space-y-3">
            {analysis.weaknesses.map((weakness, idx) => (
              <li key={idx} className="flex gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">{weakness}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Legal Errors */}
      {analysis.legalErrors.length > 0 && (
        <div className="card p-6 border-l-4 border-red-500">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Legal Issues</h3>
          <ul className="space-y-3">
            {analysis.legalErrors.map((error, idx) => (
              <li key={idx} className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">{error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Defense Strategy */}
      {analysis.defenseStrategy.length > 0 && (
        <div className="card p-6 border-l-4 border-blue-500">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Defense Strategy</h3>
          <ol className="space-y-3 list-decimal list-inside">
            {analysis.defenseStrategy.map((strategy, idx) => (
              <li key={idx} className="text-gray-700">
                {strategy}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Recommendations */}
      {analysis.recommendations.length > 0 && (
        <div className="card p-6 border-l-4 border-purple-500">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Recommendations</h3>
          <ul className="space-y-3">
            {analysis.recommendations.map((rec, idx) => (
              <li key={idx} className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                  {idx + 1}
                </span>
                <span className="text-gray-700 pt-0.5">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metadata */}
      <div className="text-xs text-gray-500 space-y-1">
        <p>Analysis ID: {analysis.id}</p>
        <p>Language: {analysis.language.toUpperCase()}</p>
        <p>Created: {formatDate(analysis.createdAt)}</p>
      </div>
    </div>
  );
}

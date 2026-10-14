'use client';

import type { AnalysisPoint, AnalysisResult, ComplianceStatus } from '@/lib/types';
import { AlertCircle, CheckCircle, AlertTriangle, TrendingDown, Scale } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import { localeInfo } from '@/lib/i18n/config';
import { useI18n } from './I18nProvider';

interface AnalysisResultProps {
  analysis: AnalysisResult;
}

const US_STATES: Record<string, string> = { NY: 'New York', CA: 'California', TX: 'Texas' };

/** "EU_RO" → "România", "USA_CA" → "United States – California", in the visitor's language. */
function jurisdictionName(code: string, tag: string): string {
  const [prefix, region] = code.split('_');
  let regions: Intl.DisplayNames | null = null;
  try {
    regions = new Intl.DisplayNames([tag], { type: 'region' });
  } catch {
    return code;
  }
  if (prefix === 'EU' && region) return regions.of(region) ?? code;
  if (prefix === 'USA') {
    const us = regions.of('US') ?? 'USA';
    return region ? `${us} – ${US_STATES[region] ?? region}` : us;
  }
  return code === 'UNKNOWN' ? '—' : code;
}

const complianceStyle: Record<ComplianceStatus, string> = {
  COMPLIANT: 'bg-green-400/10 !border-green-400/40 text-green-300',
  NON_COMPLIANT: 'bg-red-400/10 !border-red-400/40 text-red-300',
  UNCLEAR: 'bg-yellow-400/10 !border-yellow-400/40 text-yellow-300',
};

/** The legal basis and, for assessed clauses, whether the clause complies with it. */
function PointLaw({ point }: { point: AnalysisPoint }) {
  const { t } = useI18n();
  if (!point.legalBasis && !point.status) return null;

  return (
    <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
      {point.status && (
        <span className={`rounded-full border px-2 py-0.5 font-medium ${complianceStyle[point.status]}`}>
          {t.compliance[point.status]}
        </span>
      )}
      {point.legalBasis && (
        <span className="inline-flex items-center gap-1 text-slate-400">
          <Scale className="w-3.5 h-3.5" />
          {t.analysis.legalBasis}: <span className="text-slate-300">{point.legalBasis}</span>
        </span>
      )}
    </div>
  );
}

export function AnalysisResultComponent({ analysis }: AnalysisResultProps) {
  const { locale, t } = useI18n();
  const dateTag = localeInfo[locale].tag;

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW':
        return 'bg-green-400/10 !border-green-400/40 text-green-300';
      case 'MEDIUM':
        return 'bg-yellow-400/10 !border-yellow-400/40 text-yellow-300';
      case 'HIGH':
        return 'bg-orange-400/10 !border-orange-400/40 text-orange-300';
      case 'CRITICAL':
        return 'bg-red-400/10 !border-red-400/40 text-red-300';
      default:
        return 'bg-white/5 text-slate-100';
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
            <h3 className="text-sm text-slate-300 mb-2">{t.analysis.documentType}</h3>
            <p className="text-xl font-semibold text-white">
              {t.documentTypes[analysis.documentType] ?? analysis.documentType.replace(/_/g, ' ')}
            </p>
          </div>
          <div>
            <h3 className="text-sm text-slate-300 mb-2">{t.analysis.jurisdiction}</h3>
            <p className="text-xl font-semibold text-white">
              {jurisdictionName(analysis.jurisdiction, dateTag)}
            </p>
          </div>
        </div>
      </div>

      {/* Risk Assessment */}
      <div className={`card p-6 border-2 ${getRiskColor(analysis.riskLevel)}`}>
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0">{getRiskIcon(analysis.riskLevel)}</div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold">{t.analysis.riskLevel}: {t.risk[analysis.riskLevel] ?? analysis.riskLevel}</h3>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4 text-white">{t.analysis.summary}</h3>
        <p className="text-slate-200 leading-relaxed">{analysis.summary}</p>
        <p className="text-xs text-slate-400 mt-4">
          {t.analysis.analyzedOn} {formatDate(analysis.createdAt, dateTag)}
        </p>
      </div>

      {/* Strengths */}
      {analysis.strengths.length > 0 && (
        <div className="card p-6 border-s-4 !border-s-green-500">
          <h3 className="text-lg font-semibold mb-4 text-white">{t.analysis.strengths}</h3>
          <ul className="space-y-3">
            {analysis.strengths.map((strength, idx) => (
              <li key={idx} className="flex gap-3">
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="text-slate-200">{strength.text}</span>
                  <PointLaw point={strength} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Weaknesses */}
      {analysis.weaknesses.length > 0 && (
        <div className="card p-6 border-s-4 !border-s-yellow-500">
          <h3 className="text-lg font-semibold mb-4 text-white">{t.analysis.weaknesses}</h3>
          <ul className="space-y-3">
            {analysis.weaknesses.map((weakness, idx) => (
              <li key={idx} className="flex gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="text-slate-200">{weakness.text}</span>
                  <PointLaw point={weakness} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Legal Errors */}
      {analysis.legalErrors.length > 0 && (
        <div className="card p-6 border-s-4 !border-s-red-500">
          <h3 className="text-lg font-semibold mb-4 text-white">{t.analysis.legalIssues}</h3>
          <ul className="space-y-3">
            {analysis.legalErrors.map((error, idx) => (
              <li key={idx} className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="text-slate-200">{error.text}</span>
                  <PointLaw point={error} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Defense Strategy */}
      {analysis.defenseStrategy.length > 0 && (
        <div className="card p-6 border-s-4 !border-s-cyan-400">
          <h3 className="text-lg font-semibold mb-4 text-white">{t.analysis.defenseStrategy}</h3>
          <ol className="space-y-3">
            {analysis.defenseStrategy.map((strategy, idx) => (
              <li key={idx} className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-cyan-400/15 text-cyan-300 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                  {idx + 1}
                </span>
                <div className="pt-0.5">
                  <span className="text-slate-200">{strategy.text}</span>
                  <PointLaw point={strategy} />
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Recommendations */}
      {analysis.recommendations.length > 0 && (
        <div className="card p-6 border-s-4 !border-s-purple-500">
          <h3 className="text-lg font-semibold mb-4 text-white">{t.analysis.recommendations}</h3>
          <ul className="space-y-3">
            {analysis.recommendations.map((rec, idx) => (
              <li key={idx} className="flex gap-3">
                <span className="w-6 h-6 rounded-full bg-purple-400/15 text-purple-300 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                  {idx + 1}
                </span>
                <div className="pt-0.5">
                  <span className="text-slate-200">{rec.text}</span>
                  <PointLaw point={rec} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metadata */}
      <div className="text-xs text-slate-400 space-y-1">
        <p>{t.analysis.analysisId}: {analysis.id}</p>
        <p>{t.analysis.language}: {analysis.language.toUpperCase()}</p>
        <p>{t.analysis.created}: {formatDate(analysis.createdAt, dateTag)}</p>
      </div>
    </div>
  );
}

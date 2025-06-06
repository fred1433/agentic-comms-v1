import React from 'react';
import { 
  ArrowUpIcon, 
  ArrowDownIcon,
  MinusIcon 
} from '@heroicons/react/24/outline';
import classNames from 'classnames';
import { MetricCard } from '../types';

interface MetricsCardProps extends MetricCard {
  loading?: boolean;
  className?: string;
}

export default function MetricsCard({ 
  title, 
  value, 
  change, 
  icon: Icon, 
  color = 'gray',
  loading = false,
  className 
}: MetricsCardProps) {
  const getColorClasses = (color: string) => {
    switch (color) {
      case 'primary':
        return {
          bg: 'bg-primary-50',
          icon: 'text-primary-600',
          text: 'text-primary-900',
        };
      case 'success':
        return {
          bg: 'bg-success-50',
          icon: 'text-success-600',
          text: 'text-success-900',
        };
      case 'warning':
        return {
          bg: 'bg-warning-50',
          icon: 'text-warning-600',
          text: 'text-warning-900',
        };
      case 'danger':
        return {
          bg: 'bg-danger-50',
          icon: 'text-danger-600',
          text: 'text-danger-900',
        };
      default:
        return {
          bg: 'bg-gray-50',
          icon: 'text-gray-600',
          text: 'text-gray-900',
        };
    }
  };

  const colorClasses = getColorClasses(color);

  const getChangeIcon = () => {
    if (!change) return null;
    
    switch (change.type) {
      case 'positive':
        return <ArrowUpIcon className="h-4 w-4" />;
      case 'negative':
        return <ArrowDownIcon className="h-4 w-4" />;
      default:
        return <MinusIcon className="h-4 w-4" />;
    }
  };

  const getChangeColor = () => {
    if (!change) return '';
    
    switch (change.type) {
      case 'positive':
        return 'text-success-600';
      case 'negative':
        return 'text-danger-600';
      default:
        return 'text-gray-500';
    }
  };

  if (loading) {
    return (
      <div className={classNames('card p-6', className)}>
        <div className="animate-pulse">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
            </div>
            <div className="ml-4 flex-1">
              <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-16"></div>
            </div>
          </div>
          <div className="mt-4">
            <div className="h-3 bg-gray-200 rounded w-20"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={classNames('card p-6', className)}>
      <div className="flex items-center">
        <div className="flex-shrink-0">
          {Icon && (
            <div className={classNames(
              'w-10 h-10 rounded-lg flex items-center justify-center',
              colorClasses.bg
            )}>
              <Icon className={classNames('h-6 w-6', colorClasses.icon)} />
            </div>
          )}
        </div>
        <div className="ml-4 flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-500 truncate">
            {title}
          </p>
          <div className="flex items-baseline">
            <p className={classNames(
              'text-2xl font-semibold truncate',
              colorClasses.text
            )}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
          </div>
        </div>
      </div>
      
      {change && (
        <div className="mt-4">
          <div className={classNames(
            'flex items-center text-sm font-medium',
            getChangeColor()
          )}>
            {getChangeIcon()}
            <span className="ml-1">
              {change.value > 0 ? '+' : ''}{change.value}
            </span>
            <span className="ml-1 text-gray-500 font-normal">
              {change.label}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// Specialized metric cards for common use cases
export function ResponseTimeCard({ 
  responseTime, 
  target = 5000,
  className 
}: { 
  responseTime: number; 
  target?: number;
  className?: string;
}) {
  const isGood = responseTime <= target;
  const percentage = Math.min((responseTime / target) * 100, 100);
  
  return (
    <MetricsCard
      title="Avg Response Time"
      value={`${(responseTime / 1000).toFixed(1)}s`}
      color={isGood ? 'success' : 'warning'}
      change={{
        value: percentage - 100,
        type: isGood ? 'positive' : 'negative',
        label: `vs ${target/1000}s target`
      }}
      className={className}
    />
  );
}

export function ResolutionRateCard({ 
  rate, 
  target = 0.8,
  className 
}: { 
  rate: number; 
  target?: number;
  className?: string;
}) {
  const isGood = rate >= target;
  const percentage = (rate * 100).toFixed(1);
  
  return (
    <MetricsCard
      title="Auto Resolution Rate"
      value={`${percentage}%`}
      color={isGood ? 'success' : 'warning'}
      change={{
        value: Math.round((rate - target) * 100),
        type: isGood ? 'positive' : 'negative',
        label: `vs ${(target * 100)}% target`
      }}
      className={className}
    />
  );
}

export function AgentCountCard({ 
  count, 
  maxCount = 1000,
  className 
}: { 
  count: number; 
  maxCount?: number;
  className?: string;
}) {
  const utilization = (count / maxCount) * 100;
  
  return (
    <MetricsCard
      title="Active Agents"
      value={count}
      color={utilization > 80 ? 'warning' : 'primary'}
      change={{
        value: Math.round(utilization),
        type: 'neutral',
        label: '% utilization'
      }}
      className={className}
    />
  );
} 
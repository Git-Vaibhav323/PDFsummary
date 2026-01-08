"use client";

import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SimpleChartProps {
  type: "bar" | "line" | "pie" | "stacked_bar";
  title?: string;
  labels: string[];
  values: number[];
  groups?: { [key: string]: number[] };  // For stacked bar charts
  xAxis?: string;
  yAxis?: string;
}

const COLORS = ['#2563EB', '#16A34A', '#D97706', '#DC2626', '#8B5CF6', '#EC4899', '#14B8A6', '#FB923C'];

export default function SimpleChart({
  type,
  title,
  labels,
  values,
  groups,
  xAxis,
  yAxis,
}: SimpleChartProps) {
  // Validate and provide defaults for required props
  const safeLabels = Array.isArray(labels) ? labels : [];
  const safeValues = Array.isArray(values) ? values : [];
  
  // If no data, return empty state
  if (safeLabels.length === 0 || safeValues.length === 0) {
    return (
      <div className="w-full min-w-0 max-w-full bg-white rounded-xl p-4 md:p-6 border border-[#E5E7EB]">
        {title && (
          <h3 className="text-lg font-semibold mb-4 text-[#111827]">{title}</h3>
        )}
        <div className="flex items-center justify-center h-64 text-[#6B7280]">
          <p className="text-sm">No data available for this chart</p>
        </div>
      </div>
    );
  }
  
  // Transform data for Recharts
  const data = safeLabels.map((label, index) => {
    const item: any = {
      name: label,
      value: safeValues[index] !== undefined ? safeValues[index] : 0,
    };
    
    // Add group data for stacked bar charts
    if (groups && type === "stacked_bar") {
      Object.keys(groups).forEach(groupName => {
        if (groups[groupName] && groups[groupName][index] !== undefined) {
          item[groupName] = groups[groupName][index] || 0;
        }
      });
    }
    
    return item;
  });

  // Format numbers for display
  const formatNumber = (value: number) => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toLocaleString();
  };

  const renderChart = () => {
    switch (type) {
      case "bar":
        // Determine if labels need rotation based on length
        const maxLabelLength = Math.max(...safeLabels.map(l => l.length));
        const needsRotation = maxLabelLength > 10 || safeLabels.length > 8;
        
        return (
          <BarChart 
            data={data} 
            margin={{ 
              top: 20, 
              right: 30, 
              left: labels.length > 0 ? 20 : 10, 
              bottom: needsRotation ? 100 : 60 
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={1} />
            <XAxis 
              dataKey="name" 
              angle={needsRotation ? -45 : 0}
              textAnchor={needsRotation ? "end" : "middle"}
              height={needsRotation ? 100 : 60}
              tick={{ fill: '#6B7280', fontSize: 13 }}
              interval={safeLabels.length > 15 ? "preserveStartEnd" : 0}
              style={{ fontSize: '13px' }}
            />
            <YAxis 
              tick={{ fill: '#6B7280', fontSize: 13 }}
              tickFormatter={formatNumber}
              width={safeLabels.length > 0 ? 80 : 60}
              style={{ fontSize: '13px' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#FFFFFF', 
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
                color: '#111827',
                fontSize: '13px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.08)'
              }}
              formatter={(value: number) => value.toLocaleString()}
            />
            <Legend 
              wrapperStyle={{ color: '#6B7280', fontSize: '13px', paddingTop: '10px' }}
              iconSize={14}
            />
            <Bar dataKey="value" fill="#2563EB" radius={[8, 8, 0, 0]} />
          </BarChart>
        );

      case "stacked_bar":
        const groupKeys = groups ? Object.keys(groups) : [];
        const stackedMaxLabelLength = Math.max(...safeLabels.map(l => l.length));
        const stackedNeedsRotation = stackedMaxLabelLength > 10 || safeLabels.length > 8;
        
        return (
          <BarChart 
            data={data} 
            margin={{ 
              top: 20, 
              right: 30, 
              left: labels.length > 0 ? 20 : 10, 
              bottom: stackedNeedsRotation ? 100 : 60 
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={1} />
            <XAxis 
              dataKey="name" 
              angle={stackedNeedsRotation ? -45 : 0}
              textAnchor={stackedNeedsRotation ? "end" : "middle"}
              height={stackedNeedsRotation ? 100 : 60}
              tick={{ fill: '#6B7280', fontSize: 13 }}
              interval={safeLabels.length > 15 ? "preserveStartEnd" : 0}
              style={{ fontSize: '13px' }}
            />
            <YAxis 
              tick={{ fill: '#6B7280', fontSize: 13 }}
              tickFormatter={formatNumber}
              width={safeLabels.length > 0 ? 80 : 60}
              style={{ fontSize: '13px' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#FFFFFF', 
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
                color: '#111827',
                fontSize: '13px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.08)'
              }}
              formatter={(value: number) => value.toLocaleString()}
            />
            <Legend 
              wrapperStyle={{ color: '#6B7280', fontSize: '13px', paddingTop: '10px' }}
              iconSize={14}
            />
            {groupKeys.map((groupName, index) => (
              <Bar 
                key={groupName}
                dataKey={groupName} 
                stackId="1"
                fill={COLORS[index % COLORS.length]} 
                radius={index === groupKeys.length - 1 ? [8, 8, 0, 0] : [0, 0, 0, 0]}
              />
            ))}
          </BarChart>
        );

      case "line":
        const lineMaxLabelLength = Math.max(...safeLabels.map(l => l.length));
        const lineNeedsRotation = lineMaxLabelLength > 10 || safeLabels.length > 8;
        
        return (
          <LineChart 
            data={data} 
            margin={{ 
              top: 20, 
              right: 30, 
              left: labels.length > 0 ? 20 : 10, 
              bottom: lineNeedsRotation ? 100 : 60 
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
            <XAxis 
              dataKey="name" 
              angle={lineNeedsRotation ? -45 : 0}
              textAnchor={lineNeedsRotation ? "end" : "middle"}
              height={lineNeedsRotation ? 100 : 60}
              tick={{ fill: '#9ca3af', fontSize: 13 }}
              interval={safeLabels.length > 15 ? "preserveStartEnd" : 0}
              style={{ fontSize: '13px' }}
            />
            <YAxis 
              tick={{ fill: '#9ca3af', fontSize: 13 }}
              tickFormatter={formatNumber}
              width={safeLabels.length > 0 ? 80 : 60}
              style={{ fontSize: '13px' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1f2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#f3f4f6',
                fontSize: '13px'
              }}
              formatter={(value: number) => value.toLocaleString()}
            />
            <Legend 
              wrapperStyle={{ color: '#9ca3af', fontSize: '13px', paddingTop: '10px' }}
              iconSize={14}
            />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke="#2563EB" 
              strokeWidth={2}
              dot={{ fill: '#2563EB', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        );

      case "pie":
        return (
          <PieChart margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => {
                // Only show label if percentage is significant (> 5%)
                if (percent < 0.05) return '';
                return `${name}: ${(percent * 100).toFixed(0)}%`;
              }}
              outerRadius={safeLabels.length <= 5 ? 140 : 120}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#FFFFFF', 
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
                color: '#111827',
                fontSize: '13px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.08)'
              }}
              formatter={(value: number) => value.toLocaleString()}
            />
            <Legend 
              wrapperStyle={{ color: '#6B7280', fontSize: '13px', paddingTop: '20px' }}
              iconSize={14}
              layout="horizontal"
              verticalAlign="bottom"
            />
          </PieChart>
        );

      default:
        return null;
    }
  };

  return (
    <div 
      className="w-full min-w-0 max-w-full bg-transparent rounded-xl" 
      style={{ 
        position: 'relative',
        zIndex: 10,
        isolation: 'isolate'
      }}
    >
      {title && (
        <h3 className="text-lg font-semibold mb-6 text-[#111827]">{title}</h3>
      )}
      <div 
        className="w-full min-w-0 max-w-full" 
        style={{ 
          height: type === "pie" ? "500px" : "500px", 
          minHeight: "450px",
          maxHeight: "700px",
          position: 'relative',
          zIndex: 11,
          overflow: 'visible'
        }}
      >
        <ResponsiveContainer 
          width="100%" 
          height="100%" 
          debounce={1}
          style={{ position: 'relative', zIndex: 12 }}
        >
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}


"use client";

import { useEffect, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from "chart.js";
import { Bar, Line, Pie } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface ChartVisualizationProps {
  type: "bar" | "line" | "pie";
  title?: string;
  labels: string[];
  values: number[];
  xAxis?: string;
  yAxis?: string;
}

export default function ChartVisualization({
  type,
  title,
  labels,
  values,
  xAxis,
  yAxis,
}: ChartVisualizationProps) {
  // Generate colors for the chart
  const generateColors = (count: number) => {
    const colors = [
      "rgba(37, 99, 235, 0.8)",   // Blue (#2563EB)
      "rgba(22, 163, 74, 0.8)",   // Green (#16A34A)
      "rgba(217, 119, 6, 0.8)",   // Orange (#D97706)
      "rgba(220, 38, 38, 0.8)",   // Red (#DC2626)
      "rgba(139, 92, 246, 0.8)",  // Purple
      "rgba(236, 72, 153, 0.8)",  // Pink
      "rgba(20, 184, 166, 0.8)",  // Teal
      "rgba(59, 130, 246, 0.8)",  // Blue (alternative)
    ];
    
    const result = [];
    for (let i = 0; i < count; i++) {
      result.push(colors[i % colors.length]);
    }
    return result;
  };

  const backgroundColors = generateColors(values.length);
  const borderColors = backgroundColors.map(color => color.replace('0.8', '1'));

  const chartData = {
    labels: labels,
    datasets: [
      {
        label: title || "Data",
        data: values,
        backgroundColor: type === "pie" ? backgroundColors : "rgba(59, 130, 246, 0.8)",
        borderColor: type === "pie" ? borderColors : "rgba(59, 130, 246, 1)",
        borderWidth: 2,
        tension: 0.4, // For line charts
      },
    ],
  };

  const options: ChartOptions<any> = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: type === "pie",
        position: "bottom" as const,
        labels: {
          color: "rgb(156, 163, 175)", // text-gray-400
          font: {
            size: 12,
          },
          padding: 15,
        },
      },
      title: {
        display: !!title,
        text: title || "",
        color: "rgb(209, 213, 219)", // text-gray-300
        font: {
          size: 16,
          weight: "bold" as const,
        },
        padding: {
          top: 10,
          bottom: 20,
        },
      },
      tooltip: {
        backgroundColor: "rgba(17, 24, 39, 0.95)", // bg-gray-900
        titleColor: "rgb(243, 244, 246)", // text-gray-100
        bodyColor: "rgb(229, 231, 235)", // text-gray-200
        borderColor: "rgba(75, 85, 99, 0.8)", // border-gray-600
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          label: function(context: any) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              // Format large numbers with commas
              const value = context.parsed.y || context.parsed;
              label += new Intl.NumberFormat('en-US', {
                maximumFractionDigits: 2,
              }).format(value);
            }
            return label;
          }
        }
      },
    },
    scales: type !== "pie" ? {
      x: {
        title: {
          display: !!xAxis,
          text: xAxis || "",
          color: "rgb(156, 163, 175)", // text-gray-400
          font: {
            size: 13,
            weight: "bold" as const,
          },
        },
        ticks: {
          color: "rgb(156, 163, 175)", // text-gray-400
          font: {
            size: 11,
          },
          maxRotation: 45,
          minRotation: 0,
        },
        grid: {
          color: "rgba(75, 85, 99, 0.2)", // Very subtle grid
        },
      },
      y: {
        title: {
          display: !!yAxis,
          text: yAxis || "",
          color: "rgb(156, 163, 175)", // text-gray-400
          font: {
            size: 13,
            weight: "bold" as const,
          },
        },
        ticks: {
          color: "rgb(156, 163, 175)", // text-gray-400
          font: {
            size: 11,
          },
          callback: function(value: any) {
            // Format y-axis numbers with commas
            return new Intl.NumberFormat('en-US', {
              notation: 'compact',
              compactDisplay: 'short',
            }).format(value as number);
          },
        },
        grid: {
          color: "rgba(75, 85, 99, 0.2)", // Very subtle grid
        },
        beginAtZero: true,
      },
    } : undefined,
  };

  return (
    <div className="w-full bg-card/50 backdrop-blur-sm rounded-lg p-6 border border-border/50">
      <div className="w-full" style={{ maxHeight: type === "pie" ? "400px" : "500px" }}>
        {type === "bar" && <Bar data={chartData} options={options} />}
        {type === "line" && <Line data={chartData} options={options} />}
        {type === "pie" && <Pie data={chartData} options={options} />}
      </div>
    </div>
  );
}


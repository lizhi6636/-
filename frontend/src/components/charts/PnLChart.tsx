import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface Props {
  data: { date: string; value: number }[];
  height?: number;
}

export default function PnLChart({ data, height = 350 }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current);

    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', top: 20, bottom: 30 },
      xAxis: { type: 'category', data: data.map((d) => d.date) },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'line',
          data: data.map((d) => d.value),
          smooth: true,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(22,119,255,0.3)' },
              { offset: 1, color: 'rgba(22,119,255,0.05)' },
            ]),
          },
        },
      ],
    });

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [data]);

  return <div ref={chartRef} style={{ width: '100%', height }} />;
}

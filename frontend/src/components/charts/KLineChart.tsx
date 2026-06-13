import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { KlineData } from '../../types/stock';

interface Props {
  data: KlineData[];
  height?: number;
}

export default function KLineChart({ data, height = 500 }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current);
    }

    const dates = data.map((d) => d.date);
    const ohlc = data.map((d) => [d.open, d.close, d.low, d.high]);
    const volumes = data.map((d) => d.volume);

    // Calculate MA
    const closes = data.map((d) => d.close);
    const ma5 = calcMA(closes, 5);
    const ma10 = calcMA(closes, 10);
    const ma20 = calcMA(closes, 20);
    const ma60 = calcMA(closes, 60);

    instanceRef.current.setOption(
      {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
        },
        legend: {
          data: ['K线', 'MA5', 'MA10', 'MA20', 'MA60'],
          top: 0,
        },
        grid: [
          { left: '8%', right: '8%', top: 40, height: '55%' },
          { left: '8%', right: '8%', top: '75%', height: '15%' },
        ],
        xAxis: [
          { type: 'category', data: dates, gridIndex: 0, axisLabel: { show: false } },
          { type: 'category', data: dates, gridIndex: 1 },
        ],
        yAxis: [
          { type: 'value', gridIndex: 0, scale: true },
          { type: 'value', gridIndex: 1 },
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            data: ohlc,
            itemStyle: {
              color: '#cf1322',
              color0: '#3f8600',
              borderColor: '#cf1322',
              borderColor0: '#3f8600',
            },
          },
          {
            name: 'MA5', type: 'line', data: ma5,
            smooth: true, lineStyle: { width: 1 }, symbol: 'none',
          },
          {
            name: 'MA10', type: 'line', data: ma10,
            smooth: true, lineStyle: { width: 1 }, symbol: 'none',
          },
          {
            name: 'MA20', type: 'line', data: ma20,
            smooth: true, lineStyle: { width: 1 }, symbol: 'none',
          },
          {
            name: 'MA60', type: 'line', data: ma60,
            smooth: true, lineStyle: { width: 1 }, symbol: 'none',
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes,
            itemStyle: {
              color: (params: { dataIndex: number }) => {
                const d = data[params.dataIndex];
                return d.close >= d.open ? '#cf1322' : '#3f8600';
              },
            },
          },
        ],
      },
      true
    );

    const handleResize = () => instanceRef.current?.resize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [data]);

  return <div ref={chartRef} style={{ width: '100%', height }} />;
}

function calcMA(data: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += data[j];
      result.push(+(sum / period).toFixed(2));
    }
  }
  return result;
}

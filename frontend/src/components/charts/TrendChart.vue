<script setup lang="ts">
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GraphicComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { computed } from 'vue'
import VChart from 'vue-echarts'

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  GraphicComponent,
  CanvasRenderer,
])

type ChartKind = 'line' | 'bar' | 'donut'

const props = withDefaults(
  defineProps<{
    kind: ChartKind
    categories: string[]
    series: { name: string; values: number[]; color?: string; kind?: ChartKind; axis?: number }[]
    height?: number
    unit?: string
  }>(),
  { height: 240, unit: '' },
)

const PALETTE = ['#B08968', '#7A9E7E', '#C0714F', '#D9C3A9', '#8A7F70', '#9A7355', '#A8BFA1']

const axisStyle = {
  axisLine: { lineStyle: { color: '#E8E1D5' } },
  axisTick: { show: false },
  axisLabel: { color: '#8A7F70', fontSize: 11 },
  splitLine: { lineStyle: { color: '#F1EBE1' } },
}

const option = computed(() => {
  if (props.kind === 'donut') {
    const values = props.series[0]?.values ?? []
    return {
      color: PALETTE,
      tooltip: {
        trigger: 'item',
        valueFormatter: (value: unknown) => `${value}${props.unit}`,
      },
      legend: {
        bottom: 0,
        icon: 'circle',
        itemWidth: 8,
        itemHeight: 8,
        textStyle: { color: '#8A7F70', fontSize: 11 },
      },
      graphic: values.length
        ? [
            {
              type: 'text',
              left: 'center',
              top: '37%',
              silent: true,
              style: {
                text: `¥${values.reduce((sum, value) => sum + value, 0).toFixed(2)}`,
                fill: '#3D3528',
                font: '600 17px sans-serif',
                textAlign: 'center',
              },
            },
            {
              type: 'text',
              left: 'center',
              top: '47%',
              silent: true,
              style: { text: '本月支出', fill: '#8A7F70', font: '11px sans-serif', textAlign: 'center' },
            },
          ]
        : [],
      series: [
        {
          type: 'pie',
          radius: ['52%', '74%'],
          center: ['50%', '44%'],
          avoidLabelOverlap: true,
          itemStyle: { borderColor: '#FFFFFF', borderWidth: 2, borderRadius: 4 },
          label: { show: false },
          data: props.categories.map((name, index) => ({ name, value: values[index] ?? 0 })),
        },
      ],
    }
  }

  const dualAxis = props.series.some((item) => item.axis === 1)
  const yAxis = dualAxis
    ? [
        { type: 'value', ...axisStyle, axisLine: { show: false } },
        {
          type: 'value',
          ...axisStyle,
          axisLine: { show: false },
          splitLine: { show: false },
        },
      ]
    : { type: 'value', ...axisStyle, axisLine: { show: false } }

  return {
    color: PALETTE,
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: unknown) => `${value}${props.unit}`,
      backgroundColor: '#FFFFFF',
      borderColor: '#E8E1D5',
      textStyle: { color: '#3D3528', fontSize: 12 },
    },
    legend: {
      top: 0,
      right: 0,
      icon: 'roundRect',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: '#8A7F70', fontSize: 11 },
    },
    grid: { top: 34, left: 8, right: dualAxis ? 16 : 12, bottom: 4, containLabel: true },
    xAxis: { type: 'category', data: props.categories, ...axisStyle, splitLine: { show: false } },
    yAxis,
    series: props.series.map((item) => {
      const kind = item.kind ?? props.kind
      return {
        name: item.name,
        type: kind,
        data: item.values,
        yAxisIndex: item.axis === 1 ? 1 : 0,
        smooth: kind === 'line',
        symbol: 'circle',
        symbolSize: 5,
        barMaxWidth: 18,
        itemStyle: {
          color: item.color,
          borderRadius: kind === 'bar' ? [4, 4, 0, 0] : undefined,
        },
        areaStyle: kind === 'line' ? { opacity: 0.12 } : undefined,
      }
    }),
  }
})
</script>

<template>
  <VChart :option="option" :style="{ height: `${height}px`, width: '100%' }" autoresize />
</template>

/**
 * D3 donut chart component. Imported into the Program Performance Dashboard.
 * @packageDocumentation
 **/
import React, { useEffect, useRef } from "react";

import * as d3 from "d3";
import { PieArcDatum } from "d3";

/**
 * Interface for the DonutChart component
 */
interface DonutChartData {
  /**
   * Key for a segment of the chart.
   */
  key: string;
  /**
   * Value of the segment of the chart.
   */
  value: number;
}

interface DonutChartProps {
  /**
   * List of key-value pairs representing the data for the chart
   */
  data: DonutChartData[];
  /**
   * Chart height in pixels
   */
  height?: number;
  /**
   * Chart width in pixels
   */
  width?: number;
  /**
   * List of hexcodes to fill donut chart.
   */
  colors?: string[];
  /**
   * Boolean to set height and width to 100%
   */
  fullWidth?: boolean;
}

export const DonutChart: React.FC<DonutChartProps> = ({
  data,
  height = 200,
  width = 200,
  colors = ["#00A91C", "#B50909"],
  fullWidth,
}): React.ReactElement => {
  /**
   * Creates a reference to the svg element
   */
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    /**
     * Chart radius based on height and width
     */
    const radius = Math.min(width, height) / 2;

    /**
     * Checks whether the data contains a segment that is 100% of the chart
     */
    const has100Percent = (data: DonutChartData[]): boolean => {
      const total = d3.sum(data, (d) => d.value);
      const percentages = data.map((d) => (d.value / total) * 100);
      return percentages.includes(100);
    };

    /**
     * Adds whitespace between the donut chart segments.
     *
     * If there is only one segment that fills the entire chart,
     * sets the padAngle to 0.
     */
    const padAngle = has100Percent(data) ? 0 : 0.03;

    /**
     * The arc generator
     */
    const arc = d3
      .arc<PieArcDatum<DonutChartData>>()
      .innerRadius(radius * 0.5)
      .outerRadius(radius - 1)
      .padAngle(padAngle);

    /**
     * Computes the start and end angles of each group
     */
    const pie = d3
      .pie<DonutChartData>()
      .padAngle(padAngle)
      .sort(null)
      .value((d: DonutChartData) => d.value);

    /**
     * Creates the color scale
     */
    const color = d3
      .scaleOrdinal<string>()
      .domain(data.map((d) => d.key))
      .range(colors);

    /**
     * Selects the svg object using the current ref and set its dimensions
     */
    const svg = d3
      .select(ref.current)
      .attr("viewBox", [-width / 2, -height / 2, width, height])
      .attr("height", fullWidth ? "100%" : height)
      .attr("width", fullWidth ? "100%" : width);

    /**
     * Removes any existing children
     */
    svg.selectAll("*").remove();

    /**
     * Creates and updates the svg path elements based on the data array
     */
    svg
      .append("g")
      .selectAll()
      .data(pie(data))
      .join("path")
      .attr("fill", (d: PieArcDatum<DonutChartData>) => color(d.data.key))
      .attr("d", arc);
  }, [data]);

  return (
    <div id="DonutChart" data-testid="DonutChart">
      <svg ref={ref}></svg>
    </div>
  );
};

export default DonutChart;

(() => {
    "use strict";

    const payloadElement = document.getElementById("detail-chart-data");
    const chartPayloads = JSON.parse(payloadElement?.textContent ?? "{}");
    const renderedCharts = new Set();
    const parseDate = d3.timeParse("%Y-%m-%d");
    const formatDate = d3.timeFormat("%b %-d, %Y");
    const formatCurrency = (value) => `$${d3.format(",.2f")(value)}`;
    const formatXAxisTick = (date) =>
        date.getMonth() === 0 && date.getDate() === 1
            ? d3.timeFormat("%Y")(date)
            : d3.timeFormat("%b %-d")(date);

    function xAxisTickValues(scale, count = 7) {
        const [start, end] = scale.domain();
        const yearBoundaries = d3.timeYear.range(
            d3.timeYear.ceil(start),
            d3.timeYear.offset(d3.timeYear.floor(end), 1)
        );
        return [...new Map(
            [...scale.ticks(count), ...yearBoundaries]
                .filter((date) => date >= start && date <= end)
                .map((date) => [+date, date])
        ).values()].sort((left, right) => left - right);
    }

    function renderChart(pageName) {
        if (renderedCharts.has(pageName) || !chartPayloads[pageName]) {
            return;
        }

        const payload = chartPayloads[pageName];
        const options = payload.options ?? {};
        const svg = d3.select(`#${pageName}-chart`);
        const tooltip = d3.select(`#${pageName}-chart-tooltip`);
        const container = document.querySelector(
            `#detail-page-${pageName} .detail-line-chart-container`
        );
        const data = (payload.series_data ?? [])
            .map((row) => {
                const parsed = {...row, __date: parseDate(row.Date)};
                Object.keys(row).forEach((key) => {
                    if (key !== "Date") {
                        parsed[key] = Number(row[key]);
                    }
                });
                return parsed;
            })
            .filter((row) => row.__date instanceof Date)
            .sort((left, right) => left.__date - right.__date);

        if (!data.length) {
            return;
        }

        const seriesNames = Object.keys(data[0]).filter(
            (name) => name !== "Date" && name !== "__date"
        );
        const values = seriesNames.flatMap((name) =>
            data.map((row) => row[name]).filter(Number.isFinite)
        );
        if (!seriesNames.length || !values.length) {
            return;
        }

        renderedCharts.add(pageName);
        const width = 1200;
        const height = 560;
        const margin = {top: 42, right: 48, bottom: 58, left: 88};
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;
        const xScale = d3.scaleTime()
            .domain(d3.extent(data, (row) => row.__date))
            .range([0, innerWidth]);

        let yMinimum = d3.min(values) ?? 0;
        let yMaximum = d3.max(values) ?? 0;
        if (options.symmetric_zero) {
            const extent = Math.max(Math.abs(yMinimum), Math.abs(yMaximum), 1);
            yMinimum = -extent;
            yMaximum = extent;
        } else {
            if (yMinimum === yMaximum) {
                const padding = Math.max(Math.abs(yMinimum) * 0.1, 1);
                yMinimum -= padding;
                yMaximum += padding;
            }
            const padding = Math.max((yMaximum - yMinimum) * 0.08, 1);
            yMinimum = yMinimum >= 0 ? 0 : yMinimum - padding;
            yMaximum = yMaximum <= 0 ? 0 : yMaximum + padding;
        }
        const yScale = d3.scaleLinear()
            .domain([yMinimum, yMaximum])
            .nice()
            .range([innerHeight, 0]);

        svg.selectAll("*").remove();
        svg.attr("viewBox", `0 0 ${width} ${height}`);
        const chart = svg.append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);

        chart.append("g")
            .attr("class", "hero-grid")
            .call(d3.axisLeft(yScale).ticks(7).tickSize(-innerWidth).tickFormat(""));
        chart.append("g")
            .attr("class", "hero-axis")
            .attr("transform", `translate(0,${innerHeight})`)
            .call(d3.axisBottom(xScale)
                .tickValues(xAxisTickValues(xScale))
                .tickFormat(formatXAxisTick));
        chart.append("g")
            .attr("class", "hero-axis")
            .call(d3.axisLeft(yScale).ticks(7).tickFormat((value) => `$${d3.format("~s")(value)}`));

        if (yScale.domain()[0] <= 0 && yScale.domain()[1] >= 0) {
            chart.append("line")
                .attr("class", "detail-zero-line")
                .attr("x1", 0)
                .attr("x2", innerWidth)
                .attr("y1", yScale(0))
                .attr("y2", yScale(0))
                .attr("stroke", "#77777d")
                .attr("stroke-width", 1.25);
        }

        const today = d3.timeDay.floor(new Date());
        const xDomain = xScale.domain();
        const includesToday = today >= xDomain[0] && today <= xDomain[1];
        const animationOriginX = xScale(includesToday ? today : xDomain[0]);
        const clipId = `detail-line-clip-${pageName}-${Math.random().toString(36).slice(2)}`;
        const clipPath = svg.append("defs").append("clipPath").attr("id", clipId);
        const leftClip = clipPath.append("rect")
            .attr("x", margin.left + animationOriginX)
            .attr("y", margin.top)
            .attr("width", 0)
            .attr("height", innerHeight);
        const rightClip = clipPath.append("rect")
            .attr("x", margin.left + animationOriginX)
            .attr("y", margin.top)
            .attr("width", 0)
            .attr("height", innerHeight);
        const lineLayer = svg.append("g").attr("clip-path", `url(#${clipId})`);
        const line = (seriesName) => d3.line()
            .defined((row) => Number.isFinite(row[seriesName]))
            .x((row) => xScale(row.__date))
            .y((row) => yScale(row[seriesName]))
            .curve(d3.curveMonotoneX);

        seriesNames.forEach((seriesName) => {
            const style = options.line_styles?.[seriesName] ?? {};
            lineLayer.append("path")
                .datum(data)
                .attr("class", "hero-series-line")
                .attr("transform", `translate(${margin.left},${margin.top})`)
                .attr("stroke", style.color ?? "#7a7a80")
                .attr("stroke-width", style.width ?? 2)
                .attr("d", line(seriesName));
        });

        const reducedMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;
        const duration = reducedMotion ? 0 : options.line_animation_ms ?? 1800;
        leftClip.transition().duration(duration).ease(d3.easeCubicInOut)
            .attr("x", margin.left).attr("width", animationOriginX);
        rightClip.transition().duration(duration).ease(d3.easeCubicInOut)
            .attr("width", innerWidth - animationOriginX);

        const legend = chart.append("g").attr("class", "detail-chart-legend");
        let legendOffset = 0;
        seriesNames.forEach((seriesName) => {
            const item = legend.append("g")
                .attr("transform", `translate(${legendOffset},-22)`);
            item.append("line")
                .attr("x1", 0).attr("x2", 18).attr("y1", 0).attr("y2", 0)
                .attr("stroke", options.line_styles?.[seriesName]?.color ?? "#7a7a80")
                .attr("stroke-width", 3);
            item.append("text")
                .attr("x", 24).attr("y", 4)
                .attr("fill", "currentColor")
                .attr("font-size", 13)
                .text(seriesName);
            legendOffset += 42 + seriesName.length * 7;
        });

        const guide = chart.append("line")
            .attr("class", "hero-today-guide")
            .attr("y1", 0).attr("y2", innerHeight)
            .style("display", "none");
        const bisect = d3.bisector((row) => row.__date).center;
        chart.append("rect")
            .attr("width", innerWidth)
            .attr("height", innerHeight)
            .attr("fill", "transparent")
            .on("mousemove", (event) => {
                const [pointerX] = d3.pointer(event);
                const row = data[bisect(data, xScale.invert(pointerX))];
                guide.attr("x1", xScale(row.__date)).attr("x2", xScale(row.__date))
                    .style("display", null);
                const absoluteSeries = new Set(options.absolute_tooltip_series ?? []);
                const rows = [["Date", formatDate(row.__date)], ...seriesNames.map(
                    (name) => [name, formatCurrency(absoluteSeries.has(name) ? Math.abs(row[name]) : row[name])]
                )];
                tooltip.html(rows.map(([label, value]) => `
                    <div class="hero-chart-tooltip-row">
                        <span class="hero-chart-tooltip-label">${label}</span>
                        <span class="hero-chart-tooltip-value">${value}</span>
                    </div>`).join("")).attr("hidden", null);
                const bounds = container.getBoundingClientRect();
                tooltip.style("left", `${Math.min(event.clientX - bounds.left + 14, bounds.width - 230)}px`)
                    .style("top", `${Math.max(8, event.clientY - bounds.top - 12)}px`);
            })
            .on("mouseleave", () => {
                guide.style("display", "none");
                tooltip.attr("hidden", true);
            });
    }

    Object.keys(chartPayloads).forEach((pageName) => {
        const page = document.getElementById(`detail-page-${pageName}`);
        if (!page) {
            return;
        }
        const observer = new MutationObserver(() => {
            if (page.classList.contains("is-active")) {
                renderChart(pageName);
            }
        });
        observer.observe(page, {attributes: true, attributeFilter: ["class"]});
        if (page.classList.contains("is-active")) {
            renderChart(pageName);
        }
    });
})();

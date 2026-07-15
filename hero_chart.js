(() => {
    "use strict";

    const heroChartDataElement =
        document.getElementById("hero-chart-data");

    const heroChartPayload = JSON.parse(
        heroChartDataElement?.textContent ?? "{}"
    );

    function renderHeroChart(payload) {
        const svg = d3.select("#hero-chart");
        const tooltip = d3.select("#hero-chart-tooltip");

        const rawSeriesData = payload.series_data ?? [];
        const highlightedTransactions =
            payload.highlighted_transactions ?? [];
        const accountMilestoneAchievedDates =
            payload.account_milestone_achieved_dates ?? [];
        const options = payload.options ?? {};

        const dateColumn = options.date_column ?? "Date";
        const primarySeries = options.primary_series;

        if (!rawSeriesData.length) {
            svg
                .attr("viewBox", "0 0 1000 500")
                .append("text")
                .attr("x", 500)
                .attr("y", 250)
                .attr("text-anchor", "middle")
                .attr("fill", "#77777d")
                .text("No hero chart data available");

            return;
        }

        if (!primarySeries) {
            throw new Error(
                "hero_chart_options.primary_series is required."
            );
        }

        const parseDate = d3.timeParse("%Y-%m-%d");

        const seriesData = rawSeriesData
            .map((row) => {
                const parsedRow = {
                    ...row,
                    __date: parseDate(row[dateColumn]),
                };

                Object.keys(row).forEach((key) => {
                    if (key === dateColumn) {
                        return;
                    }

                    const value = row[key];

                    parsedRow[key] =
                        value === null ||
                        value === undefined ||
                        value === ""
                            ? null
                            : Number(value);
                });

                return parsedRow;
            })
            .filter((row) => row.__date instanceof Date)
            .sort((left, right) => left.__date - right.__date);

        const transactionData = highlightedTransactions
            .map((transaction) => ({
                ...transaction,
                __date: parseDate(transaction.Date),
                Amount: Number(transaction.Amount),
            }))
            .filter(
                (transaction) =>
                    transaction.__date instanceof Date &&
                    Number.isFinite(transaction.Amount)
            )
            .sort((left, right) => left.__date - right.__date);

        const milestoneData = accountMilestoneAchievedDates
            .map((milestoneDate) => ({
                ...milestoneDate,
                __date: parseDate(milestoneDate.Date),
                Amount: Number(milestoneDate.Amount),
                Milestones: Array.isArray(milestoneDate.Milestones)
                    ? milestoneDate.Milestones
                    : [],
            }))
            .filter(
                (milestoneDate) =>
                    milestoneDate.__date instanceof Date &&
                    Number.isFinite(milestoneDate.Amount) &&
                    milestoneDate.Milestones.length
            )
            .sort((left, right) => left.__date - right.__date);

        const seriesNames = Object.keys(seriesData[0]).filter(
            (columnName) =>
                columnName !== dateColumn &&
                columnName !== "__date"
        );

        if (!seriesNames.includes(primarySeries)) {
            throw new Error(
                `Primary series "${primarySeries}" was not found.`
            );
        }

        const width = 1200;
        const height = 560;

        const margin = {
            top: 30,
            right: 88,
            bottom: 58,
            left: 88,
        };

        const innerWidth =
            width - margin.left - margin.right;

        const innerHeight =
            height - margin.top - margin.bottom;

        svg.selectAll("*").remove();

        svg.attr(
            "viewBox",
            `0 0 ${width} ${height}`
        );

        const chart = svg
            .append("g")
            .attr(
                "transform",
                `translate(${margin.left},${margin.top})`
            );

        const xDomain = d3.extent(
            seriesData,
            (row) => row.__date
        );

        const allSeriesValues = seriesNames.flatMap(
            (seriesName) =>
                seriesData
                    .map((row) => row[seriesName])
                    .filter(Number.isFinite)
        );

        const transactionAmounts = transactionData.map(
            (transaction) => transaction.Amount
        );

        const allYValues = [
            ...allSeriesValues,
            ...transactionAmounts,
        ];

        let yMinimum = d3.min(allYValues);
        let yMaximum = d3.max(allYValues);

        if (yMinimum === yMaximum) {
            if (yMinimum === 0) {
                yMaximum = 1;
            } else {
                const padding = Math.abs(yMinimum) * 0.1;
                yMinimum -= padding;
                yMaximum += padding;
            }
        }

        const yPadding =
            Math.max(
                (yMaximum - yMinimum) * 0.08,
                1
            );

        const xScale = d3
            .scaleTime()
            .domain(xDomain)
            .range([0, innerWidth]);

        const yDomain = [
            yMinimum >= 0 ? 0 : yMinimum - yPadding,
            yMaximum <= 0 ? 0 : yMaximum + yPadding,
        ];

        const yScale = d3
            .scaleLinear()
            .domain(yDomain)
            .nice()
            .range([innerHeight, 0]);

        const milestoneAmounts = milestoneData.map(
            (milestoneDate) => milestoneDate.Amount
        );
        const rightAxisValues = milestoneAmounts.length
            ? milestoneAmounts
            : allSeriesValues;
        let rightMinimum = d3.min(rightAxisValues) ?? 0;
        let rightMaximum = d3.max(rightAxisValues) ?? 1;

        if (rightMinimum === rightMaximum) {
            if (rightMinimum === 0) {
                rightMaximum = 1;
            } else {
                const padding = Math.abs(rightMinimum) * 0.1;
                rightMinimum -= padding;
                rightMaximum += padding;
            }
        }

        const rightPadding = Math.max(
            (rightMaximum - rightMinimum) * 0.08,
            1
        );
        const milestoneYDomain = [
            rightMinimum >= 0 ? 0 : rightMinimum - rightPadding,
            rightMaximum <= 0 ? 0 : rightMaximum + rightPadding,
        ];
        const milestoneYScale = d3
            .scaleLinear()
            .domain(milestoneYDomain)
            .nice()
            .range([innerHeight, 0]);

        const currencySymbol =
            options.currency_symbol ?? "$";

        const formatCurrency = (value) =>
            `${currencySymbol}${d3.format(",.2f")(value)}`;

        const formatDate = d3.timeFormat("%b %-d, %Y");

        chart
            .append("g")
            .attr("class", "hero-grid")
            .call(
                d3
                    .axisLeft(yScale)
                    .ticks(6)
                    .tickSize(-innerWidth)
                    .tickFormat("")
            );

        chart
            .append("g")
            .attr("class", "hero-axis hero-axis-right")
            .attr("transform", `translate(${innerWidth},0)`)
            .call(
                d3
                    .axisRight(milestoneYScale)
                    .ticks(6)
                    .tickFormat((value) =>
                        `${currencySymbol}${d3.format("~s")(value)}`
                    )
            );

        chart
            .append("g")
            .attr("class", "hero-axis")
            .attr(
                "transform",
                `translate(0,${innerHeight})`
            )
            .call(
                d3
                    .axisBottom(xScale)
                    .ticks(7)
                    .tickFormat(d3.timeFormat("%b %-d"))
            );

        chart
            .append("g")
            .attr("class", "hero-axis")
            .call(
                d3
                    .axisLeft(yScale)
                    .ticks(6)
                    .tickFormat((value) =>
                        `${currencySymbol}${d3.format("~s")(value)}`
                    )
            );

        const lineGenerator = (seriesName) =>
            d3
                .line()
                .defined((row) =>
                    Number.isFinite(row[seriesName])
                )
                .x((row) => xScale(row.__date))
                .y((row) => yScale(row[seriesName]))
                .curve(d3.curveMonotoneX);

        const today = d3.timeDay.floor(new Date());

        const includesToday =
            today >= xDomain[0] &&
            today <= xDomain[1];

        const animationOriginDate = includesToday
            ? today
            : xDomain[0];

        const animationOriginX = xScale(
            animationOriginDate
        );

        const clipId =
            `hero-line-clip-${Math.random()
                .toString(36)
                .slice(2)}`;

        const clipPath = svg
            .append("defs")
            .append("clipPath")
            .attr("id", clipId);

        const leftClip = clipPath
            .append("rect")
            .attr("x", margin.left + animationOriginX)
            .attr("y", margin.top)
            .attr("width", 0)
            .attr("height", innerHeight);

        const rightClip = clipPath
            .append("rect")
            .attr("x", margin.left + animationOriginX)
            .attr("y", margin.top)
            .attr("width", 0)
            .attr("height", innerHeight);

        const lineLayer = svg
            .append("g")
            .attr(
                "clip-path",
                `url(#${clipId})`
            );

        seriesNames.forEach((seriesName) => {
            const style =
                options.line_styles?.[seriesName] ?? {};

            lineLayer
                .append("path")
                .datum(seriesData)
                .attr("class", "hero-series-line")
                .attr(
                    "transform",
                    `translate(${margin.left},${margin.top})`
                )
                .attr(
                    "stroke",
                    style.color ??
                        options.default_line_color ??
                        "#7a7a80"
                )
                .attr(
                    "stroke-width",
                    style.width ??
                        options.default_line_width ??
                        2
                )
                .attr("d", lineGenerator(seriesName));
        });

        const respectReducedMotion =
            options.respect_reduced_motion ?? true;
        const reducedMotion =
            respectReducedMotion &&
            window.matchMedia(
                "(prefers-reduced-motion: reduce)"
            ).matches;

        const lineAnimationDuration = reducedMotion
            ? 0
            : options.line_animation_ms ?? 1800;

        leftClip
            .transition()
            .duration(lineAnimationDuration)
            .ease(d3.easeCubicInOut)
            .attr("x", margin.left)
            .attr("width", animationOriginX);

        rightClip
            .transition()
            .duration(lineAnimationDuration)
            .ease(d3.easeCubicInOut)
            .attr(
                "width",
                innerWidth - animationOriginX
            );

        function interpolateSeriesValue(
            data,
            targetDate,
            seriesName
        ) {
            const exactRow = data.find(
                (row) =>
                    +d3.timeDay.floor(row.__date) ===
                    +targetDate
            );

            if (
                exactRow &&
                Number.isFinite(exactRow[seriesName])
            ) {
                return exactRow[seriesName];
            }

            const insertionIndex = d3.bisector(
                (row) => row.__date
            ).left(data, targetDate);

            const leftRow = data[insertionIndex - 1];
            const rightRow = data[insertionIndex];

            if (!leftRow || !rightRow) {
                return null;
            }

            const leftValue = leftRow[seriesName];
            const rightValue = rightRow[seriesName];

            if (
                !Number.isFinite(leftValue) ||
                !Number.isFinite(rightValue)
            ) {
                return null;
            }

            const proportion =
                (targetDate - leftRow.__date) /
                (rightRow.__date - leftRow.__date);

            return (
                leftValue +
                proportion * (rightValue - leftValue)
            );
        }

        function positionTooltip(event) {
            const container =
                document.getElementById(
                    "hero-chart-container"
                );

            const containerBounds =
                container.getBoundingClientRect();

            const tooltipNode = tooltip.node();

            const proposedLeft =
                event.clientX -
                containerBounds.left +
                14;

            const proposedTop =
                event.clientY -
                containerBounds.top -
                12;

            const maximumLeft =
                containerBounds.width -
                tooltipNode.offsetWidth -
                8;

            tooltip
                .style(
                    "left",
                    `${Math.min(
                        proposedLeft,
                        maximumLeft
                    )}px`
                )
                .style(
                    "top",
                    `${Math.max(8, proposedTop)}px`
                );
        }

        function showTooltip(event, rows) {
            const escapeHtml = (value) =>
                String(value ?? "")
                    .replaceAll("&", "&amp;")
                    .replaceAll("<", "&lt;")
                    .replaceAll(">", "&gt;")
                    .replaceAll('"', "&quot;")
                    .replaceAll("'", "&#039;");

            tooltip
                .html(
                    rows
                        .map(
                            ([label, value]) => `
                                <div class="hero-chart-tooltip-row">
                                    <span class="hero-chart-tooltip-label">
                                        ${escapeHtml(label)}
                                    </span>

                                    <span class="hero-chart-tooltip-value">
                                        ${escapeHtml(value)}
                                    </span>
                                </div>
                            `
                        )
                        .join("")
                )
                .attr("hidden", null);

            positionTooltip(event);
        }

        function hideTooltip() {
            tooltip.attr("hidden", true);
        }

        if (includesToday) {
            const todayValue = interpolateSeriesValue(
                seriesData,
                today,
                primarySeries
            );

            if (Number.isFinite(todayValue)) {
                chart
                    .append("line")
                    .attr("class", "hero-today-guide")
                    .attr("x1", xScale(today))
                    .attr("x2", xScale(today))
                    .attr("y1", 0)
                    .attr("y2", innerHeight);

                chart
                    .append("circle")
                    .attr("class", "hero-today-dot")
                    .attr("cx", xScale(today))
                    .attr("cy", yScale(todayValue))
                    .attr("r", 6)
                    .attr(
                        "fill",
                        options.today_color ?? "#2878d0"
                    )
                    .attr(
                        "stroke",
                        "var(--report-surface-color)"
                    )
                    .attr("stroke-width", 2)
                    .on("mouseenter", (event) => {
                        showTooltip(event, [
                            [
                                "Date",
                                formatDate(today),
                            ],
                            [
                                "Value",
                                formatCurrency(todayValue),
                            ],
                        ]);
                    })
                    .on("mousemove", positionTooltip)
                    .on("mouseleave", hideTooltip);
            }
        }

        const milestoneDelay =
            lineAnimationDuration +
            (options.milestone_delay_ms ?? 150);
        const milestoneStagger = reducedMotion
            ? 0
            : options.milestone_stagger_ms ?? 130;
        const milestonePoints = chart
            .append("g")
            .selectAll("circle")
            .data(milestoneData)
            .join("circle")
            .attr("class", "hero-milestone-dot")
            .attr("cx", (item) => xScale(item.__date))
            .attr("cy", (item) => milestoneYScale(item.Amount))
            .attr("r", 0)
            .attr("fill", options.milestone_color ?? "#a05a9c")
            .attr("stroke", "var(--report-surface-color)")
            .attr("stroke-width", 1.5)
            .on("mouseenter", (event, item) => {
                const rows = [["Date", formatDate(item.__date)]];

                item.Milestones.forEach((milestone) => {
                    rows.push([
                        milestone.name,
                        `${milestone.account}: ${formatCurrency(Number(milestone.balance))}`,
                    ]);
                });

                showTooltip(event, rows);
            })
            .on("mousemove", positionTooltip)
            .on("mouseleave", hideTooltip);

        milestonePoints
            .transition()
            .delay(
                (_, index) =>
                    milestoneDelay + index * milestoneStagger
            )
            .duration(reducedMotion ? 0 : 280)
            .ease(d3.easeBackOut.overshoot(1.4))
            .attr("r", 12);

        const transactionDelay =
            lineAnimationDuration +
            (options.transaction_delay_ms ?? 150);

        const transactionStagger =
            reducedMotion
                ? 0
                : options.transaction_stagger_ms ?? 130;

        const transactionPoints = chart
            .append("g")
            .selectAll("circle")
            .data(transactionData)
            .join("circle")
            .attr("class", "hero-transaction-dot")
            .attr(
                "cx",
                (transaction) =>
                    xScale(transaction.__date)
            )
            .attr(
                "cy",
                (transaction) =>
                    yScale(transaction.Amount)
            )
            .attr("r", 0)
            .attr(
                "fill",
                options.transaction_color ?? "#929298"
            )
            .attr(
                "stroke",
                "var(--report-surface-color)"
            )
            .attr("stroke-width", 1.5)
            .on("mouseenter", (event, transaction) => {
                showTooltip(event, [
                    [
                        "Date",
                        formatDate(transaction.__date),
                    ],
                    [
                        "Amount",
                        formatCurrency(transaction.Amount),
                    ],
                    [
                        "Memo",
                        transaction.Memo ?? "",
                    ],
                ]);
            })
            .on("mousemove", positionTooltip)
            .on("mouseleave", hideTooltip);

        transactionPoints
            .transition()
            .delay(
                (_, index) =>
                    transactionDelay +
                    index * transactionStagger
            )
            .duration(reducedMotion ? 0 : 280)
            .ease(d3.easeBackOut.overshoot(1.4))
            .attr("r", 10);
    }

    renderHeroChart(heroChartPayload);
})();

// static/dashboard.js – Generic sensor dashboard

// ========== SIDEBAR & UTILITIES ==========
function toggleMenu() {
    var menu = document.querySelector('.menu-items');
    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

function updateLat() {
    var newLat = prompt("Enter new latitude:");
    if (newLat !== null && newLat !== "") {
        document.getElementById("latitude").textContent = newLat;
        fetch('/updateLatitude', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ latitude: parseFloat(newLat) })
        })
        .then(res => res.json())
        .then(data => console.log('Latitude updated'))
        .catch(err => console.error('Error updating latitude:', err));
    }
}

function updateLong() {
    var newLong = prompt("Enter new longitude:");
    if (newLong !== null && newLong !== "") {
        document.getElementById("longitude").textContent = newLong;
        fetch('/updateLongitude', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ longitude: parseFloat(newLong) })
        })
        .then(res => res.json())
        .then(data => console.log('Longitude updated'))
        .catch(err => console.error('Error updating longitude:', err));
    }
}

function updateSW() {
    fetch('/update_sw', { method: 'POST' })
        .then(res => console.log('Software update initiated'))
        .catch(err => console.error('Update error:', err));
}

function handleRebootClick() {
    fetch('/reboot', { method: 'POST' })
        .then(res => console.log('Reboot initiated'))
        .catch(err => console.error('Reboot error:', err));
}

function handleShutdownClick() {
    fetch('/shutdown', { method: 'POST' })
        .then(res => console.log('Shutdown initiated'))
        .catch(err => console.error('Shutdown error:', err));
}

function loadGlobalCO2() {
    fetch('http://192.168.1.162:5000/')
        .then(response => response.text())
        .then(data => {
            document.querySelector('.home-section').innerHTML = data;
        })
        .catch(err => console.error('Error loading global CO2 map:', err));
}

// ========== DYNAMIC SENSOR DASHBOARD ==========
(function() {
    'use strict';

    const MAX_POINTS = 360;
    let currentDuration = 'realtime';
    let pollingPaused = false;
    let pollInterval = null;
    const sensors = {};

    // Global CO₂ history (shared as y2 trace on every other chart)
    let co2XArray = [];
    let co2YArray = [];
    let co2Meta = null;
    
    // Location state for night shading
    let currentLat = null;
    let currentLng = null;
    
    // ---- Helper: compute sunrise/sunset for a given date ----
    function getSunTimes(date, lat, lng) {
        const rad = Math.PI / 180;
        const d = Math.floor(date.valueOf() / 86400000 - 0.5 + 2440588 - 2451545) + 0.5 - lng / 360;
        const M = (357.5291 + 0.98560028 * d) % 360;
        const C = 1.9148 * Math.sin(M * rad) + 0.02 * Math.sin(2 * M * rad) + 0.0003 * Math.sin(3 * M * rad);
        const L = (M + C + 180 + 102.9372) % 360;
        const Jtransit = 2451545 + d + 0.0053 * Math.sin(M * rad) - 0.0069 * Math.sin(2 * L * rad);
        const sinDec = Math.sin(L * rad) * Math.sin(23.44 * rad);
        const cosDec = Math.cos(Math.asin(sinDec));
        const cosH = (Math.sin(-0.833 * rad) - Math.sin(lat * rad) * sinDec) / (Math.cos(lat * rad) * cosDec);
        if (cosH > 1) return { sunrise: null, sunset: null };   // polar night
        if (cosH < -1) return { sunrise: null, sunset: null };  // polar day
        const H = Math.acos(cosH) / rad;
        const toDate = j => new Date((j - 2440587.5) * 86400000);
        return {
            sunrise: toDate(Jtransit - H / 360),
            sunset:  toDate(Jtransit + H / 360)
        };
    }
    
    // ---- Helper: build Plotly shapes for night periods ----

    function buildNightShapes(xMin, xMax, lat, lng) {
        const shapes = [];
        if (lat === null || lng === null) return shapes;
        if (!(xMin instanceof Date) || !(xMax instanceof Date)) return shapes;
        if (xMin >= xMax) return shapes;
    
        // Start at noon the day before xMin so we catch the first night
        let day = new Date(xMin);
        day.setHours(12, 0, 0, 0);
        day.setDate(day.getDate() - 1);
    
        let prevSunset = null;
        while (day.getTime() <= xMax.getTime() + 86400000) {
            const { sunrise, sunset } = getSunTimes(day, lat, lng);
            if (prevSunset && sunrise) {
                // Clip to visible window
                const start = prevSunset < xMin ? xMin : prevSunset;
                const end   = sunrise   > xMax ? xMax : sunrise;
                if (start < end) {
                    shapes.push({
                        type: 'rect',
                        xref: 'x', yref: 'paper',
                        x0: start.toISOString(),
                        x1: end.toISOString(),
                        y0: 0, y1: 1,
                        fillcolor: 'rgba(0, 0, 50, 0.10)',
                        line: { width: 0 },
                        layer: 'below'
                    });
                }
            }
            prevSunset = sunset;
            day.setDate(day.getDate() + 1);
        }
        return shapes;
    }
    
    // ---- Helper: clean sensor name for display ----
    function getDisplayName(raw) {
        // Special cases
        if (raw === 'co2') return 'CO\u2082';
        let name = raw;
        // Remove 'weather_' prefix
        if (name.startsWith('weather_')) {
            name = name.substring(8);
        }
        // Replace underscores with spaces
        name = name.replace(/_/g, ' ');
        // Capitalise first letter of each word
        name = name.replace(/\b\w/g, c => c.toUpperCase());
        return name;
    }
    function getIconForSensor(rawName) {
        const name = rawName.toLowerCase();
        console.log('getIconForSensor:', rawName);   // ADD THIS
        if (name.includes('temperature') || name === 'temp') return 'bxs-thermometer';
        if (name.includes('humidity')) return 'bxs-droplet-half';
        if (name.includes('pressure') || name.includes('barometer')) return 'bxs-tachometer';
        if (name.includes('co2') || name.includes('carbon')) return 'bxs-flask';
        if (name.includes('wind_speed') || name.includes('speed')) return 'bx-wind';
        if (name.includes('wind_direction') || name.includes('direction')) return 'bxs-compass';
        if (name.includes('rain')) return 'bxs-cloud-rain';
        if (name.includes('solar')) return 'bxs-sun';
        // default
        return 'bxs-dashboard';
    }
    // ---- Helper: get sizes ----
    function getSizes() {
        const w = document.documentElement.clientWidth;
        const h = document.documentElement.clientHeight;
        return {
            gaugeWidth: Math.min(250, w * 0.9),
            gaugeHeight: 200,
            chartWidth: Math.min(900, w * 0.95),
            chartHeight: Math.min(290, h * 0.35)
        };
    }

    // ---- Build UI for a single sensor ----
    function createSensorElements(name, meta) {
        const displayName = getDisplayName(name);
        const iconClass = getIconForSensor(name);
        // Value box
        const boxContainer = document.getElementById('sensor-boxes');
        const box = document.createElement('div');
        box.className = 'box';
        box.id = 'sensor-' + name;
        box.innerHTML = `
            <div class="right-side">
                <div class="box-topic">${displayName}</div>
                <div class="number" id="val-${name}">--</div>
                <div style="font-size:14px;color:#888;">${meta.unit || ''}</div>
            </div>
            <i class="bx ${iconClass} readings" style="color:${meta.color || '#666'}"></i>
        `;
        boxContainer.appendChild(box);

        // Gauge
        const gaugeContainer = document.getElementById('gauge-container');
        const gaugeDiv = document.createElement('div');
        gaugeDiv.className = 'gauge-box';
        gaugeDiv.id = 'gauge-' + name;
        gaugeContainer.appendChild(gaugeDiv);

        // History chart
        // Skip the standalone CO₂ history chart – CO₂ is shown as y2 on every other chart
        if (name !== 'co2') {
            const historyContainer = document.getElementById('history-container');
            const histDiv = document.createElement('div');
            histDiv.className = 'history-divs';
            histDiv.id = 'history-' + name;
            historyContainer.appendChild(histDiv);
        }
    }

    // ---- Create Plotly charts ----
    function createChartsForSensor(name) {
        const sensor = sensors[name];
        const meta = sensor.meta;
        const displayName = getDisplayName(name);
        const sizes = getSizes();

        // Gauge
        const gaugeLayout = {
            width: sizes.gaugeWidth,
            height: sizes.gaugeHeight,
            margin: { t: 10, b: 0, l: 40, r: 0 }
        };
        const gaugeData = [{
            domain: { x: [0, 1], y: [0, 1] },
            value: 0,
            title: { text: displayName, font: { size: 12 } },
            type: 'indicator',
            mode: 'gauge+number',
            gauge: {
                axis: { range: [meta.min || 0, meta.max || 100] },
                steps: [
                    { range: [meta.min || 0, (meta.min+meta.max)/2 || 50], color: 'lightgray' },
                    { range: [(meta.min+meta.max)/2 || 50, meta.max || 100], color: 'gray' }
                ],
                threshold: {
                    line: { color: 'red', width: 4 },
                    thickness: 0.75,
                    value: meta.max * 0.9 || 90
                }
            }
        }];
        Plotly.newPlot('gauge-' + name, gaugeData, gaugeLayout);

        // ---- History chart ----
        // Skip the standalone CO₂ chart – CO₂ will be shown as y2 on every other chart.
        if (name === 'co2') {
            return;
        }

        const co2Trace = {
            x: [],
            y: [],
            name: 'CO₂',
            mode: 'lines+markers',
            type: 'scatter',
            yaxis: 'y2',
            line:   { color: '#383838', width: 2 },
            marker: { color: '#383838' }
        };

        
        // History chart
        const lineLayout = {
            autosize: true,
            title: { text: `${displayName} (${meta.unit || ''})` },
            xaxis: { type: 'date' },

            yaxis: {
                title: displayName,
                range: [meta.min || 0, meta.max || 100]
            },
            yaxis2: {
                title: 'CO₂ (ppm)',
                overlaying: 'y',
                side: 'right',
                range: [co2Meta?.min || 200, co2Meta?.max || 1000],
                showgrid: false,
                color: '#383838'
            },


            legend: {
                x: 0.02, y: 0.98,
                xanchor: 'left', yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.7)',
                bordercolor: '#ccc',
                borderwidth: 1,
                font: { size: 11 }
            },
            font: { size: 14, color: '#7f7f7f' },
            colorway: [meta.color || '#1f77b4', '#008080'],
            width: sizes.chartWidth,
            height: sizes.chartHeight,
            margin: { t: 40, b: 40, pad: 5 }
        };
        const trace = {
            x: [],
            y: [],
            name: displayName,
            mode: 'lines+markers',
            type: 'scatter'
        };
        sensor.trace = trace;
        sensor.layout = lineLayout;

        sensor.hasCo2Axis = true;
        Plotly.newPlot('history-' + name, [trace, co2Trace], lineLayout);
    }

    // ---- Initialisation ----
    function init() {
        fetch('/v2/sensorMetadata')
            .then(res => res.json())
            .then(metadataArray => {
                if (!metadataArray.length) {
                    document.getElementById('sensor-boxes').innerHTML = '<p>No sensors found.</p>';
                    return;
                }
                // ---- Sort: co2 first, then temperature, then rest ----
                const priority = {
                    'co2': 0,
                    'temperature': 1
                };
                metadataArray.sort((a, b) => {
                    const orderA = (a.name in priority) ? priority[a.name] : 2;
                    const orderB = (b.name in priority) ? priority[b.name] : 2;
                    return orderA - orderB;
                });
                metadataArray.forEach(meta => {
                    const name = meta.name;
                    if (name === 'co2') co2Meta = meta;
                    sensors[name] = {
                        meta: meta,
                        xArray: [],
                        yArray: []
                    };
                    createSensorElements(name, meta);
                });
                Object.keys(sensors).forEach(name => createChartsForSensor(name));

                // Read current dropdown selection
                const btnText = document.querySelector('.dropbtn')?.textContent.trim().toLowerCase().replace(' ', '_');
                if (btnText && ['realtime','1_hour','1_day','1_week','1_month','1_year','10_years'].includes(btnText)) {
                    currentDuration = btnText;
                }
                refreshHistory();
                startPolling();
            })
            .catch(err => console.error('Init error:', err));
    }

    // ---- Polling ----
    function updateSensorReadings() {
        fetch('/v2/sensorReadings')
            .then(res => res.json())
            .then(data => {
                // Update location

                if (data.latitude !== undefined && data.longitude !== undefined) {
                    currentLat = parseFloat(data.latitude);
                    currentLng = parseFloat(data.longitude);
                    document.getElementById('latitude').textContent = currentLat.toFixed(4);
                    document.getElementById('longitude').textContent = currentLng.toFixed(4);
                
                    // First time we know the location → apply shading to the already‑drawn charts
                    if (!window._nightShadingApplied) {
                        window._nightShadingApplied = true;
                        applyNightShading();
                    }
                }
                
                // Process readings

                const readings = data.readings || [];
                readings.forEach(item => {
                    const name = item.name;
                    const sensor = sensors[name];
                    if (!sensor) return;
                    const value = parseFloat(item.value);
                
                    // Update value box
                    const valSpan = document.getElementById('val-' + name);
                    if (valSpan) valSpan.textContent = value.toFixed(1);
                
                    // Update gauge
                    Plotly.update('gauge-' + name, { value: value });
                
                    // Append to history (if not paused)
                    if (pollingPaused) return;
                
                    if (name === 'co2') {
                        // CO₂ has no standalone chart – store globally and push to y2 of every other chart
                        co2XArray.push(new Date());
                        co2YArray.push(value);
                        if (co2XArray.length > MAX_POINTS) {
                            co2XArray.shift();
                            co2YArray.shift();
                        }
                        Object.keys(sensors).forEach(otherName => {
                            const other = sensors[otherName];
                            if (other.hasCo2Axis) {
                                Plotly.update('history-' + otherName, {
                                    x: [other.xArray.slice(), co2XArray.slice()],
                                    y: [other.yArray.slice(), co2YArray.slice()]
                                });
                            }
                        });
                    } else {
                        sensor.xArray.push(new Date());
                        sensor.yArray.push(value);
                        if (sensor.xArray.length > MAX_POINTS) {
                            sensor.xArray.shift();
                            sensor.yArray.shift();
                        }
                        if (sensor.hasCo2Axis) {
                            Plotly.update('history-' + name, {
                                x: [sensor.xArray.slice(), co2XArray.slice()],
                                y: [sensor.yArray.slice(), co2YArray.slice()]
                            });
                        } else {
                            Plotly.update('history-' + name, {
                                x: [sensor.xArray.slice()],
                                y: [sensor.yArray.slice()]
                            });
                        }
                    }
                });
            })
            .catch(err => console.error('Polling error:', err));
    }

    function refreshHistory() {
        const url = `/v2/refreshHistory?maxPoints=${MAX_POINTS}&duration=${currentDuration}`;
        fetch(url)
            .then(res => res.json())
            .then(data => {
                // ---- 1. Store CO₂ globally ----
                const co2Pairs = data['co2'] || [];
                const co2Sorted = co2Pairs
                    .map(p => ({ x: new Date(p[0]), y: p[1] }))
                    .sort((a, b) => a.x - b.x);
                co2XArray = co2Sorted.map(p => p.x);
                co2YArray = co2Sorted.map(p => p.y);
    
                // ---- 2. Compute overall time range ----
                let xMin = null, xMax = null;
                const consider = arr => {
                    if (!arr.length) return;
                    const first = arr[0];
                    const last = arr[arr.length - 1];
                    if (xMin === null || first < xMin) xMin = first;
                    if (xMax === null || last > xMax) xMax = last;
                };
                consider(co2XArray);
                Object.keys(data).forEach(name => {
                    if (name === 'co2') return;
                    const pairs = data[name] || [];
                    if (!pairs.length) return;
                    const times = pairs.map(p => new Date(p[0])).sort((a, b) => a - b);
                    consider(times);
                });
    
                // ---- 3. Night shading ----
                const shapes = (xMin && xMax)
                    ? buildNightShapes(xMin, xMax, currentLat, currentLng)
                    : [];
    
                // ---- 4. Update each chart's y1 (and y2 = CO₂) ----
                Object.keys(data).forEach(name => {
                    if (name === 'co2') return;    // no standalone CO₂ chart
                    const sensor = sensors[name];
                    if (!sensor) return;
                    const pairs = data[name] || [];
                    const sorted = pairs
                        .map(p => ({ x: new Date(p[0]), y: p[1] }))
                        .sort((a, b) => a.x - b.x);
                    const xArr = sorted.map(p => p.x);
                    const yArr = sorted.map(p => p.y);
                    sensor.xArray = xArr;
                    sensor.yArray = yArr;
    
                    if (sensor.hasCo2Axis) {
                        Plotly.update('history-' + name,
                            { x: [xArr, co2XArray], y: [yArr, co2YArray] },
                            { shapes: shapes });
                    } else {
                        Plotly.update('history-' + name,
                            { x: [xArr], y: [yArr] },
                            { shapes: shapes });
                    }
                });
            })
            .catch(err => console.error('History refresh error:', err));
    }
    
    function applyNightShading() {
        if (currentLat === null || currentLng === null) return;
    
        // Union range across all sensors that already have data
        let xMin = null, xMax = null;
        Object.values(sensors).forEach(s => {
            if (!s.xArray || s.xArray.length === 0) return;
            const first = s.xArray[0];
            const last  = s.xArray[s.xArray.length - 1];
            if (xMin === null || first < xMin) xMin = first;
            if (xMax === null || last  > xMax) xMax = last;
        });
        if (!xMin || !xMax) return;
    
        const shapes = buildNightShapes(xMin, xMax, currentLat, currentLng);
        Object.keys(sensors).forEach(name => {
            Plotly.relayout('history-' + name, { shapes: shapes });
        });
    }

    
    function startPolling() {
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(() => {
            if (!pollingPaused) updateSensorReadings();
        }, 30000);
    }

    // ---- Dropdown listener ----
    function attachDropdownListener() {
        const links = document.querySelectorAll('.dropdown-content a');
        links.forEach(link => {
            link.addEventListener('click', function(e) {
                const val = this.dataset.value;
                if (val === 'pause') {
                    pollingPaused = true;
                    return;
                }
                // Resume if paused
                pollingPaused = false;
                currentDuration = val;
                // Update button text
                const btn = document.querySelector('.dropbtn');
                if (btn) btn.textContent = this.textContent.trim();
                refreshHistory();
            });
        });
    }

    // ---- Resize handler ----
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            const sizes = getSizes();
            Object.keys(sensors).forEach(name => {
                Plotly.relayout('gauge-' + name, {
                    width: sizes.gaugeWidth,
                    height: sizes.gaugeHeight
                });
                Plotly.relayout('history-' + name, {
                    width: sizes.chartWidth,
                    height: sizes.chartHeight
                });
            });
        }, 300);
    });

    // ---- Start ----
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            init();
            attachDropdownListener();
        });
    } else {
        init();
        attachDropdownListener();
    }

})();

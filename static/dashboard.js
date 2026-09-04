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

    // ---- Helper: clean sensor name for display ----
    function getDisplayName(raw) {
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
            <i class="bx bxs-thermometer readings" style="color:${meta.color || '#666'}"></i>
        `;
        boxContainer.appendChild(box);

        // Gauge
        const gaugeContainer = document.getElementById('gauge-container');
        const gaugeDiv = document.createElement('div');
        gaugeDiv.className = 'gauge-box';
        gaugeDiv.id = 'gauge-' + name;
        gaugeContainer.appendChild(gaugeDiv);

        // History chart
        const historyContainer = document.getElementById('history-container');
        const histDiv = document.createElement('div');
        histDiv.className = 'history-divs';
        histDiv.id = 'history-' + name;
        historyContainer.appendChild(histDiv);
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

        // History chart
        const lineLayout = {
            autosize: true,
            title: { text: `${displayName} (${meta.unit || ''})` },
            xaxis: { type: 'date' },
            yaxis: { range: [meta.min || 0, meta.max || 100] },
            font: { size: 14, color: '#7f7f7f' },
            colorway: [meta.color || '#1f77b4'],
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
        Plotly.newPlot('history-' + name, [trace], lineLayout);
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
                metadataArray.forEach(meta => {
                    const name = meta.name;
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
                // Fetch initial readings to set latitude/longitude immediately
                setTimeout(updateSensorReadings, 200);
            })
            .catch(err => console.error('Init error:', err));
    }

    // ---- Polling ----
    function updateSensorReadings() {
    fetch('/v2/sensorReadings')
        .then(res => res.json())
        .then(data => {
            // Update latitude/longitude
            if (data.latitude !== undefined) {
                const latSpan = document.getElementById('latitude');
                if (latSpan) latSpan.textContent = data.latitude.toFixed(4);
            }
            if (data.longitude !== undefined) {
                const longSpan = document.getElementById('longitude');
                if (longSpan) longSpan.textContent = data.longitude.toFixed(4);
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
                if (valSpan) valSpan.textContent = value.toFixed(2);

                // Update gauge
                Plotly.update('gauge-' + name, { value: value });

                // Append to history (if not paused)
                if (!pollingPaused) {
                    sensor.xArray.push(new Date());
                    sensor.yArray.push(value);
                    if (sensor.xArray.length > MAX_POINTS) {
                        sensor.xArray.shift();
                        sensor.yArray.shift();
                    }
                    Plotly.update('history-' + name, {
                        x: [sensor.xArray.slice()],
                        y: [sensor.yArray.slice()]
                    });
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
                Object.keys(data).forEach(name => {
                    const sensor = sensors[name];
                    if (!sensor) return;
                    const pairs = data[name] || [];
                    const sorted = pairs.map(p => ({ x: new Date(p[0]), y: p[1] }))
                                       .sort((a,b) => a.x - b.x);
                    const xArr = sorted.map(p => p.x);
                    const yArr = sorted.map(p => p.y);
                    sensor.xArray = xArr;
                    sensor.yArray = yArr;
                    Plotly.update('history-' + name, {
                        x: [xArr],
                        y: [yArr]
                    });
                });
            })
            .catch(err => console.error('History refresh error:', err));
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

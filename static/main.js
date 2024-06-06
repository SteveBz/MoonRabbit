var temperatureHistoryDiv = document.getElementById("temperature-history");
var humidityHistoryDiv = document.getElementById("humidity-history");
var pressureHistoryDiv = document.getElementById("pressure-history");
var co2HistoryDiv = document.getElementById("co2-history");

var temperatureGaugeDiv = document.getElementById("temperature-gauge");
var humidityGaugeDiv = document.getElementById("humidity-gauge");
var pressureGaugeDiv = document.getElementById("pressure-gauge");
var co2GaugeDiv = document.getElementById("co2-gauge");
const number = 100;

// JavaScript to toggle sidebar on hamburger menu click
function toggleMenu() {
  var menu = document.querySelector('.menu-items');
  menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}
function loadGlobalCO2() {
  fetch('http://192.168.1.162:5000/')
    .then(response => response.text())
    .then(data => {
      console.log(data); // Log response data to console
      document.querySelector('.home-section').innerHTML = data;
    })
    .catch(error => {
      console.error('Error fetching global CO2 data:', error);
    });
}


// JavaScript for triggering refresh on option selection
document.addEventListener("DOMContentLoaded", function() {
    // Get the dropdown element
    var dropdown = document.querySelector('.dropdown');
    var dropdownButton = document.querySelector('.dropbtn');
    var dropdownContent = document.querySelector('.dropdown-content');
    var isDropdownOpen = false;

    // JavaScript to toggle sidebar on hamburger menu click
    var ddcontent = document.querySelector('.dropdown-content');
    //ddcontent.style.display = ddcontent.style.display != 'none' ? 'block' : 'none';

    // Add event listener for when an option is selected
    dropdown.addEventListener('click', function(event) {
    
        // Check if the clicked element is an <a> tag (option)
        if (event.target.tagName === 'A') {
            // Prevent the default action of the <a> tag
            event.preventDefault();
            // Get the text content of the selected option
            SELECTED_OPTION = event.target.textContent.trim();
            // Trigger the appropriate action based on the selected option
            switch (SELECTED_OPTION) {
                case 'Pause':
                    pausePolling();
                    break;
                case 'Realtime':
                    setDurationAndRefresh('realtime'); // Simplified call
                    break;
                case '1 Hour':
                    setDurationAndRefresh('1_hour'); // Simplified call
                    break;
                case '1 Day':
                    setDurationAndRefresh('1_day'); // Simplified call
                    break;
                case '1 Week':
                    setDurationAndRefresh('1_week'); // Simplified call
                    break;
                case '1 Month':
                    setDurationAndRefresh('1_month'); // Simplified call
                    break;
                case '1 Year':
                    setDurationAndRefresh('1_year'); // Simplified call
                    break;
                case '10 Years':
                    setDurationAndRefresh('10_years'); // Simplified call
                    break;
                // Add cases for other options if needed
            }
        }
    });
    
    // Add event listener to show dropdown menu on hover or click
    dropdownButton.addEventListener('mouseover', showDropdownMenu);
    //dropdownButton.addEventListener('click', showDropdownMenu);
    
    // Add event listener to hide dropdown menu on document click
    document.addEventListener('click', function(event) {
        if (!dropdown.contains(event.target)) {
            dropdownContent.style.display = 'none';
        }
    });
});
// Helper function to set duration and refresh history
function setDurationAndRefresh(duration) {
    DURATION = duration;
    pausePolling();
    refreshHistory();
    resumePolling();
}


// Function to show dropdown menu
function showDropdownMenu() {
    var dropdownContent = document.querySelector('.dropdown-content');
    dropdownContent.style.display = 'block';
}

// Function to hide dropdown menu
function hideDropdownMenuAndUpdate(SELECTED_OPTION) {
    var dropdownContent = document.querySelector('.dropdown-content');
    dropdownContent.style.display = 'none';
    
    // Update dropdown button text with selected timeframe
    document.querySelector('.dropbtn').textContent = SELECTED_OPTION;
    
}

// Event listener for dropdown options
document.querySelectorAll('.dropdown-content a').forEach(option => {
    option.addEventListener('click', function() {
        SELECTED_OPTION = this.textContent;
        hideDropdownMenuAndUpdate(SELECTED_OPTION); // Hide dropdown menu and update selected timeframe
        updateSensorReadingsWithTimeRange(SELECTED_OPTION); // Update sensor readings based on selected time range
        
        // If the selected option is not 'Pause', resume polling
        if (SELECTED_OPTION !== 'Pause') {
            resumePolling();
        }
    });
});

// Variable to keep track of whether polling is paused or not
var pollingPaused = false;

// Function to pause polling
function pausePolling() {
    console.log('Polling paused.');
    // Implementation here
    pollingPaused = true;
}

// Function to resume polling
function resumePolling() {
    console.log('Polling resumed.');
    // Implementation here
    pollingPaused = false;
}
// History Data
var temperatureTrace = {
  x: [],
  y: [],
  name: "Temperature (\u00B0C)",
  mode: "lines+markers",
  type: "line",
};
var humidityTrace = {
  x: [],
  y: [],
  name: "Humidity (%)",
  mode: "lines+markers",
  type: "line",
};
var pressureTrace = {
  x: [],
  y: [],
  name: "Pressure (hPa)",
  mode: "lines+markers",
  type: "line",
};
var co2Trace = {
  x: [],
  y: [],
  name: "Carbon Dioxide (ppm)",
  mode: "lines+markers",
  type: "line",
};
var lineChartWidth = 900
var lineChartHeight = 290
var ticktype = "date"
var bottom = 40
var temperatureLayout = {
  autosize: true,
  title: {
    text: "Temperature (\u00B0C)",
  },
  xaxis: {
      //tickformat: format,
      type: ticktype
      //tickmode: "linear", //  If "linear", the placement of the ticks is determined by a starting position `tick0` and a tick step `dtick`
      //tick0: '00:00',
      //dtick: 15 * 60 * 1000 // milliseconds
  },
  yaxis: {
    range: [-10, 50]
  },
  font: {
    size: 14,
    color: "#7f7f7f",
  },
  colorway: ["#B22222"],
  width: lineChartWidth,
  height: lineChartHeight,
  margin: { t: 40, b: bottom, pad: 5 },
};
var humidityLayout = {
  autosize: true,
  title: {
    text: "Humidity (%)",
  },
 xaxis: {
      //tickformat: format,
      type: ticktype
      //tickmode: "linear", //  If "linear", the placement of the ticks is determined by a starting position `tick0` and a tick step `dtick`
      //tick0: '00:00',
      //dtick: 15 * 60 * 1000 // milliseconds
  },
  yaxis: {
    range: [0, 100]
  },
  font: {
    size: 14,
    color: "#7f7f7f",
  },
  colorway: ["#00008B"],
  width: lineChartWidth,
  height: lineChartHeight,
  margin: { t: 40, b: bottom, pad: 5 },
};
var pressureLayout = {
  autosize: true,
  title: {
    text: "Pressure (hPa)",
  },
  xaxis: {
      //tickformat: format,
      type: ticktype
      //tickmode: "linear", //  If "linear", the placement of the ticks is determined by a starting position `tick0` and a tick step `dtick`
      //tick0: '00:00',
      //dtick: 15 * 60 * 1000 // milliseconds
  },
  yaxis: {
    range: [850, 1100]
  },
  font: {
    size: 14,
    color: "#7f7f7f",
  },
  colorway: ["#FF4500"],
  width: lineChartWidth,
  height: lineChartHeight,
  margin: { t: 40, b: bottom, pad: 5 },
};
var co2Layout = {
  autosize: true,
  title: {
    text: "Carbon Dioxide (ppm)",
  },
  xaxis: {
      //tickformat: format,
      //xaxis_range = [00:00, 23:59],
      type: ticktype
      //tickmode: "linear", //  If "linear", the placement of the ticks is determined by a starting position `tick0` and a tick step `dtick`
      //tick0: '00:00',
      //dtick: 15 * 60 * 1000 // milliseconds
  },
  yaxis: {
    range: [200, 1000]
  },
  font: {
    size: 14,
    color: "#7f7f7f",
  },
  colorway: ["#008080"],
  width: lineChartWidth,
  height: lineChartHeight,
  margin: { t: 40, b: bottom, pad: 5 },
};

Plotly.newPlot(temperatureHistoryDiv, [temperatureTrace], temperatureLayout);
Plotly.newPlot(humidityHistoryDiv, [humidityTrace], humidityLayout);
Plotly.newPlot(pressureHistoryDiv, [pressureTrace], pressureLayout);
Plotly.newPlot(co2HistoryDiv, [co2Trace], co2Layout);

// Gauge Data
var temperatureData = [
  {
    domain: { x: [0, 1], y: [0, 1] },
    value: 0,
    title: { 
      text: "Temperature (\u00B0C)",
          font: {
          size: 12
        },
     },
    type: "indicator",
    mode: "gauge+number+delta",
    delta: { reference: 23 },
    gauge: {
      axis: { range: [null, 50] },
      steps: [
        { range: [0, 20], color: "lightgray" },
        { range: [20, 30], color: "gray" },
      ],
      threshold: {
        line: { color: "red", width: 4 },
        thickness: 0.75,
        value: 30,
      },
    },
  },
];

var humidityData = [
  {
    domain: { x: [0, 1], y: [0, 1] },
    value: 0,
    title: { 
      text: "Humidity (%)",
          font: {
          size: 12
        },
      },
    type: "indicator",
    mode: "gauge+number+delta",
    delta: { reference: 50 },
    gauge: {
      axis: { range: [null, 100] },
      steps: [
        { range: [0, 20], color: "lightgray" },
        { range: [20, 30], color: "gray" },
      ],
      threshold: {
        line: { color: "red", width: 4 },
        thickness: 0.75,
        value: 30
      },
    },
  },
];

var pressureData = [
  {
    domain: { x: [0, 1], y: [0, 1] },
    value: 0,
    title: { 
      text: "Pressure (hPa)" ,
          font: {
          size: 12
        }
    },
    type: "indicator",
    mode: "gauge+number+delta",
    delta: { reference: 1000 },
    gauge: {
      axis: { range: [850, 1100] },
      steps: [
        { range: [850, 1000], color: "lightgray" },
        { range: [1000, 1100], color: "gray" },
      ],
      threshold: {
        line: { color: "red", width: 4 },
        thickness: 0.75,
        value: 900,
      },
    },
  },
];

var co2Data = [
  {
    domain: { x: [0, 1], y: [0, 1] },
    value: 0,
    title: { 
      text: "Carbon Dioxide (ppm)",
          font: {
          size: 12
        },
      },
    type: "indicator",
    mode: "gauge+number+delta",
    delta: { reference: 420 },
    gauge: {
      axis: { range: [200, 1000] },
      steps: [
        { range: [200, 550], color: "white" },
        { range: [550, 650], color: "lightgray" },
        { range: [650, 1000], color: "gray" },
      ],
      threshold: {
        line: { color: "red", width: 4 },
        thickness: 0.75,
        value: 700,
      },
    },
  },
];
// Size of gauges
var layout = { width: 250, height: 200, margin: { t: 10, b: 0, l: 40, r: 0 } };

Plotly.newPlot(temperatureGaugeDiv, temperatureData, layout);
Plotly.newPlot(humidityGaugeDiv, humidityData, layout);
Plotly.newPlot(pressureGaugeDiv, pressureData, layout);
Plotly.newPlot(co2GaugeDiv, co2Data, layout);

// Will hold the arrays we receive from our BME280 sensor
// Temperature
let newTempXArray = [];
let newTempYArray = [];
// Humidity
let newHumidityXArray = [];
let newHumidityYArray = [];
// Pressure
let newPressureXArray = [];
let newPressureYArray = [];
// co2
let newco2XArray = [];
let newco2YArray = [];

// The maximum number of data points displayed on our scatter/line graph
let MAX_GRAPH_POINTS = 360;
let ctr = 0;

// Callback function that will retrieve our latest sensor readings and redraw our Gauge with the latest readings
function updateSensorReadings() {
  fetch(`/sensorReadings`)
    .then((response) => response.json())
    .then((jsonResponse) => {
      let temperature = jsonResponse.temperature.toFixed(2);
      let humidity = jsonResponse.humidity.toFixed(2);
      let pressure = jsonResponse.pressure.toFixed(2);
      let co2 = jsonResponse.co2.toFixed(2);
      let latitude = jsonResponse.latitude.toFixed(4);
      let longitude = jsonResponse.longitude.toFixed(4);

      updateBoxes(temperature, humidity, pressure, co2);

      updateGauge(temperature, humidity, pressure, co2);

      // Update latitude & Longitude
      updateLoc(latitude,longitude);
      
      // Update Temperature Line Chart
      updateCharts(
        temperatureHistoryDiv,
        newTempXArray,
        newTempYArray,
        temperature
      );
      // Update Humidity Line Chart
      updateCharts(
        humidityHistoryDiv,
        newHumidityXArray,
        newHumidityYArray,
        humidity
      );
      // Update Pressure Line Chart
      updateCharts(
        pressureHistoryDiv,
        newPressureXArray,
        newPressureYArray,
        pressure
      );

      // Update co2 Line Chart
      updateCharts(
        co2HistoryDiv,
        newco2XArray,
        newco2YArray,
        co2
      );
    });
}
function refreshHistory() {
    // Make a fetch request to the backend route '/refreshHistory'
    // Pass MAX_GRAPH_POINTS as a query parameter
    //DURATION='hour'
    fetch('/refreshHistory?maxPoints=' + MAX_GRAPH_POINTS + '&duration=' + DURATION)
        .then(response => response.json())
        .then(data => {
            // Handle the received historical data
            console.log('Received historical data:', data);
                      
            // Update Temperature Line Chart
            console.log('Updating temperature chart with data:', temperatureTrace);
            const temperatureData = data.temperature.map(entry => ({
                x: new Date(entry[2] + "Z"), // Assuming the date is at index 2 in the inner array
                y: entry[7] // Assuming the value is at index 7 in the inner array
            }));
            temperatureData.sort((a, b) => a.x - b.x);
            const temperatureX = temperatureData.map(entry => entry.x.toISOString());
            const temperatureY = temperatureData.map(entry => entry.y);
            temperatureTrace.x = temperatureX;
            temperatureTrace.y = temperatureY;
            
            // Update newTempXArray and newTempYArray
            newTempXArray = temperatureX.slice();
            newTempYArray = temperatureY.slice();
            updateCharts(
              temperatureHistoryDiv,
              newTempXArray,
              newTempYArray
            );
            // Update Humidity Line Chart
            console.log('Updating humidity chart with data:', humidityTrace);
            const humidityData = data.humidity.map(entry => ({
                x: new Date(entry[2] + "Z"), // Assuming the date is at index 2 in the inner array
                y: entry[7] // Assuming the value is at index 7 in the inner array
            }));
            humidityData.sort((a, b) => a.x - b.x);
            const humidityX = humidityData.map(entry => entry.x.toISOString());
            const humidityY = humidityData.map(entry => entry.y);
            humidityTrace.x = humidityX;
            humidityTrace.y = humidityY;
            // Update newHumidityXArray and newHumidityYArray
            newHumidityXArray = humidityX.slice();
            newHumidityYArray = humidityY.slice();
            updateCharts(
              humidityHistoryDiv,
              newHumidityXArray,
              newHumidityYArray
            );
            // Update Pressure Line Chart
            console.log('Updating pressure chart with data:', pressureTrace);
            const pressureData = data.pressure.map(entry => ({
                x: new Date(entry[2] + "Z"), // Assuming the date is at index 2 in the inner array
                y: entry[7] // Assuming the value is at index 7 in the inner array
            }));
            pressureData.sort((a, b) => a.x - b.x);
            const pressureX = pressureData.map(entry => entry.x.toISOString());
            const pressureY = pressureData.map(entry => entry.y);
            pressureTrace.x = pressureX;
            pressureTrace.y = pressureY;            
            // Update newPressureXArray and newPressureYArray
            newPressureXArray = pressureX.slice();
            newPressureYArray = pressureY.slice();
            updateCharts(
              pressureHistoryDiv,
              pressureTrace.x,
              pressureTrace.y
            );
      
            // Update co2 Line Chart
            // Extract date and value pairs from the array of arrays
            const co2Data = data.co2.map(entry => ({
                x: new Date(entry[2] + "Z"), // Assuming the date is at index 2 in the inner array
                y: entry[7] // Assuming the value is at index 7 in the inner array
            }));

            // Sort the co2Data array based on date (if necessary)
            co2Data.sort((a, b) => a.x - b.x);
            
            // Extract x and y arrays from co2Data
            const co2X = co2Data.map(entry => entry.x.toISOString());
            const co2Y = co2Data.map(entry => entry.y);
            
            // Update co2Trace with the new x and y arrays
            co2Trace.x = co2X;
            co2Trace.y = co2Y;
            // Update newco2XArray and newco2YArray
            newco2XArray = co2X.slice();
            newco2YArray = co2Y.slice();
            updateCharts(
              co2HistoryDiv,
              co2Trace.x,
              co2Trace.y
            );
            console.log('Updating CO2 chart with data:', co2Trace.x);
        })
        .catch(error => {
            console.error('Error refreshing history:', error);
        });
}
function updateLat() {
    // Code to update latitude and longitude values
    // You can fetch new values from the sensor or any other source here
    var newLatitude = prompt("Enter new latitude:");

    // Check if values are not empty and update only if both latitude and longitude are provided
    if (newLatitude !== null && newLatitude !== "" ) {
        // Update latitude and longitude values
        document.getElementById("latitude").textContent = newLatitude;

        // Call function to update coordinates on the server
        updateLatOnServer(newLatitude);
        
    }
}
function updateLong() {
    // Code to update latitude and longitude values
    // You can fetch new values from the sensor or any other source here
    var newLongitude = prompt("Enter new longitude:");

    // Check if values are not empty and update only if both latitude and longitude are provided
    if (newLongitude !== null && newLongitude !== "") {
        // Update latitude and longitude values
        document.getElementById("longitude").textContent = newLongitude;

        // Call function to update coordinates on the server
        updateLongOnServer(newLongitude);
    }
}

// Function to update latitude on the server
function updateLatOnServer(latitude) {
    fetch('/updateLatitude', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ latitude: latitude}),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update latitude on the server');
        }
        console.log('Latitude updated successfully on the server');
    })
    .catch(error => {
        console.error('Error updating latitude on the server:', error);
    });
}
// Function to update longitude on the server
function updateLongOnServer(longitude ) {
    fetch('/updateLongitude', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ longitude: longitude}),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update longitude on the server');
        }
        console.log('longitude updated successfully on the server');
    })
    .catch(error => {
        console.error('Error updating longitude on the server:', error);
    });
}

function updateBoxes(temperature, humidity, pressure, co2) {
  let temperatureDiv = document.getElementById("temperature");
  let humidityDiv = document.getElementById("humidity");
  let pressureDiv = document.getElementById("pressure");
  let co2Div = document.getElementById("co2");

  temperatureDiv.innerHTML = temperature + " \u00B0C";
  humidityDiv.innerHTML = humidity + " %";
  pressureDiv.innerHTML = pressure + " hPa";
  co2Div.innerHTML = co2 + " ppm";
}

function updateLoc(latitude, longitude) {
  let latitudeDiv = document.getElementById("latitude");
  let longitudeDiv = document.getElementById("longitude");

  latitudeDiv.innerHTML = " "+ latitude + "\u00B0";
  longitudeDiv.innerHTML = " "+ longitude + "\u00B0";
}

function updateGauge(temperature, humidity, pressure, co2) {
  var temperature_update = {
    value: temperature,
  };
  var humidity_update = {
    value: humidity,
  };
  var pressure_update = {
    value: pressure,
  };
  var co2_update = {
    value: co2,
  };
  Plotly.update(temperatureGaugeDiv, temperature_update);
  Plotly.update(humidityGaugeDiv, humidity_update);
  Plotly.update(pressureGaugeDiv, pressure_update);
  Plotly.update(co2GaugeDiv, co2_update);
}

function updateCharts(lineChartDiv, xArray, yArray, sensorRead) {
  if (xArray.length >= MAX_GRAPH_POINTS) {
    xArray.shift();
    yArray.shift();
  }
  // Only push sensorRead into yArray if it is defined
  if (typeof sensorRead !== 'undefined') {
    var currentdate = new Date();
    ctr++
    xArray.push(currentdate);
    yArray.push(sensorRead);
  };
  var data_update = {
    x: [xArray.slice()], // Slice the array to create a copy
    y: [yArray.slice()], // Slice the array to create a copy
  };

  Plotly.update(lineChartDiv, data_update);
}

// Function to update sensor readings with the given time range
function updateSensorReadingsWithTimeRange(timeRange) {
    // Implement logic to update sensor readings based on the selected time range
}

// Function to set timeout based on the selected time range
//function setTimeoutBasedOnTimeRange(timeRange) {
//    switch (timeRange) {
//        case 'Realtime':
//            return 30000; // 30 seconds for realtime
//        case 'Last Day':
//            return 60000; // 1 minute for last day
//        case '1 Month':
//            return 1800000; // 30 minutes for 1 month
//        case '1 Year':
//            return 3600000; // 1 hour for 1 year
//        case '10 Years':
//            return 86400000; // 24 hours for 10 years
//        default:
//            return 30000; // Default to 30 seconds for realtime
//    }
//}


// Function to handle the "Reboot" click event
function handleRebootClick(event) {
    // Prevent default link behavior (e.g., page navigation)
    // event.preventDefault();
    // Add your code to handle the "Reboot" action (e.g., initiate a reboot request)
    fetch('/reboot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({}), // No data to send in the request body for a reboot
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to initiate reboot on the server');
        }
        console.log('Reboot initiated successfully on the server');
    })
    .catch(error => {
        console.error('Error initiating reboot on the server:', error);
    });
    // For demonstration purposes, you can log a message
    console.log('Initiating reboot...');
}

// Continuos loop that runs every 30 seconds to update our web page with the latest sensor readings
(function loop() {
    setTimeout(() => {
        if (!pollingPaused) {
            updateSensorReadings();
        }
        loop(); // Call loop again for continuous polling
    }, 30000);
})();

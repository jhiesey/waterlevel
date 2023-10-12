const { Chart, registerables } = require('chart.js')
require('chartjs-adapter-dayjs-4')
const dayjs = require('dayjs')
const utc = require('dayjs/plugin/utc')
const timezone = require('dayjs/plugin/timezone')
dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.setDefault('America/Los_Angeles');

Chart.register(...registerables)

global.renderHistoryChart = function (canvas, data) {
  const historyChart = new Chart(canvas, {
    type: 'line',
    data: {
      datasets: [{
        id: 'orp',
        label: 'Distance from top (cm)',
        data: data
      }]
    },
    options: {
      parsing:false,
      responsive: true,
      maintainAspectRatio: false,
      title: {
        display: true,
        text: 'Readings history'
      },
      scales: {
        x: {
          type: 'time',
          title: {
            display: true,
            text: 'measurement time'
          }
        },
        y: {
          type: 'linear',
          position: 'left',
          reverse: true,
          title: {
            display: true,
            text: 'cm from top'
          }
        }
      },
      plugins: {
        legend: {
          display: false
        }
      }
    }
  })
}
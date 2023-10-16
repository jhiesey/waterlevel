const { Chart, registerables } = require('chart.js')
require('chartjs-adapter-dayjs-4')

Chart.register(...registerables)

const historyChartCanvas = document.getElementById('history-chart')
const historyDurationSelect = document.getElementById('duration-select')

let chart = null
function renderHistoryChart (data) {
  if (chart) {
    chart.data.datasets[0].data = data
    chart.update()
    return
  }

  chart = new Chart(historyChartCanvas, {
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
      animation: false,
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
          },
          time: {
            unit: 'hour',
            displayFormats: {
              hour: 'MMM D h:mm a'
            }
          },
          ticks: {
            minRotation: 90,
            maxRotation: 90
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

let loading = false
async function loadHistory () {
  if (loading) {
    return
  }
  loading = true
  try {
    const duration = historyDurationSelect.value

    const response = await fetch(`/history/${duration}`)
    if (!response.ok) {
      throw new Error(`Request failed; status ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    renderHistoryChart(data)
  } finally {
    loading = false
  }
}

function wrappedLoadHistory () {
  loadHistory().catch(err => {
    console.error('Failed to load:', err)
  })
}

wrappedLoadHistory()
historyDurationSelect.addEventListener('change', wrappedLoadHistory)

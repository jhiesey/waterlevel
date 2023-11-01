const basicAuth = require('basic-auth')
const express = require('express')
const http = require('http')
const pug = require('pug')
const path = require('path')
const fsReverse = require('fs-reverse')
const url = require('url')

const dayjs = require('dayjs')
const utc = require('dayjs/plugin/utc')
const timezone = require('dayjs/plugin/timezone')
const customParseFormat = require('dayjs/plugin/customParseFormat')
const localizedFormat = require('dayjs/plugin/localizedFormat')
dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(customParseFormat)
dayjs.extend(localizedFormat)

const secret = require('../secret')

const DATA_PATH = '../static/data.csv'

function readRecentLevels(historyLenSecs, cb) {
  let latestDate = null
  let latestLevel = null
  const points = []
  const reverseLines = fsReverse(DATA_PATH)
  reverseLines.on('error', (err) => {
    cb(err)
  })

  let done = false
  const onDone = () => {
    if (!done) {
      done = true
      cb(null, latestDate, latestLevel, points)
    }
  }

  reverseLines.on('data', (line) => {
    const parts = line.split(',')
    if (parts.length !== 2) {
      return
    }

    const date = dayjs.tz(parts[0], 'MM/DD/YYYY HH:mm', 'America/Los_Angeles')
    const level = parseFloat(parts[1])

    if (latestDate === null) {
      latestDate = date
      latestLevel = level
    }

    if (latestDate && date.valueOf() < latestDate.valueOf() - historyLenSecs * 1000) {
      reverseLines.destroy()
      onDone()
      return
    }

    points.unshift({
      x: date.valueOf(),
      y: level,
    })
  })
  reverseLines.on('end', onDone)
}

const app = express()
const httpServer = http.createServer(app)

// Templating
app.set('views', path.join(__dirname, 'views'))
app.set('view engine', 'pug')
app.set('x-powered-by', false)

app.use((req, res, next) => {
  function unauthorized() {
    res.set('WWW-Authenticate', 'Basic realm=Authorization Required')
    return res.sendStatus(401)
  }
  const user = basicAuth(req)
  // username is ignored
  if (!user || user.pass !== secret.password) {
    return unauthorized()
  }

  return next()
})

app.use(express.static(path.join(__dirname, '../static')))

app.get('/', (req, res, next) => {
  readRecentLevels(0, (err, latestDate, latestLevel, levels) => {
    if (err) {
      return next(err)
    }

    res.render('index', {
      title: 'Water Level',
      waterlevel: latestLevel,
      meastime: latestDate?.format('L LT') ?? null
    })
  })
})

app.get('/history/:seconds', (req, res, next) => {
  const seconds = Number(req.params.seconds)
  readRecentLevels(seconds, (err, latestDate, latestLevel, levels) => {
    if (err) {
      return next(err)
    }
    res.json(levels)
  })
})

app.get('*', (req, res) => {
  res.status(404).render('error', {
    title: '404 Page Not Found - water.hiesey.com',
    message: '404 Not Found'
  })
})

// error handling middleware
app.use((err, req, res, next) => {
  error(err)
  res.status(500).render('error', {
    title: '500 Server Error - water.hiesey.com',
    message: err.message || err
  })
})

httpServer.listen(9200, '::1')

function error (err) {
  console.error(err.stack || err.message || err)
}

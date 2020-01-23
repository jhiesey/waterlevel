var basicAuth = require('basic-auth')
var compress = require('compression')
var express = require('express')
var fs = require('fs')
var http = require('http')
var jade = require('jade')
var path = require('path')
var split = require('split')
var url = require('url')

var secret = require('../secret')

var DATA_PATH = '../static/data.csv'
var TAIL_LENGTH = 100

function readLevel(cb) {
  fs.stat(DATA_PATH, function (err, stats) {
    if (err) {
      return cb(err)
    }

    var readPos = Math.max(stats.size - TAIL_LENGTH, 0)
    var stream = fs.createReadStream(DATA_PATH, {
      start: readPos
    })

    var res = {
      level: null,
      time: null
    }

    var lines = stream.pipe(split())
    lines.on('data', function (line) {
      var parts = line.split(',')
      if (parts.length !== 2) {
        return
      }

      res.level = parseFloat(parts[1])
      res.time = parts[0]
    })
    lines.on('end', function () {
      cb(null, res)
    })
    lines.on('error', function (err) {
      cb(err)
    })
  })
}

var app = express()
var httpServer = http.createServer(app)

// Templating
app.set('views', path.join(__dirname, 'views'))
app.set('view engine', 'jade')
app.set('x-powered-by', false)
app.engine('jade', jade.renderFile)

app.use(function (req, res, next) {
  function unauthorized() {
    res.set('WWW-Authenticate', 'Basic realm=Authorization Required')
    return res.sendStatus(401)
  }
  var user = basicAuth(req)
  // username is ignored
  if (!user || user.pass !== secret.password) {
    return unauthorized()
  }

  return next()
})

app.use(express.static(path.join(__dirname, '../static')))

app.get('/', function (req, res, next) {
  readLevel(function (err, level) {
    if (err) {
      return next(err)
    }

    res.render('index', {
      title: 'Water Level',
      waterlevel: level.level,
      meastime: level.time
    })
  })
})

app.get('*', function (req, res) {
  res.status(404).render('error', {
    title: '404 Page Not Found - water.hiesey.com',
    message: '404 Not Found'
  })
})

// error handling middleware
app.use(function (err, req, res, next) {
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

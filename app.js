// const http = require('http');
var express = require('express');
var path = require('path');
var bodyParser = require('body-parser');
const expressValidator = require('express-validator');

var createError = require('http-errors');
var indexRouter = require('./routes/index');
var showPersonChoresRouter = require('./routes/showPersonChores');
var getPersonChoresRouter = require('./routes/getPersonChores');
var completeChoreInstanceRouter = require('./routes/completeChoreInstance');
var uncompleteChoreInstanceRouter = require('./routes/uncompleteChoreInstance');
var createChoreRouter = require('./routes/createChore');
var createChoreActionRouter = require('./routes/createChoreAction');
// var similarRouter = require('./routes/similar');

var app = express();

app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'pug');
app.locals.pretty = true;

// const hostname = '127.0.0.1';
// const port = 3000;

/*
const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/html');
  res.end('<html><body><p>Hello World</p></body></html>');
});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
*/

app.use(express.json());
app.use(express.urlencoded({extended: false}));
app.use(bodyParser.urlencoded({extended: true}));
app.use(expressValidator());
app.use(express.static(path.join(__dirname, 'public')));

app.use('/', indexRouter);
// app.use('/api/v1/resources/similar', similarRouter);
app.use('/getPersonChores', getPersonChoresRouter);
app.use('/showPersonChores', showPersonChoresRouter);
app.use('/completeChoreInstance', completeChoreInstanceRouter);
app.use('/uncompleteChoreInstance', uncompleteChoreInstanceRouter);
app.use('/createChore', createChoreRouter);
app.use('/createChoreAction', createChoreActionRouter);


app.listen(3000, function() {
  console.log('Listening on port 3000...');
});

module.exports = app;